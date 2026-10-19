import random
import threading
from tqdm.auto import tqdm
import tkinter as tk
from tkinter import messagebox
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import zipfile
import io
import re
import concurrent.futures
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import glob
import sys

# ==============================================================================
# CONFIGURACIÓN DE CONSOLA Y ENCODING (WINDOWS UTF-8)
# ==============================================================================
if sys.platform.startswith('win'):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ==============================================================================
# 0. RUTAS, DIRECTORIOS Y CONFIGURACIÓN GLOBAL
# ==============================================================================
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(SCRIPT_DIR).lower() == 'scripts':
        PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    else:
        PROJECT_ROOT = SCRIPT_DIR
except NameError:
    PROJECT_ROOT = os.getcwd()
    if os.path.basename(PROJECT_ROOT).lower() == 'scripts':
        PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
INTERMEDIATE_DIR = os.path.join(PROJECT_ROOT, "data", "intermediate")
TEMP_DIR = os.path.join(PROJECT_ROOT, "data", "temp")
TEMP_SALARIOS_DIR = os.path.join(TEMP_DIR, "imss_salarios")
TEMP_PUESTOS_DIR = os.path.join(TEMP_DIR, "imss_puestos")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(INTERMEDIATE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(TEMP_SALARIOS_DIR, exist_ok=True)
os.makedirs(TEMP_PUESTOS_DIR, exist_ok=True)

# Lock global para Selenium: evita que Salarios y Puestos compitan por foco en Windows
SELENIUM_LOCK = threading.Lock()

# ==============================================================================
# GESTIÓN DE TOKENS (VALORES POR DEFECTO + CARGA DINÁMICA .ENV / OS ENV)
# ==============================================================================
TOKENS_INEGI_DEFAULT = [
    "129ac2e3-e8a6-72c7-58c1-acced5a601bd",
    "8ff1ca1f-4ba0-4abc-b98e-c8a5dffc9467",
    "9d9b582f-0cc1-6e57-9d97-2064cebd95d9",
    "8505df05-4276-f1b8-3c6a-437fe9d77c7a",
]
TOKEN_BANXICO_DEFAULT = "3cf05ba180ebc8fa6bac83d6473f5c287fd4a5d28c8d0411ec9c2e896b844b3e"

def cargar_tokens():
    tokens_inegi = list(TOKENS_INEGI_DEFAULT)
    token_banxico = TOKEN_BANXICO_DEFAULT

    if os.getenv("TOKENS_INEGI"):
        tokens_inegi = [t.strip() for t in os.getenv("TOKENS_INEGI").split(",") if t.strip()]
    if os.getenv("TOKEN_BANXICO"):
        token_banxico = os.getenv("TOKEN_BANXICO").strip()

    env_file = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key == "TOKENS_INEGI" and val:
                        tokens_inegi = [t.strip() for t in val.split(",") if t.strip()]
                    elif key == "TOKEN_BANXICO" and val:
                        token_banxico = val
        except Exception:
            pass

    return tokens_inegi, token_banxico

TOKENS_INEGI, TOKEN_BANXICO = cargar_tokens()

def obtener_token_inegi():
    """Selecciona un token aleatorio para balancear la carga sobre la API de INEGI."""
    return random.choice(TOKENS_INEGI)

# ==============================================================================
# GESTOR DE SESIÓN HTTP ROBUSTA (CONNECTION POOLING + AUTO-RETRIES)
# ==============================================================================
def crear_sesion_robusta(retries=3, backoff_factor=0.5, pool_size=32):
    """Crea una sesión requests con pool de conexiones y reintentos automáticos."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=pool_size, pool_maxsize=pool_size)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

SESION_HTTP = crear_sesion_robusta()

# ==============================================================================
# FUNCIONES DE NORMALIZACIÓN Y LIMPIEZA
# ==============================================================================
def homologar_estado(nombre):
    if not isinstance(nombre, str): return nombre
    n = nombre.lower()
    
    if 'ciudad de méxico' in n or 'ciudad de mexico' in n or 'cdmx' in n or 'distrito federal' in n: return 'Ciudad de México'
    if 'baja california sur' in n: return 'Baja California Sur'
    if 'baja california' in n: return 'Baja California'
    if 'estado de méxico' in n or 'estado de mexico' in n or n.strip() == 'méxico' or n.strip() == 'mexico': return 'México'
    
    if 'coahuila' in n: return 'Coahuila'
    if 'michoacán' in n or 'michoacan' in n: return 'Michoacán'
    if 'veracruz' in n: return 'Veracruz'
    if 'nuevo león' in n or 'nuevo leon' in n: return 'Nuevo León'
    if 'querétaro' in n or 'queretaro' in n: return 'Querétaro'
    if 'san luis' in n: return 'San Luis Potosí'
    if 'yucatán' in n or 'yucatan' in n: return 'Yucatán'
    
    estados = ['Aguascalientes', 'Campeche', 'Colima', 'Chiapas', 'Chihuahua', 
               'Durango', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 
               'Morelos', 'Nayarit', 'Oaxaca', 'Puebla', 'Quintana Roo', 
               'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Zacatecas']
    
    for est in estados:
        if est.lower() in n: return est
        
    return nombre

def limpiar_columna_estado(df):
    nombres_validos = ['estado', 'entidad', 'entidad federativa', 'estados', 'entidades']
    for col in df.columns:
        if str(col).lower().strip() in nombres_validos:
            df[col] = df[col].apply(homologar_estado)
    return df

# ==============================================================================
# MÓDULO 1: PIB (INEGI API - Determinista y Ordenado)
# ==============================================================================
def procesar_pib():
    tqdm.write("⏳ [PIB] Iniciando extracción exhaustiva...")
    indicadores = {
        "746097": "Total Nacional",
        "746196": "Actividades Primarias",
        "746229": "Agricultura, cría y explotación de animales, aprovechamiento forestal, pesca y caza",
        "746262": "Agricultura",
        "746295": "Cría y explotación de animales",
        "746328": "Pesca, caza y captura",
        "746361": "Aprovechamiento forestal",
        "746394": "Actividades Secundarias",
        "746427": "Minería",
        "746460": "Minería petrolera",
        "746493": "Minería no petrolera",
        "746526": "Generación, transmisión y distribución de energía eléctrica, agua y gas",
        "746559": "Construcción",
        "746592": "Industrias manufactureras",
        "746625": "Industria alimentaria",
        "746658": "Bebidas y tabaco",
        "746691": "Insumos, acabados y productos textiles",
        "746724": "Prendas de vestir y productos de cuero y piel",
        "746757": "Industria de la madera",
        "746790": "Industria del papel",
        "746823": "Productos derivados del petróleo y carbón, química, plástico y hule",
        "746856": "Productos a base de minerales no metálicos",
        "746889": "Metálicas básicas y productos metálicos",
        "746922": "Maquinaria y equipo, computación, electrónicos y accesorios",
        "746955": "Muebles, colchones y persianas",
        "746988": "Otras industrias manufactureras",
        "747021": "Actividades Terciarias",
        "747054": "Comercio al por mayor",
        "747087": "Comercio al por menor",
        "747120": "Transportes, correos y almacenamiento",
        "747153": "Información en medios masivos",
        "747186": "Servicios financieros y de seguros",
        "747219": "Servicios inmobiliarios y de alquiler de bienes",
        "747252": "Servicios profesionales, científicos y técnicos",
        "747285": "Corporativos",
        "747318": "Servicios de apoyo a los negocios y manejo de residuos",
        "747351": "Servicios educativos",
        "747384": "Servicios de salud y de asistencia social",
        "747417": "Servicios de esparcimiento culturales y deportivos",
        "747450": "Servicios de alojamiento temporal y de preparación de alimentos y bebidas",
        "747483": "Otros servicios excepto actividades gubernamentales",
        "747516": "Actividades legislativas, gubernamentales"
    }
    
    resultados = []
    tareas = [(ind_clave, ind_nombre, f"{i:02d}") for ind_clave, ind_nombre in indicadores.items() for i in range(0, 33)]
    
    def hacer_peticion(tarea):
        ind_clave, ind_nombre, clave_estado = tarea
        token_actual = obtener_token_inegi()
        url = f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{ind_clave}/es/{clave_estado}/false/BIE-BISE/2.0/{token_actual}?type=json"
        
        errores_locales = 0
        for intento in range(3):
            try:
                r = SESION_HTTP.get(url, timeout=12)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        res_locales = []
                        if 'Series' in data and data['Series']:
                            serie = data['Series'][0].get('OBSERVATIONS', [])
                            serie_sorted = sorted(serie, key=lambda x: x.get('TIME_PERIOD', ''))
                            for obs in serie_sorted:
                                raw_val = obs.get('OBS_VALUE')
                                val_limpio = 0.0
                                
                                if raw_val is not None and str(raw_val).strip():
                                    try:
                                        val_limpio = float(str(raw_val).strip())
                                    except ValueError:
                                        val_limpio = 0.0
                                        
                                raw_periodo = obs.get('TIME_PERIOD', '0')
                                try:
                                    periodo_limpio = int(raw_periodo)
                                except ValueError:
                                    periodo_limpio = raw_periodo

                                res_locales.append({
                                    'Indicador': ind_nombre, 
                                    'Clave_Indicador': ind_clave,
                                    'Estado_ID': obs.get('COBER_GEO', clave_estado),
                                    'Periodo': periodo_limpio, 
                                    'Valor': val_limpio
                                })
                        return res_locales, errores_locales, "EXITO"
                    except Exception:
                        return [], errores_locales, "NO_DATA"
                elif r.status_code == 429 or r.status_code >= 500:
                    errores_locales += 1
                    time.sleep(1 + random.uniform(0.1, 1.2))
                else:
                    return [], errores_locales, "NO_DATA"
            except requests.exceptions.RequestException:
                errores_locales += 1
                time.sleep(1 + random.uniform(0.1, 1.2))
        return [], errores_locales, "RETRY"

    errores_totales = 0
    tareas_pendientes = tareas.copy()
    max_hilos = max(4, min(16, len(TOKENS_INEGI) * 3))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_hilos) as executor:
        barra_progreso = tqdm(
            total=len(tareas_pendientes), 
            desc="📊 PIB        ", 
            unit="req",
            leave=True
        )
        
        while tareas_pendientes:
            futuros = {executor.submit(hacer_peticion, t): t for t in tareas_pendientes}
            tareas_pendientes = []
            
            for futuro in concurrent.futures.as_completed(futuros):
                t = futuros[futuro]
                res, errs, estado = futuro.result()
                
                if res: resultados.extend(res)
                errores_totales += errs
                
                if estado == "RETRY":
                    tareas_pendientes.append(t)
                else:
                    barra_progreso.update(1)
                    
                if errores_totales > 0:
                    barra_progreso.set_postfix({"Errores de Red": errores_totales})
                    
        barra_progreso.close()

    if resultados:
        df = pd.DataFrame(resultados)
        # Ordenamiento determinista para evitar reordenamientos artificiales en Git
        df = df.sort_values(by=['Clave_Indicador', 'Estado_ID', 'Periodo']).reset_index(drop=True)
        df.to_csv(os.path.join(INTERMEDIATE_DIR, "pib_entidad.csv"), index=False)
        return f"✅ [PIB] Completado ({len(df)} registros)."
    return "⚠️ [PIB] No se obtuvieron datos."

# ==============================================================================
# MÓDULO 2: EXPORTACIONES (INEGI API - Determinista y Ordenado)
# ==============================================================================
def procesar_exportaciones():
    tqdm.write("⏳ [Exportaciones] Iniciando extracción detallada...")
    indicadores = {
        "629659": "Total",
        "696790": "Agricultura",
        "696791": "Cría y explotación de animales",
        "697788": "Pesca, caza y captura",
        "629660": "Extracción de petróleo y gas",
        "629661": "Minería de minerales metálicos y no metálicos",
        "629662": "Industria alimentaria",
        "629663": "Industria de las bebidas y del tabaco",
        "629664": "Fabricación de insumos textiles y acabado de textiles",
        "629665": "Fabricación de productos textiles, excepto prendas de vestir",
        "629666": "Fabricación de prendas de vestir",
        "629667": "Curtido y acabado de cuero y piel, y fabricación de productos de cuero",
        "629668": "Industria de la madera",
        "629669": "Industria del papel",
        "629670": "Impresión e industrias conexas",
        "629671": "Fabricación de productos derivados del petróleo y del carbón",
        "629672": "Industria química",
        "629673": "Industria del plástico y del hule",
        "629674": "Fabricación de productos a base de minerales no metálicos",
        "629675": "Industrias metálicas básicas",
        "629676": "Fabricación de productos metálicos",
        "629677": "Fabricación de maquinaria y equipo",
        "629678": "Fabricación de equipo de computación, comunicación, medición y otros equipos, componentes y accesorios electrónicos",
        "629679": "Fabricación de accesorios, aparatos eléctricos y equipo de generación de energía eléctrica",
        "629680": "Fabricación de equipo de transporte",
        "629681": "Fabricación de muebles, colchones y persianas",
        "629682": "Otras industrias manufactureras",
        "629683": "No especificado"
    }
    
    resultados = []
    tareas = [(ind_clave, ind_nombre, f"{i:02d}") for ind_clave, ind_nombre in indicadores.items() for i in range(1, 33)]

    def hacer_peticion_export(tarea):
        ind_clave, ind_nombre, clave_estado = tarea
        token_actual = obtener_token_inegi()
        url = f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{ind_clave}/es/{clave_estado}/false/BIE-BISE/2.0/{token_actual}?type=json"
        
        errores_locales = 0
        for intento in range(3):
            try:
                r = SESION_HTTP.get(url, timeout=12)
                
                if r.status_code == 200:
                    try:
                        data = r.json()
                        res_locales = []
                        if 'Series' in data and data['Series']:
                            serie = data['Series'][0].get('OBSERVATIONS', [])
                            serie_sorted = sorted(serie, key=lambda x: x.get('TIME_PERIOD', ''))
                            for obs in serie_sorted:
                                raw_val = obs.get('OBS_VALUE')
                                val_limpio = 0.0
                                
                                if raw_val is not None and str(raw_val).strip():
                                    try:
                                        val_limpio = float(str(raw_val).strip())
                                    except ValueError:
                                        val_limpio = 0.0

                                res_locales.append({
                                    'Sector': ind_nombre, 
                                    'Clave_Indicador': ind_clave,
                                    'Estado_ID': clave_estado, 
                                    'Periodo': obs.get('TIME_PERIOD'),
                                    'Valor': val_limpio
                                })
                        return res_locales, errores_locales, "EXITO"
                    except Exception:
                        return [], errores_locales, "NO_DATA"

                elif r.status_code == 429 or r.status_code >= 500:
                    errores_locales += 1
                    time.sleep(1 + random.uniform(0.1, 1.2))
                else:
                    return [], errores_locales, "NO_DATA"
                    
            except requests.exceptions.RequestException: 
                errores_locales += 1
                time.sleep(1 + random.uniform(0.1, 1.2))
                
        return [], errores_locales, "RETRY"

    errores_totales = 0
    tareas_pendientes = tareas.copy()
    max_hilos = max(4, min(16, len(TOKENS_INEGI) * 3))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_hilos) as executor:
        barra_progreso = tqdm(
            total=len(tareas_pendientes), 
            desc="📦 Exportaciones", 
            unit="req",
            leave=True
        )
        
        while tareas_pendientes:
            futuros = {executor.submit(hacer_peticion_export, t): t for t in tareas_pendientes}
            tareas_pendientes = []
            
            for futuro in concurrent.futures.as_completed(futuros):
                t = futuros[futuro]
                res, errs, estado = futuro.result()
                
                if res: resultados.extend(res)
                errores_totales += errs
                
                if estado == "RETRY":
                    tareas_pendientes.append(t)
                else:
                    barra_progreso.update(1)
                    
                if errores_totales > 0:
                    barra_progreso.set_postfix({"Errores de Red": errores_totales})
                    
        barra_progreso.close()

    if resultados:
        df = pd.DataFrame(resultados)
        # Ordenamiento determinista para evitar reordenamientos artificiales en Git
        df = df.sort_values(by=['Clave_Indicador', 'Estado_ID', 'Periodo']).reset_index(drop=True)
        df.to_csv(os.path.join(INTERMEDIATE_DIR, "exportaciones_entidad.csv"), index=False)
        return f"✅ [Exportaciones] Completado ({len(df)} registros)."
    return "⚠️ [Exportaciones] No se obtuvieron datos."

# ==============================================================================
# MÓDULO 3: POBLACIÓN (INEGI API - Determinista y Ordenado)
# ==============================================================================
def procesar_poblacion_api():
    tqdm.write("⏳ [Población] Iniciando extracción de pirámide completa...")
    indicadores = {
        # Hombres
        "1002000059": "0 a 4 años (Hombres)",
        "1002000089": "5 a 9 años (Hombres)",
        "1002000062": "10 a 14 años (Hombres)",
        "1002000068": "15 a 19 años (Hombres)",
        "1002000071": "20 a 24 años (Hombres)",
        "1002000074": "25 a 29 años (Hombres)",
        "1002000077": "30 a 34 años (Hombres)",
        "1002000080": "35 a 39 años (Hombres)",
        "1002000083": "40 a 44 años (Hombres)",
        "1002000086": "45 a 49 años (Hombres)",
        "1002000092": "50 a 54 años (Hombres)",
        "1002000095": "55 a 59 años (Hombres)",
        "1002000098": "60 a 64 años (Hombres)",
        "1002000101": "65 a 69 años (Hombres)",
        "1002000104": "70 a 74 años (Hombres)",
        "1002000107": "75 a 79 años (Hombres)",
        "1002000110": "80 a 84 años (Hombres)",
        "1002000113": "85 a 89 años (Hombres)",
        "1002000116": "90 a 94 años (Hombres)",
        "1002000119": "95 a 99 años (Hombres)",
        "1002000065": "100 años y más (Hombres)",

        # Mujeres
        "1002000060": "0 a 4 años (Mujeres)",
        "1002000090": "5 a 9 años (Mujeres)",
        "1002000063": "10 a 14 años (Mujeres)",
        "1002000069": "15 a 19 años (Mujeres)",
        "1002000072": "20 a 24 años (Mujeres)",
        "1002000075": "25 a 29 años (Mujeres)",
        "1002000078": "30 a 34 años (Mujeres)",
        "1002000081": "35 a 39 años (Mujeres)",
        "1002000084": "40 a 44 años (Mujeres)",
        "1002000087": "45 a 49 años (Mujeres)",
        "1002000093": "50 a 54 años (Mujeres)",
        "1002000096": "55 a 59 años (Mujeres)",
        "1002000099": "60 a 64 años (Mujeres)",
        "1002000102": "65 a 69 años (Mujeres)",
        "1002000105": "70 a 74 años (Mujeres)",
        "1002000108": "75 a 79 años (Mujeres)",
        "1002000111": "80 a 84 años (Mujeres)",
        "1002000114": "85 a 89 años (Mujeres)",
        "1002000117": "90 a 94 años (Mujeres)",
        "1002000120": "95 a 99 años (Mujeres)",
        "1002000066": "100 años y más (Mujeres)"
    }
    
    resultados = []
    tareas = [(ind_clave, desc, f"{i:02d}") for ind_clave, desc in indicadores.items() for i in range(0, 33)]

    def hacer_peticion_pob(tarea):
        ind_clave, desc, clave_estado = tarea
        token_actual = obtener_token_inegi()
        url = f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{ind_clave}/es/{clave_estado}/true/BISE/2.0/{token_actual}?type=json"
        
        errores_locales = 0
        for intento in range(3):
            try:
                r = SESION_HTTP.get(url, timeout=12)
                if r.status_code == 200:
                    data = r.json()
                    if 'Series' in data and data['Series']:
                        obs = data['Series'][0]['OBSERVATIONS'][0]
                        
                        raw_val = obs.get('OBS_VALUE')
                        val_limpio = 0.0
                        
                        if raw_val is not None and str(raw_val).strip():
                            try:
                                val_limpio = float(str(raw_val).strip())
                            except ValueError:
                                val_limpio = 0.0

                        return [{
                            'Indicador': desc, 
                            'Clave_Indicador': ind_clave, 
                            'Estado_ID': clave_estado, 
                            'Periodo': obs.get('TIME_PERIOD'),
                            'Valor': val_limpio
                        }], errores_locales
                    return [], errores_locales
                else: 
                    errores_locales += 1
                    time.sleep(1 + random.uniform(0.1, 1.2))
            except Exception: 
                errores_locales += 1
                time.sleep(1 + random.uniform(0.1, 1.2))
        return [], errores_locales

    errores_totales = 0
    max_hilos = max(4, min(16, len(TOKENS_INEGI) * 3))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_hilos) as executor:
        futuros = {executor.submit(hacer_peticion_pob, t): t for t in tareas}
        
        barra_progreso = tqdm(
            concurrent.futures.as_completed(futuros), 
            total=len(tareas), 
            desc="👥 Población  ", 
            unit="req",
            leave=True
        )
        
        for futuro in barra_progreso:
            res, errs = futuro.result()
            if res: resultados.extend(res)
            
            errores_totales += errs
            if errores_totales > 0:
                barra_progreso.set_postfix({"Errores de Red": errores_totales})

    if resultados:
        df = pd.DataFrame(resultados)
        # Ordenamiento determinista para evitar reordenamientos artificiales en Git
        df = df.sort_values(by=['Clave_Indicador', 'Estado_ID']).reset_index(drop=True)
        df.to_csv(os.path.join(INTERMEDIATE_DIR, "poblacion_edad.csv"), index=False)
        return f"✅ [Población] Completado ({len(df)} registros)."
    return "⚠️ [Población] No se obtuvieron datos."

# ==============================================================================
# MÓDULO 4: ENOE (Detección Robusta de Archivo ZIP de INEGI)
# ==============================================================================
def procesar_enoe_auto():
    tqdm.write("⏳ [ENOE] Iniciando descarga y procesamiento...")
    
    base_url = "https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/tabulados/"
    anio_actual = datetime.now().year
    url_final, anio_found, trim_found = None, None, None
    
    for a in [anio_actual, anio_actual - 1]:
        if url_final: break
        for t in ["trim4", "trim3", "trim2", "trim1"]:
            test_url = f"{base_url}enoe_indicadores_estrategicos_{a}_{t}_xls.zip"
            try:
                # Usar GET stream=True para inspeccionar encabezados reales (evita que Akamai devuelva text/html con HEAD)
                r = SESION_HTTP.get(test_url, stream=True, timeout=8)
                content_type = r.headers.get('Content-Type', '').lower()
                content_length = int(r.headers.get('Content-Length', 0))
                if r.status_code == 200 and ('zip' in content_type or 'octet-stream' in content_type or content_length > 50000):
                    url_final = test_url
                    anio_found = a
                    trim_found = t
                    break
            except requests.exceptions.RequestException:
                pass
            
    if not url_final:
        return "❌ [ENOE] No se encontró ningún archivo ZIP de ENOE disponible en el servidor de INEGI."

    try:
        tqdm.write(f"   📥 [ENOE] Descargando ({anio_found}-{trim_found}): {url_final}")
        r = SESION_HTTP.get(url_final, timeout=60)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        
        archivos = [f for f in z.namelist() if ("Entidades/" in f or "Nacional/" in f) and (f.endswith('.xlsx') or f.endswith('.xls'))]
        if not archivos:
            return f"⚠️ [ENOE] El archivo ZIP descargado no contiene archivos de entidades esperados."
            
        datos = []
        
        config_enoe = {
            "Poblacion Total": ["", "Población total"],
            "PEA": ["", "Población económicamente activa (PEA)"],
            "Desocupada": ["Población económicamente activa", "Desocupada"],
            "Edad Promedio PEA": ["Edad de la población económicamente activa", "Promedio"],
            "Sector Primario": ["3.2 Sector de actividad", "Primario"],
            "Sector Secundario": ["3.2 Sector de actividad", "Secundario"],
            "Sector Terciario": ["3.2 Sector de actividad", "Terciario"],
            "No especificado": ["3.2 Sector de actividad", "No especificado"],
            "Educacion Sup": ["Nivel de instrucción", "Medio superior y superior"],
            "Informalidad TIL1": ["", "Tasa de informalidad laboral 1 (TIL1)"]
        }

        for arch in archivos:
            if "Nacional" in arch:
                estado = "Nacional"
            else:
                estado = arch.split("Entidad_")[-1].replace(".xlsx", "").replace(".xls", "").replace("_", " ").title()
                
            with z.open(arch) as f:
                df = pd.read_excel(f, header=None)
            
            registro = {'Estado': estado, 'Anio': anio_found, 'Trimestre': trim_found}
            
            col_val = 4 
            for idx, row in df.iterrows():
                txt = " ".join([str(x).lower() for x in row[:5]])
                if "población total" in txt:
                    for c in range(4, min(15, len(row))):
                        try:
                            if float(str(row[c]).replace(",","").replace(" ", "")) > 1000: 
                                col_val = c
                                break
                        except (ValueError, TypeError):
                            continue
                    break
            
            context = {i: "" for i in range(5)}
            sticky = {1: ""}
            
            for idx, row in df.iterrows():
                cols = [str(row[i]).strip() if i < len(row) and pd.notna(row[i]) else "" for i in range(5)]
                indent = -1
                txt_row = ""
                
                for i, txt in enumerate(cols):
                    if txt:
                        indent = i
                        txt_row = txt
                        context[i] = txt
                        for j in range(i+1, 5): 
                            context[j] = ""
                            if j in sticky: sticky[j] = ""
                        break
                
                if not txt_row: continue
                
                if indent == 1 and re.match(r'^(\d+\.?\d*)\s', txt_row):
                    sticky[1] = txt_row
                
                path = [context[0]]
                if indent == 1 and not re.match(r'^(\d+\.?\d*)\s', txt_row) and sticky[1]:
                    path.append(sticky[1])
                    path.append(txt_row)
                else:
                    path.append(context[1])
                path += [context[k] for k in range(2, 5)]
                
                path_str = " | ".join([p.lower() for p in path if p])
                
                for kpi, (padre, target) in config_enoe.items():
                    if target.lower() in txt_row.lower() and padre.lower() in path_str:
                        try: 
                            val_str = str(row[col_val]).replace(",", "").replace(" ", "")
                            registro[kpi] = float(val_str)
                        except (ValueError, TypeError):
                            pass
            
            datos.append(registro)

        df_out = pd.DataFrame(datos)
        df_out = limpiar_columna_estado(df_out)
        outfile = os.path.join(INTERMEDIATE_DIR, "enoe_indicadores.csv")
        df_out.to_csv(outfile, index=False)
        return f"✅ [ENOE] Completado ({anio_found}-{trim_found})."
        
    except Exception as e:
        return f"❌ [ENOE] Error: {e}"

# ==============================================================================
# MÓDULO 5: EDUCACIÓN (Local)
# ==============================================================================
def procesar_educacion():
    tqdm.write("⏳ [Educación] Procesando anuario (Generando Totales y Top 3)...")
    
    archivos = [
        f for f in os.listdir(RAW_DIR) 
        if f.startswith("base_anuario_") and f.endswith(".xlsx") and not f.startswith("~$")
    ]
    if not archivos:
        return "⚠️ [Educación] Falta archivo base_anuario_####-####.xlsx en data/raw"
    
    archivos.sort(reverse=True)
    archivo_anuario = archivos[0]
    fpath = os.path.join(RAW_DIR, archivo_anuario)
    tqdm.write(f"   📂 [Educación] Usando anuario: {archivo_anuario}")
    
    match = re.search(r'base_anuario_(\d{4}-\d{4})\.xlsx', archivo_anuario)
    ciclo_val = match.group(1) if match else "¿?"
    
    try:
        df = pd.read_excel(fpath, sheet_name="Base de datos")
        
        cols_num = ['Matrícula Total', 'Egresados Total']
        for c in cols_num: 
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        
        mapa_niveles = {
            'TÉCNICO SUPERIOR': 'Técnico Superior', 'LICENCIATURA EN EDUCACIÓN NORMAL': 'Licenciatura',
            'LICENCIATURA UNIVERSITARIA Y TECNOLÓGICA': 'Licenciatura', 'ESPECIALIDAD': 'Licenciatura',
            'MAESTRÍA': 'Maestría', 'DOCTORADO': 'Doctorado'
        }
        df['Nivel_Agrupado'] = df['NIVEL'].str.upper().str.strip().map(mapa_niveles)
        df = limpiar_columna_estado(df)
        
        # 1. TOTALES
        df_totales = df.groupby(['ENTIDAD', 'Nivel_Agrupado'])[cols_num].sum().reset_index()
        df_totales['Ciclo'] = ciclo_val
        df_totales.to_csv(os.path.join(INTERMEDIATE_DIR, "educacion_totales.csv"), index=False)
        
        df_campos = df.groupby(['ENTIDAD', 'Nivel_Agrupado', 'CAMPO AMPLIO'])[cols_num].sum().reset_index()
        
        df_nivels = df_campos.groupby(['ENTIDAD', 'Nivel_Agrupado'])[cols_num].sum().reset_index().rename(columns={
            'Matrícula Total': 'Total_Mat', 
            'Egresados Total': 'Total_Egr'
        })
        df_campos = df_campos.merge(df_nivels, on=['ENTIDAD', 'Nivel_Agrupado'])
        
        df_campos['Participacion_Matricula'] = df_campos.apply(lambda x: (x['Matrícula Total']/x['Total_Mat']*100) if x['Total_Mat']>0 else 0, axis=1)
        df_campos['Participacion_Egresados'] = df_campos.apply(lambda x: (x['Egresados Total']/x['Total_Egr']*100) if x['Total_Egr']>0 else 0, axis=1)
        
        top_mat = df_campos.sort_values(['ENTIDAD', 'Nivel_Agrupado', 'Matrícula Total'], ascending=[True, True, False])
        top_mat = top_mat.groupby(['ENTIDAD', 'Nivel_Agrupado']).head(3).copy()
        top_mat['Ciclo'] = ciclo_val
        
        cols_mat = ['ENTIDAD', 'Nivel_Agrupado', 'CAMPO AMPLIO', 'Matrícula Total', 'Participacion_Matricula', 'Ciclo']
        top_mat[cols_mat].to_csv(os.path.join(INTERMEDIATE_DIR, "educacion_top3_matricula.csv"), index=False)
        
        top_egr = df_campos.sort_values(['ENTIDAD', 'Nivel_Agrupado', 'Egresados Total'], ascending=[True, True, False])
        top_egr = top_egr.groupby(['ENTIDAD', 'Nivel_Agrupado']).head(3).copy()
        top_egr['Ciclo'] = ciclo_val
        
        cols_egr = ['ENTIDAD', 'Nivel_Agrupado', 'CAMPO AMPLIO', 'Egresados Total', 'Participacion_Egresados', 'Ciclo']
        top_egr[cols_egr].to_csv(os.path.join(INTERMEDIATE_DIR, "educacion_top3_egresados.csv"), index=False)
        
        return f"✅ [Educación] Completado (Totales + 2 Archivos Top3 - Ciclo {ciclo_val})."
        
    except Exception as e:
        return f"❌ [Educación] Error: {e}"

# ==============================================================================
# MÓDULO 6: IED (Local)
# ==============================================================================
def buscar_archivo_ied():
    candidatos = [
        f for f in os.listdir(RAW_DIR) 
        if "flujos_ef_or" in f.lower() and f.endswith((".xlsx", ".xls")) and not f.startswith("~$")
    ]
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: os.path.getmtime(os.path.join(RAW_DIR, x)), reverse=True)
    return os.path.join(RAW_DIR, candidatos[0])

def procesar_ied():
    tqdm.write("⏳ [IED] Procesando datos complejos (Totales 3 Dígitos y Detalle)...")
    fpath = buscar_archivo_ied()
    
    if not fpath or not os.path.exists(fpath): 
        return "⚠️ [IED] Falta archivo de flujos (*Flujos_EF_OR*.xlsx) en data/raw"
    
    tqdm.write(f"   📂 [IED] Usando archivo: {os.path.basename(fpath)}")
    
    try:
        df_head = pd.read_excel(fpath, sheet_name='EF por Actividad Económica', header=None, nrows=15)
        
        header_idx = None
        for idx, row in df_head.iterrows():
            if str(row[0]).strip().startswith("Entidad Federativa"):
                header_idx = idx
                break
        
        if header_idx is None: 
            return "❌ [IED] Sin encabezados reconocibles en la hoja 'EF por Actividad Económica'."
        
        years_row = df_head.iloc[header_idx].tolist()
        quarters_row = df_head.iloc[header_idx + 1].tolist()
        
        col_map = {}
        current_year = None
        for i in range(1, len(years_row)):
            val_y = str(years_row[i]).strip()
            if val_y and val_y.lower() != 'nan':
                match_y = re.search(r'(20\d{2})', val_y)
                if match_y:
                    current_year = int(match_y.group(1))
                    
            val_q = str(quarters_row[i]).strip()
            if current_year and val_q and val_q.lower() != 'nan':
                match_q = re.search(r'([1-4])', val_q)
                if match_q:
                    q = int(match_q.group(1))
                    col_map[i] = (current_year, q)
        
        if not col_map: 
            return "❌ [IED] Error al mapear columnas de año/trimestre en IED."
        
        last_period = max(col_map.values())
        prev_period = (last_period[0]-1, last_period[1])
        
        idx_act = [k for k, v in col_map.items() if v == last_period][0]
        idx_prev = [k for k, v in col_map.items() if v == prev_period]
        idx_prev = idx_prev[0] if idx_prev else None
        
        df_data = pd.read_excel(fpath, sheet_name='EF por Actividad Económica', header=header_idx+1)
        
        def clean(x):
            if pd.isna(x): return 0.0
            s = str(x).strip().replace(',', '')
            try: return float(s)
            except (ValueError, TypeError): return 0.0
            
        def clasificar(cod):
            if cod.startswith('1'): return 'Primaria'
            if cod.startswith(('2', '3')): return 'Secundaria'
            return 'Terciaria'
            
        filas = []
        estado_act = None
        
        for i, row in df_data.iterrows():
            c = str(row.iloc[0]).strip()
            if not c or c == 'nan': continue
            
            match = re.match(r'^(\d{2,6}|31-33)\s+(.*)', c)
            if match:
                cod, desc = match.groups()
                if len(cod) == 3 and cod != '31-33':
                    val_act = clean(row.iloc[idx_act])
                    val_prev = clean(row.iloc[idx_prev]) if idx_prev else 0.0
                    
                    filas.append({
                        'Estado': estado_act,
                        'Codigo': cod,
                        'Actividad': desc,
                        'Sector': clasificar(cod), 
                        'Inversion': val_act, 
                        'Inversion_Anterior': val_prev
                    })
            elif not c[0].isdigit() and "total" not in c.lower() and "nota" not in c.lower():
                estado_act = c
                val_act = clean(row.iloc[idx_act])
                val_prev = clean(row.iloc[idx_prev]) if idx_prev else 0.0
                
                filas.append({
                    'Estado': estado_act,
                    'Codigo': 'Total',
                    'Actividad': 'Total',
                    'Sector': 'Total', 
                    'Inversion': val_act, 
                    'Inversion_Anterior': val_prev
                })
        
        df_clean = pd.DataFrame(filas)
        if not df_clean.empty:
            df_clean = limpiar_columna_estado(df_clean)

        if not df_clean.empty:
            df_totales = df_clean.groupby(['Estado', 'Sector'])[['Inversion', 'Inversion_Anterior']].sum().reset_index()
            
            df_totales['Anio'] = last_period[0]
            df_totales['Trimestre'] = last_period[1]
            
            df_totales.to_csv(os.path.join(INTERMEDIATE_DIR, "ied_totales.csv"), index=False)
            
            tops = []
            for est in df_clean['Estado'].unique():
                d_est = df_clean[df_clean['Estado'] == est]
                for sec in ['Primaria', 'Secundaria', 'Terciaria']:
                    d_sec = d_est[d_est['Sector'] == sec]
                    
                    d_inv = d_sec[d_sec['Inversion'] > 0]
                    top3_inv = d_inv.sort_values('Inversion', ascending=False).head(3).copy()
                    if not top3_inv.empty:
                        top3_inv['Clasificacion_Flujo'] = 'Inversión Positiva'
                        tops.append(top3_inv)
                        
                    d_des = d_sec[d_sec['Inversion'] < 0]
                    top3_des = d_des.sort_values('Inversion', ascending=True).head(3).copy()
                    if not top3_des.empty:
                        top3_des['Clasificacion_Flujo'] = 'Desinversión'
                        tops.append(top3_des)
            
            if tops:
                df_tops = pd.concat(tops)
                df_tops['Anio'] = last_period[0]
                df_tops['Trimestre'] = last_period[1]
                
                cols = df_tops.columns.tolist()
                if 'Clasificacion_Flujo' in cols:
                    cols.insert(4, cols.pop(cols.index('Clasificacion_Flujo')))
                    df_tops = df_tops[cols]
                
                df_tops.to_csv(os.path.join(INTERMEDIATE_DIR, "ied_top3_sectores.csv"), index=False)
                return f"✅ [IED] Completado (Periodo {last_period})."
        
        return "⚠️ [IED] Sin datos extraídos."
        
    except Exception as e:
        return f"❌ [IED] Error: {e}"

# ==============================================================================
# MÓDULO 7: SAIC (Local)
# ==============================================================================
def procesar_saic():
    tqdm.write("⏳ [SAIC] Procesando censo...")
    fpath = os.path.join(RAW_DIR, "SAIC.xlsx")
    if not os.path.exists(fpath): return f"⚠️ [SAIC] Falta {fpath}"
    
    try:
        df = pd.read_excel(fpath, header=4)
        df = df.iloc[:, [0, 1, 3, 4]]
        df.columns = ['Anio_Censal', 'Entidad', 'Personal_Ocupado', 'Produccion_Bruta']
        
        df = df.dropna(how='all')
        df = df[~df['Anio_Censal'].astype(str).str.lower().str.startswith('nota')]
        df = df.dropna(subset=['Entidad'])
        
        def clean_entidad(val):
            return re.sub(r'^\d+\s+', '', str(val).strip())

        def clean_numeric(val):
            if pd.isna(val): return 0.0
            if isinstance(val, str):
                val = val.replace(',', '').strip()
                if val == '' or val == '-': return 0.0
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0

        df['Entidad'] = df['Entidad'].apply(clean_entidad)
        df = limpiar_columna_estado(df)
        df['Personal_Ocupado'] = df['Personal_Ocupado'].apply(clean_numeric)
        df['Produccion_Bruta'] = df['Produccion_Bruta'].apply(clean_numeric)

        df['Indicador_Productividad'] = df.apply(
            lambda row: (row['Produccion_Bruta'] / row['Personal_Ocupado']) * 1000
            if row['Personal_Ocupado'] != 0 else 0.0, 
            axis=1
        )
        
        cols_finales = ['Anio_Censal', 'Entidad', 'Personal_Ocupado', 'Produccion_Bruta', 'Indicador_Productividad']
        df = df[cols_finales]
        
        df.to_csv(os.path.join(INTERMEDIATE_DIR, "saic_productividad.csv"), index=False)
        return "✅ [SAIC] Completado."
        
    except Exception as e:
        return f"❌ [SAIC] Error: {e}"

# ==============================================================================
# MÓDULO 8: IMCO (Local)
# ==============================================================================
def procesar_imco():
    tqdm.write("⏳ [IMCO] Procesando competitividad...")
    f_gen = os.path.join(RAW_DIR, "imco_general.csv")
    f_des = os.path.join(RAW_DIR, "imco_desagregado.csv")
    if not os.path.exists(f_gen) or not os.path.exists(f_des): 
        return "⚠️ [IMCO] Faltan archivos (imco_general.csv o imco_desagregado.csv) en data/raw"
    
    try:
        try: 
            df_g = pd.read_csv(f_gen, encoding='utf-8')
        except UnicodeDecodeError: 
            df_g = pd.read_csv(f_gen, encoding='latin-1')

        cols_map = {c: 'Año' if 'AÃ±o' in c else 'Cambio' if 'posiciÃ³n' in c else c for c in df_g.columns}
        df_g.rename(columns=cols_map, inplace=True)
        df_g = df_g[df_g['Año'] == df_g['Año'].max()]
        df_g = limpiar_columna_estado(df_g)
        df_g.to_csv(os.path.join(INTERMEDIATE_DIR, "imco_general_final.csv"), index=False)
        
        try: 
            df_d = pd.read_csv(f_des, encoding='utf-8')
        except UnicodeDecodeError: 
            df_d = pd.read_csv(f_des, encoding='latin-1')

        cols_map_d = {c: 'Subíndice' if 'SubÃ­ndice' in c else c for c in df_d.columns}
        df_d.rename(columns=cols_map_d, inplace=True)
        df_d = limpiar_columna_estado(df_d)
        
        fechas = sorted(df_d['Date'].unique(), reverse=True)[:2]
        df_d = df_d[df_d['Date'].isin(fechas)].copy()
        df_d['Rank'] = df_d.groupby(['Date', 'Indicador'])['Value'].rank(ascending=False, method='min')
        
        if len(fechas) >= 2:
            df_curr = df_d[df_d['Date'] == fechas[0]].copy()
            df_prev = df_d[df_d['Date'] == fechas[1]][['Entidad', 'Indicador', 'Rank']].rename(columns={'Rank': 'Rank_Prev'})
            df_fin = df_curr.merge(df_prev, on=['Entidad', 'Indicador'], how='left')
            df_fin['Cambio_Posicion'] = df_fin['Rank_Prev'] - df_fin['Rank']
            df_fin['Cambio_Posicion'] = df_fin['Cambio_Posicion'].fillna(0)
        else:
            df_fin = df_d
            df_fin['Cambio_Posicion'] = 0
            
        df_fin.to_csv(os.path.join(INTERMEDIATE_DIR, "imco_desagregado_final.csv"), index=False)
        return "✅ [IMCO] Completado."
    except Exception as e:
        return f"❌ [IMCO] Error: {e}"

# ==============================================================================
# MÓDULO 9: SALARIOS IMSS (Selenium Visible - Descarga Atómica por Estado + Consolidación Batch)
# ==============================================================================
def esperar_tableau_listo(driver, timeout=8):
    """Espera a que el telón de carga translúcido de Tableau (loadingGlassPane) desaparezca."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.ID, "loadingGlassPane"))
        )
    except Exception:
        pass
    time.sleep(0.5)

def procesar_salarios_imss():
    tqdm.write("⏳ [Salarios IMSS] Iniciando extracción de 32 estados con Selenium...")
    
    with SELENIUM_LOCK:
        driver = None 
        try:
            # 1. Limpieza inicial de la carpeta temporal exclusiva
            for f in glob.glob(os.path.join(TEMP_SALARIOS_DIR, "*")):
                try: os.remove(f)
                except Exception: pass
                
            opciones = webdriver.ChromeOptions()
            prefs = {"download.default_directory" : TEMP_SALARIOS_DIR}
            opciones.add_experimental_option("prefs", prefs)
            opciones.add_argument("--lang=es-MX") 
            
            xpath_pestana = "//div[contains(@class, 'tabStoryPointContent') and contains(normalize-space(), 'Cifras de salario')]"
            xpath_filtro_entidad = "(//span[@aria-haspopup='listbox' and contains(concat(' ', normalize-space(@class), ' '), ' tabComboBox ')])[1]"
            xpath_todo_box = "//div[@role='checkbox' and .//a[@title='(Todo)' or @title='(All)']]//div[@class='fakeCheckBox']"
            xpath_search = "//textarea[contains(@class, 'QueryBox')]"

            def iniciar_navegador():
                d = webdriver.Chrome(options=opciones)
                d.get("https://public.tableau.com/app/profile/imss.cpe/viz/Histrico_4/Empleo_h?publish=yes")
                w = WebDriverWait(d, 20)

                # Cookies (espera corta protegida)
                try:
                    btn_cookies = WebDriverWait(d, 6).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
                    btn_cookies.click()
                    time.sleep(1) 
                except Exception:
                    pass

                # Entrar al iFrame y Pestaña
                iframe = w.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                d.switch_to.frame(iframe)
                esperar_tableau_listo(d, 6)
                
                tab_salario = w.until(EC.element_to_be_clickable((By.XPATH, xpath_pestana)))
                tab_salario.click()
                esperar_tableau_listo(d, 6)
                time.sleep(2)

                # Filtro Entidad y deseleccionar (Todo)
                filtro_entidad = w.until(EC.element_to_be_clickable((By.XPATH, xpath_filtro_entidad)))
                filtro_entidad.click()
                esperar_tableau_listo(d, 4)
                time.sleep(2)
                
                try:
                    box_todo = w.until(EC.presence_of_element_located((By.XPATH, xpath_todo_box)))
                    ActionChains(d).move_to_element(box_todo).click().perform()
                except Exception:
                    pass
                esperar_tableau_listo(d, 4)
                time.sleep(2)

                return d, w

            estados_totales = [
                "Aguascalientes", "Baja California", "Baja California Sur", "Campeche", "Chiapas", 
                "Chihuahua", "Ciudad de México", "Coahuila de Zaragoza", "Colima", "Durango", 
                "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "México", "Michoacán de Ocampo", 
                "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla", "Querétaro", 
                "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora", "Tabasco", 
                "Tamaulipas", "Tlaxcala", "Veracruz de Ignacio de la Llave", "Yucatán", "Zacatecas"
            ]
            
            def esperar_y_renombrar_descarga(directorio, estado_nombre, tiempo_inicio, timeout=40):
                """Espera a que termine de descargar el archivo y lo renombra de inmediato a Salario_{estado}.csv"""
                fin = time.time() + timeout
                while time.time() < fin:
                    archivos = [
                        f for f in glob.glob(os.path.join(directorio, "*.csv"))
                        if os.path.getmtime(f) >= (tiempo_inicio - 1)
                        and not f.endswith('.crdownload')
                        and not f.endswith('.tmp')
                        and not os.path.basename(f).startswith("Salario_")
                    ]
                    if archivos:
                        reciente = max(archivos, key=os.path.getmtime)
                        time.sleep(0.5)
                        if os.path.getsize(reciente) > 0:
                            destino = os.path.join(directorio, f"Salario_{estado_nombre}.csv")
                            try:
                                if os.path.exists(destino):
                                    os.remove(destino)
                                os.replace(reciente, destino)
                                return destino
                            except Exception:
                                pass
                    time.sleep(0.5)
                return None

            driver, wait = iniciar_navegador()
            estados_pendientes = estados_totales.copy()
            intentos_estado = {est: 0 for est in estados_totales}

            # Bucle de consultas y descargas individuales (cada una se renombra inmediatamente)
            while estados_pendientes:
                estado = estados_pendientes[0]
                destino_final_estado = os.path.join(TEMP_SALARIOS_DIR, f"Salario_{estado}.csv")

                # Si ya existe con datos, saltar
                if os.path.exists(destino_final_estado) and os.path.getsize(destino_final_estado) > 50:
                    estados_pendientes.pop(0)
                    continue

                if driver is None:
                    for intento_recon in range(3):
                        try:
                            driver, wait = iniciar_navegador()
                            break
                        except Exception as e_recon:
                            tqdm.write(f"⚠️ [Salarios IMSS] Intento {intento_recon+1} de conexión falló: {e_recon}")
                            try:
                                if driver: driver.quit()
                            except Exception: pass
                            driver = None
                            time.sleep(3)
                    if driver is None:
                        tqdm.write(f"❌ [Salarios IMSS] No fue posible inicializar navegador para {estado}. Pasando al siguiente...")
                        intentos_estado[estado] += 1
                        estados_pendientes.append(estados_pendientes.pop(0))
                        continue

                try:
                    esperar_tableau_listo(driver, 5)
                    estado_encontrado = False
                    xpath_estado_box = f"//div[@role='checkbox' and .//a[@title='{estado}']]//div[@class='fakeCheckBox']"
                    
                    for intento_busqueda in range(2):
                        try:
                            search_box = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_search)))
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", search_box)
                            try:
                                search_box.click()
                            except (ElementClickInterceptedException, Exception):
                                driver.execute_script("arguments[0].click();", search_box)
                            
                            driver.execute_script("arguments[0].value = '';", search_box)
                            search_box.send_keys(Keys.CONTROL, "a")
                            search_box.send_keys(Keys.DELETE)
                            time.sleep(0.4) 
                            
                            for letra in estado:
                                search_box.send_keys(letra)
                                time.sleep(0.08)
                                
                            wait.until(EC.text_to_be_present_in_element_value((By.XPATH, xpath_search), estado)) 
                            esperar_tableau_listo(driver, 5)
                            time.sleep(1.2)
                            
                            box_estado = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_estado_box)))
                            ActionChains(driver).move_to_element(box_estado).pause(0.4).click().perform()
                            estado_encontrado = True
                            break 
                        except TimeoutException:
                            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                            time.sleep(1)
                            filtro_entidad = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_filtro_entidad)))
                            driver.execute_script("arguments[0].click();", filtro_entidad)
                            time.sleep(1)
                    
                    if not estado_encontrado:
                        raise Exception(f"Dropdown de Tableau no mostró la opción {estado}.")
                        
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    esperar_tableau_listo(driver, 5)
                    time.sleep(1.5) 
                    
                    # Proceso de Descarga
                    xpath_btn_descarga = "//button[@data-tb-test-id='viz-viewer-toolbar-button-download']"
                    btn_descarga = wait.until(EC.presence_of_element_located((By.XPATH, xpath_btn_descarga)))
                    driver.execute_script("arguments[0].click();", btn_descarga)
                    time.sleep(1) 

                    xpath_crosstab = "//div[@data-tb-test-id='download-flyout-download-crosstab-MenuItem' or (@data-tb-test-id='download-flyout-TextMenuItem' and .//span[normalize-space()='Crosstab'])]"
                    btn_crosstab = wait.until(EC.presence_of_element_located((By.XPATH, xpath_crosstab)))
                    driver.execute_script("arguments[0].click();", btn_crosstab)
                    
                    xpath_csv_label = "//label[@data-tb-test-id='crosstab-options-dialog-radio-csv-Label']"
                    btn_csv = wait.until(EC.presence_of_element_located((By.XPATH, xpath_csv_label)))
                    driver.execute_script("arguments[0].click();", btn_csv)
                    time.sleep(1) 

                    xpath_descarga_final = "//button[@data-tb-test-id='export-crosstab-export-Button']"
                    btn_descarga_final = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_descarga_final)))
                    
                    tiempo_descarga = time.time()
                    driver.execute_script("arguments[0].click();", btn_descarga_final)
                    
                    # Renombrar de inmediato a Salario_{estado}.csv
                    archivo_guardado = esperar_y_renombrar_descarga(TEMP_SALARIOS_DIR, estado, tiempo_descarga)
                    
                    if not archivo_guardado:
                        raise Exception(f"No se detectó el archivo descargado para {estado}.")

                    # Deseleccionar el estado para dejar listo el dropdown
                    esperar_tableau_listo(driver, 5)
                    filtro_entidad = wait.until(EC.presence_of_element_located((By.XPATH, xpath_filtro_entidad)))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filtro_entidad)
                    time.sleep(0.5) 
                    
                    ActionChains(driver).move_to_element(filtro_entidad).pause(0.3).click().perform()
                    time.sleep(1) 
                    
                    search_box = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_search)))
                    search_box.click()
                    search_box.send_keys(Keys.CONTROL, "a")
                    search_box.send_keys(Keys.DELETE)
                    time.sleep(0.3)
                    
                    for letra in estado:
                        search_box.send_keys(letra)
                        time.sleep(0.06)
                    
                    wait.until(EC.text_to_be_present_in_element_value((By.XPATH, xpath_search), estado))
                    time.sleep(1.2)
                    
                    box_estado_limpiar = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_estado_box)))
                    ActionChains(driver).move_to_element(box_estado_limpiar).pause(0.4).click().perform()
                    time.sleep(0.8) 
                    
                    driver.execute_script("arguments[0].value = '';", search_box)
                    wait.until(EC.text_to_be_present_in_element_value((By.XPATH, xpath_search), ""))
                    estados_pendientes.pop(0)
                    
                except Exception as e:
                    intentos_estado[estado] += 1
                    tqdm.write(f"⚠️ [Salarios IMSS] Falla al procesar {estado}: {e}")
                    
                    try:
                        if driver: driver.quit()
                    except Exception: pass
                    driver = None
                    
                    if intentos_estado[estado] < 3:
                        tqdm.write(f"🔄 [Salarios IMSS] Reintentando {estado} (Intento {intentos_estado[estado]}/3). Moviendo al final de la cola...")
                        estados_pendientes.append(estados_pendientes.pop(0))
                    else:
                        tqdm.write(f"❌ [Salarios IMSS] Se agotaron los 3 intentos para {estado}. Continuando con los demás...")
                        estados_pendientes.pop(0)

            # Cierre definitivo del navegador Selenium antes de la consolidación
            if driver:
                try: driver.quit()
                except Exception: pass
                driver = None

            # 2. VERIFICACIÓN DE ARCHIVOS DESCARGADOS
            archivos_por_estado = {
                est: os.path.join(TEMP_SALARIOS_DIR, f"Salario_{est}.csv")
                for est in estados_totales
                if os.path.exists(os.path.join(TEMP_SALARIOS_DIR, f"Salario_{est}.csv"))
                and os.path.getsize(os.path.join(TEMP_SALARIOS_DIR, f"Salario_{est}.csv")) > 50
            }
            
            faltantes = [est for est in estados_totales if est not in archivos_por_estado]
            if faltantes:
                tqdm.write(f"⚠️ [Salarios IMSS] Atención: No se pudieron obtener los siguientes estados: {faltantes}")

            # 3. CONSOLIDACIÓN EN BATCH ("DE GOLPE")
            tqdm.write(f"   📊 [Salarios IMSS] Consolidando de golpe {len(archivos_por_estado)} estados...")
            
            def normalizar_fechas(serie):
                s = serie.astype(str).str.lower().str.strip()
                meses = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12', 'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'}
                for m_nom, m_num in meses.items():
                    s = s.str.replace(rf'\b{m_nom}\b', m_num, regex=True)
                s = s.str.replace(' de ', '-', regex=False).str.replace('.', '', regex=False).str.replace('/', '-').str.replace(' ', '-')
                s = s.apply(lambda x: f"01-{x}" if re.match(r'^\d{2}-\d{2,4}$', str(x)) else x)
                return pd.to_datetime(s, dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

            ruta_salida = os.path.join(INTERMEDIATE_DIR, "salarios_imss.csv")
            df_master = pd.DataFrame()
            if os.path.exists(ruta_salida):
                try:
                    df_master = pd.read_csv(ruta_salida)
                    cols_to_drop = [c for c in df_master.columns if c.endswith('_x') or c.endswith('_y')]
                    if cols_to_drop:
                        df_master = df_master.drop(columns=cols_to_drop)
                    if 'Fecha' in df_master.columns:
                        df_master['Fecha'] = normalizar_fechas(df_master['Fecha'])
                        df_master = df_master.dropna(subset=['Fecha']).groupby('Fecha', as_index=False).first()
                except Exception:
                    df_master = pd.DataFrame()

            for est, ruta_csv in archivos_por_estado.items():
                try:
                    df_temp = pd.read_csv(
                        ruta_csv, skiprows=1, header=None, usecols=[0, 1], 
                        names=['Fecha', est], encoding='utf-16', sep='\t'
                    )
                    df_temp['Fecha'] = normalizar_fechas(df_temp['Fecha'])
                    df_temp = df_temp.dropna(subset=['Fecha']).groupby('Fecha', as_index=False).first()
                    
                    if not df_master.empty:
                        if est in df_master.columns:
                            df_master = df_master.drop(columns=[est])
                        df_master = pd.merge(df_master, df_temp, on='Fecha', how='outer')
                    else: 
                        df_master = df_temp
                except Exception as e_parse:
                    tqdm.write(f"⚠️ [Salarios IMSS] Error leyendo {ruta_csv}: {e_parse}")

            if not df_master.empty:
                df_master = df_master.sort_values(by='Fecha', ascending=True).reset_index(drop=True)
                
                # Formato final esperado por ficha_v4.py: "mes AAAA" (ej. "julio 1997")
                df_export = df_master.copy()
                df_export['Fecha'] = pd.to_datetime(df_export['Fecha']).dt.strftime('%m-%Y')
                meses_inv = {'01': 'enero', '02': 'febrero', '03': 'marzo', '04': 'abril', '05': 'mayo', '06': 'junio', '07': 'julio', '08': 'agosto', '09': 'septiembre', '10': 'octubre', '11': 'noviembre', '12': 'diciembre'}
                for num, nom in meses_inv.items():
                    df_export['Fecha'] = df_export['Fecha'].str.replace(rf'^{num}-', f"{nom} ", regex=True)
                    
                df_export.to_csv(ruta_salida, index=False, encoding='utf-8-sig')

                # Limpieza final de temporales
                for f in glob.glob(os.path.join(TEMP_SALARIOS_DIR, "*")):
                    try: os.remove(f)
                    except Exception: pass

                return f"✅ [Salarios IMSS] Completado. {len(archivos_por_estado)} estados consolidados de golpe."
            else:
                return "⚠️ [Salarios IMSS] El DataFrame maestro quedó vacío."
                
        except Exception as e:
            return f"❌ [Salarios IMSS] Error general: {e}"
        finally:
            if driver:
                try: driver.quit()
                except Exception: pass

# ==============================================================================
# MÓDULO 10: PUESTOS IMSS (Selenium Visible con Anti-Colisión y Temp Aislado)
# ==============================================================================
def procesar_puestos_imss():
    tqdm.write("⏳ [Puestos IMSS] Iniciando extracción directa con Selenium...")
    
    with SELENIUM_LOCK:
        tiempo_inicio_script = time.time() - 2
        driver = None
        
        try:
            for f in glob.glob(os.path.join(TEMP_PUESTOS_DIR, "*")):
                try: os.remove(f)
                except Exception: pass
                
            opciones = webdriver.ChromeOptions()
            prefs = {"download.default_directory" : TEMP_PUESTOS_DIR}
            opciones.add_experimental_option("prefs", prefs)
            opciones.add_argument("--lang=es-MX") 
            
            driver = webdriver.Chrome(options=opciones)
            driver.get("https://public.tableau.com/app/profile/imss.cpe/viz/Histrico_4/Empleo_h?publish=yes")
            wait = WebDriverWait(driver, 20)

            try:
                btn_cookies = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
                btn_cookies.click()
                time.sleep(1) 
            except Exception:
                pass

            iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            driver.switch_to.frame(iframe)
            esperar_tableau_listo(driver, 6)
            time.sleep(2)

            xpath_pestana = "//div[contains(@class, 'tabStoryPointContent') and contains(normalize-space(), 'Nacional - Puestos de Trabajo')]"
            tab_puestos = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_pestana)))
            tab_puestos.click()
            esperar_tableau_listo(driver, 6)
            time.sleep(4)

            # Proceso de Descarga
            xpath_btn_descarga = "//button[@data-tb-test-id='viz-viewer-toolbar-button-download']"
            btn_descarga = wait.until(EC.presence_of_element_located((By.XPATH, xpath_btn_descarga)))
            driver.execute_script("arguments[0].click();", btn_descarga)
            time.sleep(1) 

            xpath_crosstab = "//div[@data-tb-test-id='download-flyout-download-crosstab-MenuItem' or (@data-tb-test-id='download-flyout-TextMenuItem' and .//span[normalize-space()='Crosstab'])]"
            btn_crosstab = wait.until(EC.presence_of_element_located((By.XPATH, xpath_crosstab)))
            driver.execute_script("arguments[0].click();", btn_crosstab)
            time.sleep(2)
            
            xpath_csv_label = "//label[@data-tb-test-id='crosstab-options-dialog-radio-csv-Label']"
            btn_csv = wait.until(EC.presence_of_element_located((By.XPATH, xpath_csv_label)))
            driver.execute_script("arguments[0].click();", btn_csv)
            time.sleep(1) 

            xpath_descarga_final = "//button[@data-tb-test-id='export-crosstab-export-Button']"
            btn_descarga_final = wait.until(EC.presence_of_element_located((By.XPATH, xpath_descarga_final)))
            driver.execute_script("arguments[0].click();", btn_descarga_final)
            time.sleep(5) 

            prefijo_descarga = "Nacional" 
            patron_busqueda = os.path.join(TEMP_PUESTOS_DIR, f"{prefijo_descarga}*.csv")
            archivos_candidatos = glob.glob(patron_busqueda)
            archivos_validos = [f for f in archivos_candidatos if os.path.getmtime(f) >= tiempo_inicio_script and not f.endswith('.crdownload')]

            if archivos_validos:
                archivo_reciente = max(archivos_validos, key=os.path.getmtime)
                df = pd.read_csv(archivo_reciente, skiprows=1, encoding='utf-16', sep='\t')
                
                nuevos_nombres = {df.columns[0]: 'Año', df.columns[1]: 'Mes'}
                df.rename(columns=nuevos_nombres, inplace=True)
                
                try: os.remove(archivo_reciente)
                except Exception: pass
                    
                ruta_salida = os.path.join(INTERMEDIATE_DIR, "puestos_imss.csv") 
                df.to_csv(ruta_salida, index=False, encoding='utf-8-sig')
                
                return f"✅ [Puestos IMSS] Completado. Archivo guardado."
            else:
                return "⚠️ [Puestos IMSS] No se detectó ningún archivo CSV descargado en la carpeta temporal."
                
        except Exception as e:
            return f"❌ [Puestos IMSS] Error general: {e}"
        finally:
            if driver:
                try: driver.quit()
                except Exception: pass

# ==============================================================================
# MÓDULO 11: REMESAS (Banxico API con Determinismo y Sin Trimestres Futuros Vacíos)
# ==============================================================================
entidades_banxico = {
    "SE28528": "Total", "SE29670": "Aguascalientes",
    "SE29671": "Baja California", "SE29672": "Baja California Sur",
    "SE29673": "Campeche", "SE29674": "Coahuila", "SE29675": "Colima",
    "SE29676": "Chiapas", "SE29677": "Chihuahua", "SE29678": "Ciudad de México",
    "SE29679": "Durango", "SE29680": "Guanajuato", "SE29681": "Guerrero",
    "SE29682": "Hidalgo", "SE29683": "Jalisco", "SE29684": "México",
    "SE29685": "Michoacán", "SE29686": "Morelos", "SE29687": "Nayarit",
    "SE29688": "Nuevo León", "SE29689": "Oaxaca", "SE29690": "Puebla",
    "SE29691": "Querétaro", "SE29692": "Quintana Roo", "SE29693": "San Luis Potosí",
    "SE29694": "Sinaloa", "SE29695": "Sonora", "SE29696": "Tabasco",
    "SE29697": "Tamaulipas", "SE29698": "Tlaxcala", "SE29699": "Veracruz",
    "SE29700": "Yucatán", "SE29701": "Zacatecas"
}

def obtener_serie_banxico(token, serie_id):
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie_id}/datos"
    headers = {"Bmx-Token": token}
    for intento in range(3):
        try:
            response = SESION_HTTP.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                data = response.json()
                serie_info = data['bmx']['series'][0]
                df = pd.DataFrame(serie_info['datos'])
                df.columns = ['fecha', serie_info['titulo']]
                df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y')
                df[serie_info['titulo']] = pd.to_numeric(df[serie_info['titulo']].str.replace(',', ''), errors='coerce')
                return df
            else:
                time.sleep(1)
        except requests.exceptions.RequestException:
            time.sleep(1)
    return pd.DataFrame(columns=['fecha', 'valor_nulo'])

def procesar_remesas_banxico():
    tqdm.write("⏳ [Remesas] Iniciando extracción trimestral de Banxico...")
    dates = pd.date_range(start="2003-01-01", end=pd.Timestamp.today(), freq="QS")
    df_master = pd.DataFrame({"fecha": dates})
    errores = 0
    
    barra_progreso = tqdm(entidades_banxico.items(), desc="💸 Remesas    ", unit="edo", leave=True)
    
    for serie_id, nombre_columna in barra_progreso:
        df_temp = obtener_serie_banxico(TOKEN_BANXICO, serie_id)
        if not df_temp.empty and len(df_temp.columns) == 2:
            df_temp.columns = ['fecha', nombre_columna]
            df_master = df_master.merge(df_temp, on="fecha", how="left")
        else:
            errores += 1
            barra_progreso.set_postfix({"Errores de Red": errores})
            
    if not df_master.empty:
        # Filtrar trimestres futuros sin datos (evita agregar filas vacías en Git)
        df_master = df_master.dropna(subset=['Total']).sort_values(by='fecha').reset_index(drop=True)
        df_master['fecha'] = df_master['fecha'].dt.strftime('%Y-%m-%d')
        ruta_salida = os.path.join(INTERMEDIATE_DIR, "remesas_entidad.csv")
        df_master.to_csv(ruta_salida, index=False, encoding='utf-8-sig')
        return f"✅ [Remesas] Completado ({len(df_master)} periodos)."
    return "⚠️ [Remesas] No se pudieron extraer los datos."

# ==============================================================================
# INTERFAZ GRÁFICA DE SELECCIÓN (TKINTER ROBUSTA Y AMIGABLE)
# ==============================================================================
def mostrar_interfaz_seleccion(modulos_disponibles):
    seleccion = []
    
    root = tk.Tk()
    root.title("Panel de Control ETL Estatal - Bancomext")
    root.geometry("400x560")
    root.resizable(False, False)
    root.attributes('-topmost', True)
    
    lbl_titulo = tk.Label(root, text="Módulos de Actualización", font=("Arial", 12, "bold"))
    lbl_titulo.pack(pady=(12, 2))
    lbl_sub = tk.Label(root, text="Selecciona los módulos que deseas procesar:", font=("Arial", 9), fg="#555")
    lbl_sub.pack(pady=(0, 10))
    
    frame_botones_rapidos = tk.Frame(root)
    frame_botones_rapidos.pack(fill='x', padx=30, pady=(0, 8))
    
    variables_checkbox = {}
    
    def seleccionar_todos():
        for var in variables_checkbox.values():
            var.set(True)
            
    def deseleccionar_todos():
        for var in variables_checkbox.values():
            var.set(False)

    btn_todos = tk.Button(frame_botones_rapidos, text="Seleccionar Todos", command=seleccionar_todos, font=("Arial", 8), bg="#E1E1E1", width=18)
    btn_todos.pack(side='left', padx=(0, 5))
    
    btn_ninguno = tk.Button(frame_botones_rapidos, text="Limpiar Selección", command=deseleccionar_todos, font=("Arial", 8), bg="#E1E1E1", width=18)
    btn_ninguno.pack(side='right')

    frame_chk = tk.Frame(root, bd=1, relief="solid")
    frame_chk.pack(fill='both', expand=True, padx=25, pady=(0, 10))
    
    for modulo in modulos_disponibles:
        var = tk.BooleanVar(value=False)
        variables_checkbox[modulo] = var
        chk = tk.Checkbutton(frame_chk, text=modulo, variable=var, font=("Arial", 9), anchor='w')
        chk.pack(fill='x', padx=15, pady=2)
        
    def ejecutar_seleccion():
        for mod, var in variables_checkbox.items():
            if var.get():
                seleccion.append(mod)
        
        if not seleccion:
            messagebox.showwarning("Atención", "Debes seleccionar al menos un módulo para continuar.")
            return
            
        root.destroy()
        
    btn_iniciar = tk.Button(
        root, text="▶ Iniciar Extracción", command=ejecutar_seleccion, 
        bg="#0078D7", fg="white", font=("Arial", 10, "bold"), height=2, cursor="hand2"
    )
    btn_iniciar.pack(fill='x', padx=25, pady=(0, 15))
    
    root.mainloop()
    return seleccion

# ==============================================================================
# ORQUESTADOR PRINCIPAL
# ==============================================================================
def main():
    print("=" * 80)
    print("🚀 ETL ESTATAL UNIFICADO (v2.0 Blindado) - BANCOMEXT 🚀")
    print("=" * 80)
    print(f"📍 Raíz del Proyecto: {PROJECT_ROOT}")
    print(f"📂 Datos Crudos:     {RAW_DIR}")
    print(f"📂 Datos Procesados: {INTERMEDIATE_DIR}")
    print(f"📂 Temporales:       {TEMP_DIR}")
    print(f"🔑 Tokens INEGI activos: {len(TOKENS_INEGI)}")
    print("=" * 80)
    
    mapa_tareas = {
        "PIB (INEGI)": procesar_pib,
        "Exportaciones (INEGI)": procesar_exportaciones,
        "Población (INEGI)": procesar_poblacion_api,
        "ENOE (Descarga Excel)": procesar_enoe_auto,
        "Educación (Anuario)": procesar_educacion,
        "IED (Estructura)": procesar_ied,
        "SAIC (Productividad)": procesar_saic,
        "IMCO (Competitividad)": procesar_imco,
        "Salarios IMSS (Selenium)": procesar_salarios_imss,
        "Puestos IMSS (Selenium)": procesar_puestos_imss,
        "Remesas (Banxico)": procesar_remesas_banxico
    }
    
    nombres_seleccionados = mostrar_interfaz_seleccion(list(mapa_tareas.keys()))
    
    if not nombres_seleccionados:
        print("⚠️ Operación cancelada. No se seleccionó ningún módulo.")
        return
        
    inicio = time.time()
    print(f"\nIniciando extracción para {len(nombres_seleccionados)} módulos seleccionados...")
    for idx, nombre in enumerate(nombres_seleccionados, 1):
        print(f"   [{idx}/{len(nombres_seleccionados)}] {nombre}")
    print("-" * 80)
    
    tareas_a_ejecutar = [(nombre, mapa_tareas[nombre]) for nombre in nombres_seleccionados]
    resumen_resultados = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(tareas_a_ejecutar))) as executor:
        futuros = {executor.submit(func): nombre for nombre, func in tareas_a_ejecutar}
        
        for futuro in concurrent.futures.as_completed(futuros):
            nombre = futuros[futuro]
            try:
                resultado = futuro.result()
                resumen_resultados[nombre] = resultado
                tqdm.write(f"{resultado}")
            except Exception as e:
                mensaje_err = f"❌ [{nombre}] Error no controlado en hilo: {e}"
                resumen_resultados[nombre] = mensaje_err
                tqdm.write(mensaje_err)
                
    duracion = time.time() - inicio
    print("\n" + "=" * 80)
    print(f"✨ PROCESO TERMINADO EN {duracion:.2f} SEGUNDOS ✨")
    print(f"📂 Archivos consolidados en: {INTERMEDIATE_DIR}")
    print("=" * 80)
    print("📊 RESUMEN DE EJECUCIÓN:")
    for nombre in nombres_seleccionados:
        estado = resumen_resultados.get(nombre, "⚠️ Sin estatus registrado")
        print(f"  • {nombre:<30} -> {estado}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
