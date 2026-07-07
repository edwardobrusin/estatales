import random
from tqdm.auto import tqdm
import tkinter as tk
from tkinter import messagebox
import os
import time
import requests
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
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import glob

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

# ==========================================
# 0. CONFIGURACIÓN GLOBAL Y RUTAS
# ==========================================
TOKENS_INEGI = [
    "129ac2e3-e8a6-72c7-58c1-acced5a601bd",
    "8ff1ca1f-4ba0-4abc-b98e-c8a5dffc9467",
    "9d9b582f-0cc1-6e57-9d97-2064cebd95d9",
    "8505df05-4276-f1b8-3c6a-437fe9d77c7a",

    # Puedes agregar tantas como consigas
]

def obtener_token():
    # Elige un token al azar para distribuir la carga equitativamente
    return random.choice(TOKENS_INEGI)

# Detección robusta de directorios
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(SCRIPT_DIR) == 'scripts':
        PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    else:
        PROJECT_ROOT = SCRIPT_DIR
except NameError:
    PROJECT_ROOT = os.getcwd()
    if os.path.basename(PROJECT_ROOT) == 'scripts':
        PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
INTERMEDIATE_DIR = os.path.join(PROJECT_ROOT, "data", "intermediate")

os.makedirs(INTERMEDIATE_DIR, exist_ok=True)

print(f"📍 Raíz del Proyecto: {PROJECT_ROOT}")
print(f"📂 Datos Crudos: {RAW_DIR}")
print(f"📂 Datos Procesados: {INTERMEDIATE_DIR}")
print("-" * 80)

# ==========================================
# MÓDULO 1: PIB (API)
# ==========================================
def procesar_pib():
    print("⏳ [PIB] Iniciando extracción exhaustiva...")
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
        token_actual = obtener_token()
        url = f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{ind_clave}/es/{clave_estado}/false/BIE-BISE/2.0/{token_actual}?type=json"
        
        errores_locales = 0
        for intento in range(3):
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        res_locales = []
                        if 'Series' in data and data['Series']:
                            serie = data['Series'][0].get('OBSERVATIONS', [])
                            serie_sorted = sorted(serie, key=lambda x: x.get('TIME_PERIOD', ''))
                            for obs in serie_sorted:
                                res_locales.append({
                                    'Indicador': ind_nombre, 'Clave_Indicador': ind_clave,
                                    'Estado_ID': obs.get('COBER_GEO', clave_estado),
                                    'Periodo': int(obs.get('TIME_PERIOD')), 'Valor': float(obs.get('OBS_VALUE', 0))
                                })
                        return res_locales, errores_locales, "EXITO"
                    except Exception:
                        return [], errores_locales, "NO_DATA"
                elif r.status_code == 429 or r.status_code >= 500:
                    errores_locales += 1
                    time.sleep(1 + random.uniform(0.1, 1.5))
                else:
                    return [], errores_locales, "NO_DATA"
            except requests.exceptions.RequestException:
                errores_locales += 1
                time.sleep(1 + random.uniform(0.1, 1.5))
        return [], errores_locales, "RETRY"

    errores_totales = 0
    tareas_pendientes = tareas.copy()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TOKENS_INEGI) * 2) as executor:
        barra_progreso = tqdm(
            total=len(tareas_pendientes), 
            desc="📊 PIB        ", 
            unit="req",
            position=0,
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
        df.to_csv(os.path.join(INTERMEDIATE_DIR, "pib_entidad.csv"), index=False)
        return f"✅ [PIB] Completado ({len(df)} registros)."
    return "⚠️ [PIB] No se obtuvieron datos."

# ==========================================
# MÓDULO 2: EXPORTACIONES (API)
# ==========================================
def procesar_exportaciones():
    print("⏳ [Exportaciones] Iniciando extracción detallada...")
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
        token_actual = obtener_token()
        url = f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{ind_clave}/es/{clave_estado}/false/BIE-BISE/2.0/{token_actual}?type=json"
        
        errores_locales = 0
        for intento in range(3):
            try:
                r = requests.get(url, timeout=10)
                
                if r.status_code == 200:
                    try:
                        data = r.json()
                        res_locales = []
                        if 'Series' in data and data['Series']:
                            serie = data['Series'][0].get('OBSERVATIONS', [])
                            serie_sorted = sorted(serie, key=lambda x: x.get('TIME_PERIOD', ''))
                            if serie_sorted:
                                max_year = int(serie_sorted[-1]['TIME_PERIOD'][:4])
                                for obs in serie_sorted:
                                    if int(obs['TIME_PERIOD'][:4]) >= (max_year - 1):
                                        res_locales.append({
                                            'Sector': ind_nombre, 'Clave_Indicador': ind_clave,
                                            'Estado_ID': clave_estado, 'Periodo': obs.get('TIME_PERIOD'),
                                            'Valor': float(obs.get('OBS_VALUE', 0))
                                        })
                        return res_locales, errores_locales, "EXITO"
                    except Exception:
                        return [], errores_locales, "NO_DATA"

                elif r.status_code == 429 or r.status_code >= 500:
                    errores_locales += 1
                    time.sleep(1 + random.uniform(0.1, 1.5))
                
                else:
                    return [], errores_locales, "NO_DATA"
                    
            except requests.exceptions.RequestException: 
                errores_locales += 1
                time.sleep(1 + random.uniform(0.1, 1.5))
                
        return [], errores_locales, "RETRY"

    errores_totales = 0
    tareas_pendientes = tareas.copy()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TOKENS_INEGI) * 2) as executor:
        barra_progreso = tqdm(
            total=len(tareas_pendientes), 
            desc="📦 Exportaciones", 
            unit="req",
            position=1,
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
        df.to_csv(os.path.join(INTERMEDIATE_DIR, "exportaciones_entidad.csv"), index=False)
        return f"✅ [Exportaciones] Completado ({len(df)} registros)."
    return "⚠️ [Exportaciones] No se obtuvieron datos."

# ==========================================
# MÓDULO 3: POBLACIÓN (API)
# ==========================================
def procesar_poblacion_api():
    print("⏳ [Población] Iniciando extracción de pirámide completa...")
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
        token_actual = obtener_token()
        url = f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{ind_clave}/es/{clave_estado}/true/BISE/2.0/{token_actual}?type=json"
        
        errores_locales = 0
        for intento in range(3):
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    if 'Series' in data and data['Series']:
                        obs = data['Series'][0]['OBSERVATIONS'][0]
                        return [{
                            'Indicador': desc, 'Clave_Indicador': ind_clave,
                            'Estado_ID': clave_estado, 'Periodo': obs.get('TIME_PERIOD'),
                            'Valor': float(obs.get('OBS_VALUE', 0))
                        }], errores_locales
                    return [], errores_locales
                else: 
                    errores_locales += 1
                    time.sleep(1 + random.uniform(0.1, 1.5))
            except Exception: 
                errores_locales += 1
                time.sleep(1 + random.uniform(0.1, 1.5))
        return [], errores_locales

    errores_totales = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TOKENS_INEGI) * 2) as executor:
        futuros = {executor.submit(hacer_peticion_pob, t): t for t in tareas}
        
        barra_progreso = tqdm(
            concurrent.futures.as_completed(futuros), 
            total=len(tareas), 
            desc="👥 Población  ", 
            unit="req",
            position=2, # Carril 3
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
        df.to_csv(os.path.join(INTERMEDIATE_DIR, "poblacion_edad.csv"), index=False)
        return f"✅ [Población] Completado ({len(df)} registros)."
    return "⚠️ [Población] No se obtuvieron datos."

# ==========================================
# MÓDULO 4: ENOE (Descarga + PEA Corregida)
# ==========================================
def procesar_enoe_auto():
    print("⏳ [ENOE] Iniciando descarga y procesamiento...")
    
    base_url = "https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/tabulados/"
    anio_actual = datetime.now().year
    url_final, anio_found, trim_found = None, None, None
    
    encontrado = False
    for a in [anio_actual, anio_actual-1]:
        if encontrado: break
        for t in ["trim4", "trim3", "trim2", "trim1"]:
            test_url = f"{base_url}enoe_indicadores_estrategicos_{a}_{t}_xls.zip"
            try:
                r = requests.head(test_url, timeout=5)
                content_type = r.headers.get('Content-Type', '').lower()
                if r.status_code == 200 and ('zip' in content_type or 'octet-stream' in content_type):
                    url_final = test_url; anio_found = a; trim_found = t; encontrado = True
                    break
            except: pass
            
    if not url_final: return "❌ [ENOE] URL no encontrada."

    try:
        print(f"   📥 Descargando: {url_final}")
        r = requests.get(url_final)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        
        archivos = [f for f in z.namelist() if ("Entidades/" in f or "Nacional/" in f) and (f.endswith('.xlsx') or f.endswith('.xls'))]
        
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
                                col_val = c; break
                        except: continue
                    break
            
            context = {i:"" for i in range(5)}
            sticky = {1:""}
            
            for idx, row in df.iterrows():
                cols = [str(row[i]).strip() if i < len(row) and pd.notna(row[i]) else "" for i in range(5)]
                indent = -1
                txt_row = ""
                
                for i, txt in enumerate(cols):
                    if txt:
                        indent = i; txt_row = txt; context[i] = txt
                        for j in range(i+1, 5): 
                            context[j] = ""; 
                            if j in sticky: sticky[j]=""
                        break
                
                if not txt_row: continue
                
                if indent == 1 and re.match(r'^(\d+\.?\d*)\s', txt_row): sticky[1] = txt_row
                
                path = [context[0]]
                if indent == 1 and not re.match(r'^(\d+\.?\d*)\s', txt_row) and sticky[1]:
                    path.append(sticky[1]); path.append(txt_row)
                else: path.append(context[1])
                path += [context[k] for k in range(2,5)]
                
                path_str = " | ".join([p.lower() for p in path if p])
                
                for kpi, (padre, target) in config_enoe.items():
                    if target.lower() in txt_row.lower() and padre.lower() in path_str:
                        try: 
                            val_str = str(row[col_val]).replace(",","").replace(" ", "")
                            registro[kpi] = float(val_str)
                        except: pass
            
            datos.append(registro)

        df_out = pd.DataFrame(datos)
        df_out = limpiar_columna_estado(df_out)
        outfile = os.path.join(INTERMEDIATE_DIR, "enoe_indicadores.csv")
        df_out.to_csv(outfile, index=False)
        return f"✅ [ENOE] Completado ({anio_found}-{trim_found})."
        
    except Exception as e: return f"❌ [ENOE] Error: {e}"

# ==========================================
# MÓDULO 5: EDUCACIÓN (Local)
# ==========================================
def procesar_educacion():
    print("⏳ [Educación] Procesando anuario (Generando Top 3 separados)...")
    
    archivos = [f for f in os.listdir(RAW_DIR) if f.startswith("base_anuario_") and f.endswith(".xlsx")]
    if not archivos:
        return "⚠️ [Educación] Falta archivo base_anuario_####-####.xlsx"
    
    archivo_anuario = archivos[0]
    fpath = os.path.join(RAW_DIR, archivo_anuario)
    
    match = re.search(r'base_anuario_(\d{4}-\d{4})\.xlsx', archivo_anuario)
    ciclo_val = match.group(1) if match else "¿?"
    
    try:
        df = pd.read_excel(fpath, sheet_name="Base de datos")
        
        # Limpieza de columnas numéricas
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
        
        # --- 1. TOTALES (INTACTO) ---
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
        
    except Exception as e: return f"❌ [Educación] Error: {e}"
# ==========================================
# MÓDULO 6: IED (Local) - GRUPOS POR SECTOR Y SIN %
# ==========================================
def procesar_ied():
    print("⏳ [IED] Procesando datos complejos (Totales 3 Dígitos y Detalle)...")
    fpath = os.path.join(RAW_DIR, "2026_1T_Flujos_EF_OR_11A.xlsx")
    
    if not os.path.exists(fpath): 
        return f"⚠️ [IED] Falta {fpath}"
    
    try:
        # 1. MAPEO DE COLUMNAS
        df_head = pd.read_excel(fpath, sheet_name='EF por Actividad Econ', header=None, nrows=10)
        
        header_idx = None
        for idx, row in df_head.iterrows():
            if "Entidad Federativa" in str(row[0]):
                header_idx = idx
                break
        
        if header_idx is None: return "❌ [IED] Sin encabezados."
        
        years_row = df_head.iloc[header_idx].tolist()
        quarters_row = df_head.iloc[header_idx + 1].tolist()
        
        col_map = {}
        current_year = None
        for i in range(1, len(years_row)):
            if pd.notna(years_row[i]):
                try:
                    y = int(float(years_row[i]))
                    if y > 2000: current_year = y
                except: pass
            if current_year and pd.notna(quarters_row[i]):
                try:
                    q = int(float(quarters_row[i]))
                    if 1 <= q <= 4: col_map[i] = (current_year, q)
                except: pass
        
        if not col_map: return "❌ [IED] Error mapeo columnas."
        
        last_period = max(col_map.values()) # (Año, Trim)
        prev_period = (last_period[0]-1, last_period[1])
        
        idx_act = [k for k, v in col_map.items() if v == last_period][0]
        idx_prev = [k for k, v in col_map.items() if v == prev_period]
        idx_prev = idx_prev[0] if idx_prev else None
        
        # 2. EXTRACCIÓN (Solo 3 dígitos)
        df_data = pd.read_excel(fpath, sheet_name='EF por Actividad Econ', header=header_idx+2)
        
        def clean(x):
            if pd.isna(x): return 0.0
            s = str(x).strip().replace(',','')
            try: return float(s)
            except: return 0.0
            
        def clasificar(cod):
            if cod.startswith('1'): return 'Primaria'
            if cod.startswith(('2','3')): return 'Secundaria'
            return 'Terciaria'
            
        filas = []
        estado_act = None
        
        for i, row in df_data.iterrows():
            c = str(row.iloc[0]).strip()
            if not c or c == 'nan': continue
            
            match = re.match(r'^(\d{2,6}|31-33)\s+(.*)', c)
            if match:
                cod, desc = match.groups()
                # Filtro Estricto: Solo 3 dígitos
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
            
            # --- NUEVA LÓGICA: Top 3 Inversiones (>0) y Top 3 Desinversiones (<0) ---
            tops = []
            for est in df_clean['Estado'].unique():
                d_est = df_clean[df_clean['Estado'] == est]
                for sec in ['Primaria', 'Secundaria', 'Terciaria']:
                    d_sec = d_est[d_est['Sector'] == sec]
                    
                    # 1. Top 3 Inversiones (Mayores a 0, orden descendente)
                    d_inv = d_sec[d_sec['Inversion'] > 0]
                    top3_inv = d_inv.sort_values('Inversion', ascending=False).head(3).copy()
                    if not top3_inv.empty:
                        top3_inv['Clasificacion_Flujo'] = 'Inversión Positiva'
                        tops.append(top3_inv)
                        
                    # 2. Top 3 Desinversiones (Menores a 0, orden ascendente para capturar las mayores fugas)
                    d_des = d_sec[d_sec['Inversion'] < 0]
                    top3_des = d_des.sort_values('Inversion', ascending=True).head(3).copy()
                    if not top3_des.empty:
                        top3_des['Clasificacion_Flujo'] = 'Desinversión'
                        tops.append(top3_des)
            
            if tops:
                df_tops = pd.concat(tops)
                
                df_tops['Anio'] = last_period[0]
                df_tops['Trimestre'] = last_period[1]
                
                # Reordenamos columnas para que 'Clasificacion_Flujo' quede en una posición lógica (después de Sector)
                cols = df_tops.columns.tolist()
                cols.insert(4, cols.pop(cols.index('Clasificacion_Flujo')))
                df_tops = df_tops[cols]
                
                # Opcional: Cambié el nombre del archivo para reflejar que ahora incluye ambos flujos
                df_tops.to_csv(os.path.join(INTERMEDIATE_DIR, "ied_top3_sectores.csv"), index=False)
                return f"✅ [IED] Completado (Periodo {last_period})."
        
        return "⚠️ [IED] Sin datos extraídos."
        
    except Exception as e: return f"❌ [IED] Error: {e}"

# ==========================================
# MÓDULO 7: SAIC (Local)
# ==========================================
def procesar_saic():
    print("⏳ [SAIC] Procesando censo...")
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
            return float(val)

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
        
    except Exception as e: return f"❌ [SAIC] Error: {e}"

# ==========================================
# MÓDULO 8: IMCO (Local)
# ==========================================
def procesar_imco():
    print("⏳ [IMCO] Procesando competitividad...")
    f_gen = os.path.join(RAW_DIR, "imco_general.csv")
    f_des = os.path.join(RAW_DIR, "imco_desagregado.csv")
    if not os.path.exists(f_gen) or not os.path.exists(f_des): return "⚠️ [IMCO] Faltan archivos."
    
    try:
        # General
        try: df_g = pd.read_csv(f_gen, encoding='utf-8')
        except: df_g = pd.read_csv(f_gen, encoding='latin-1')
        cols_map = {c: 'Año' if 'AÃ±o' in c else 'Cambio' if 'posiciÃ³n' in c else c for c in df_g.columns}
        df_g.rename(columns=cols_map, inplace=True)
        df_g = df_g[df_g['Año'] == df_g['Año'].max()]
        df_g = limpiar_columna_estado(df_g)
        df_g.to_csv(os.path.join(INTERMEDIATE_DIR, "imco_general_final.csv"), index=False)
        
        # Desagregado
        try: df_d = pd.read_csv(f_des, encoding='utf-8')
        except: df_d = pd.read_csv(f_des, encoding='latin-1')
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
            df_fin = df_d; df_fin['Cambio_Posicion'] = 0
            
        df_fin.to_csv(os.path.join(INTERMEDIATE_DIR, "imco_desagregado_final.csv"), index=False)
        return "✅ [IMCO] Completado."
    except Exception as e: return f"❌ [IMCO] Error: {e}"

# ==========================================
# MÓDULO 9: SALARIOS IMSS (Selenium)
# ==========================================
def procesar_salarios_imss():
    print("⏳ [Salarios IMSS] Iniciando extracción de 32 estados con Selenium...")
    tiempo_inicio_script = time.time() - 2
    
    # Inicializamos el driver como None para poder cerrarlo de forma segura en caso de error
    driver = None 
    try:
        TEMP_DIR = os.path.join(PROJECT_ROOT, "data", "temp")
        os.makedirs(TEMP_DIR, exist_ok=True)
        for f in glob.glob(os.path.join(TEMP_DIR, "*")):
            os.remove(f)
            
        opciones = webdriver.ChromeOptions()
        prefs = {"download.default_directory" : TEMP_DIR}
        opciones.add_experimental_option("prefs", prefs)
        opciones.add_argument("--lang=es-MX") 
        
        driver = webdriver.Chrome(options=opciones)
        driver.get("https://public.tableau.com/app/profile/imss.cpe/viz/Histrico_4/Empleo_h?publish=yes")
        wait = WebDriverWait(driver, 20)
        df_master = pd.DataFrame()

        # A. Manejar el banner de cookies
        try:
            btn_cookies = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            btn_cookies.click()
            time.sleep(1) 
        except: pass

        # B. Entrar al iFrame y Pestaña
        iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        driver.switch_to.frame(iframe)
        
        xpath_pestana = "//div[contains(@class, 'tabStoryPointContent') and contains(normalize-space(), 'Cifras de salario')]"
        tab_salario = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_pestana)))
        tab_salario.click()
        time.sleep(2)

        # D y E. Filtro Entidad y (Todo)
        xpath_filtro_entidad = "(//span[@role='combobox'])[1]"
        filtro_entidad = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_filtro_entidad)))
        filtro_entidad.click()
        time.sleep(2)
        
        xpath_todo_box = "//div[@role='checkbox' and .//a[@title='(Todo)' or @title='(All)']]//div[@class='fakeCheckBox']"
        try:
            box_todo = wait.until(EC.presence_of_element_located((By.XPATH, xpath_todo_box)))
            ActionChains(driver).move_to_element(box_todo).click().perform()
        except: pass
        time.sleep(2) 

        estados_pendientes = [
            "Aguascalientes", "Baja California", "Baja California Sur", "Campeche", "Chiapas", 
            "Chihuahua", "Ciudad de México", "Coahuila de Zaragoza", "Colima", "Durango", 
            "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "México", "Michoacán de Ocampo", 
            "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla", "Querétaro", 
            "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora", "Tabasco", 
            "Tamaulipas", "Tlaxcala", "Veracruz de Ignacio de la Llave", "Yucatán", "Zacatecas"
        ]
        xpath_search = "//textarea[contains(@class, 'QueryBox')]"

        def esperar_descarga(directorio, tiempo_inicio, timeout=45):
            fin = time.time() + timeout
            while time.time() < fin:
                archivos = glob.glob(os.path.join(directorio, "Salario*.csv"))
                archivos_validos = [f for f in archivos if os.path.getmtime(f) >= tiempo_inicio and not f.endswith('.crdownload') and not f.endswith('.tmp')]
                if archivos_validos:
                    return max(archivos_validos, key=os.path.getmtime)
                time.sleep(0.5)
            return None

        intentos_estado = {est: 0 for est in estados_pendientes}

        while estados_pendientes:
            estado = estados_pendientes[0]
            try:
                estado_encontrado = False
                xpath_estado_box = f"//div[@role='checkbox' and .//a[@title='{estado}']]//div[@class='fakeCheckBox']"
                
                for intento_busqueda in range(2):
                    try:
                        search_box = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_search)))
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", search_box)
                        search_box.click() # Asegurar foco
                        
                        # Doble limpieza para vaciar el DOM
                        driver.execute_script("arguments[0].value = '';", search_box)
                        search_box.send_keys(Keys.CONTROL, "a")
                        search_box.send_keys(Keys.DELETE)
                        time.sleep(0.5) 
                        
                        # Efecto "Typing"
                        for letra in estado:
                            search_box.send_keys(letra)
                            time.sleep(0.08) # Simula velocidad humana
                            
                        wait.until(EC.text_to_be_present_in_element_value((By.XPATH, xpath_search), estado)) 
                        time.sleep(1.5) # Pausa crítica para que Tableau filtre la lista y renderice el checkbox
                        
                        # Cambiamos presence_of_element_located por element_to_be_clickable
                        box_estado = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath_estado_box)))
                        ActionChains(driver).move_to_element(box_estado).pause(0.5).click().perform()
                        estado_encontrado = True
                        break 
                    except TimeoutException:
                        # Mecanismo de acción-reacción: Esc, click al filtro y reintento
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(1)
                        filtro_entidad = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_filtro_entidad)))
                        driver.execute_script("arguments[0].click();", filtro_entidad)
                        time.sleep(1)
                
                if not estado_encontrado:
                    # Detona el reinicio limpio desde cero con la variable de estado
                    raise Exception(f"Bug de Tableau: Dropdown bloqueado al buscar {estado}.")
                    
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(2) 
                
                # Proceso de Descarga
                xpath_btn_descarga = "//button[@data-tb-test-id='viz-viewer-toolbar-button-download']"
                btn_descarga = wait.until(EC.presence_of_element_located((By.XPATH, xpath_btn_descarga)))
                driver.execute_script("arguments[0].click();", btn_descarga)
                time.sleep(1) 

                xpath_crosstab = "//div[@data-tb-test-id='download-flyout-download-crosstab-MenuItem']"
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
                
                archivo_reciente = esperar_descarga(TEMP_DIR, tiempo_descarga)
                
                if archivo_reciente:
                    df_temp = pd.read_csv(
                        archivo_reciente, skiprows=1, header=None, usecols=[0, 1], 
                        names=['Fecha', estado], encoding='utf-16', sep='\t'
                    )
                    df_temp['Fecha'] = df_temp['Fecha'].astype(str).str.replace(' de ', ' ', regex=False).str.strip()
                    
                    if df_master.empty: df_master = df_temp
                    else: df_master = pd.merge(df_master, df_temp, on='Fecha', how='outer')
                        
                    try: os.remove(archivo_reciente)
                    except: pass

                # Reset
                filtro_entidad = wait.until(EC.presence_of_element_located((By.XPATH, xpath_filtro_entidad)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filtro_entidad)
                time.sleep(1) 
                
                ActionChains(driver).move_to_element(filtro_entidad).pause(0.5).click().perform()
                time.sleep(1) 
                
                search_box = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_search)))
                search_box.click()
                search_box.send_keys(Keys.CONTROL, "a")
                search_box.send_keys(Keys.DELETE)
                time.sleep(0.5)
                
                # Efecto "Typing" en la limpieza
                for letra in estado:
                    search_box.send_keys(letra)
                    time.sleep(0.08)
                
                wait.until(EC.text_to_be_present_in_element_value((By.XPATH, xpath_search), estado))
                time.sleep(1.5)
                
                box_estado_limpiar = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_estado_box)))
                ActionChains(driver).move_to_element(box_estado_limpiar).pause(0.5).click().perform()
                time.sleep(1) 
                
                driver.execute_script("arguments[0].value = '';", search_box)
                wait.until(EC.text_to_be_present_in_element_value((By.XPATH, xpath_search), ""))
                estados_pendientes.pop(0)
                
            except Exception:
                intentos_estado[estado] += 1
                if intentos_estado[estado] < 3:
                    estados_pendientes.append(estados_pendientes.pop(0))
                    driver.quit()
                    
                    driver = webdriver.Chrome(options=opciones)
                    driver.get("https://public.tableau.com/app/profile/imss.cpe/viz/Histrico_4/Empleo_h?publish=yes")
                    wait = WebDriverWait(driver, 20)
                    
                    iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                    driver.switch_to.frame(iframe)
                    
                    tab_salario = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_pestana)))
                    tab_salario.click()
                    
                    filtro_entidad = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_filtro_entidad)))
                    filtro_entidad.click()
                else:
                    estados_pendientes.pop(0)

        # Ordenar Cronológicamente y Guardar
        if not df_master.empty:
            meses = {
                'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
            }
            df_master['Fecha_Temp'] = df_master['Fecha'].str.lower().str.strip()
            for mes_nombre, mes_numero in meses.items():
                df_master['Fecha_Temp'] = df_master['Fecha_Temp'].str.replace(mes_nombre, f"{mes_numero}/", regex=False)
            df_master['Fecha_Temp'] = df_master['Fecha_Temp'].str.replace(' ', '', regex=False)
            df_master['Fecha_Temp'] = pd.to_datetime(df_master['Fecha_Temp'], format='%m/%Y', errors='coerce')
            df_master = df_master.sort_values(by='Fecha_Temp', ascending=True).reset_index(drop=True)
            df_master = df_master.drop(columns=['Fecha_Temp'])
            
            ruta_salida = os.path.join(INTERMEDIATE_DIR, "salarios_imss.csv")
            df_master.to_csv(ruta_salida, index=False, encoding='utf-8-sig')
            
            driver.quit()
            return f"✅ [Salarios IMSS] Completado. Archivo consolidado guardado."
        else:
            driver.quit()
            return "⚠️ [Salarios IMSS] El DataFrame maestro está vacío."
            
    except Exception as e:
        if driver: driver.quit()
        return f"❌ [Salarios IMSS] Error general: {e}"


# ==========================================
# MÓDULO 10: PUESTOS IMSS (Selenium)
# ==========================================
def procesar_puestos_imss():
    print("⏳ [Puestos IMSS] Iniciando extracción directa con Selenium...")
    tiempo_inicio_script = time.time() - 2
    driver = None
    
    try:
        opciones = webdriver.ChromeOptions()
        prefs = {"download.default_directory" : RAW_DIR}
        opciones.add_experimental_option("prefs", prefs)
        opciones.add_argument("--lang=es-MX") 
        
        driver = webdriver.Chrome(options=opciones)
        driver.get("https://public.tableau.com/app/profile/imss.cpe/viz/Histrico_4/Empleo_h?publish=yes")
        wait = WebDriverWait(driver, 20)

        try:
            btn_cookies = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            btn_cookies.click()
            time.sleep(1) 
        except: pass

        iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        driver.switch_to.frame(iframe)
        time.sleep(2) # Breve pausa para asegurar que el iframe cargó

        # NUEVO PASO: Seleccionar la pestaña "Nacional - Puestos de Trabajo"
        xpath_pestana = "//div[contains(@class, 'tabStoryPointContent') and contains(normalize-space(), 'Nacional - Puestos de Trabajo')]"
        tab_puestos = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_pestana)))
        tab_puestos.click()
        time.sleep(5) # Pausa un poco más larga para dejar que los datos de la pestaña rendericen

        # Proceso de Descarga
        xpath_btn_descarga = "//button[@data-tb-test-id='viz-viewer-toolbar-button-download']"
        btn_descarga = wait.until(EC.presence_of_element_located((By.XPATH, xpath_btn_descarga)))
        driver.execute_script("arguments[0].click();", btn_descarga)
        time.sleep(1) 

        xpath_crosstab = "//div[@data-tb-test-id='download-flyout-download-crosstab-MenuItem']"
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

        # Búsqueda quirúrgica y limpieza
        prefijo_descarga = "Nacional" 
        patron_busqueda = os.path.join(RAW_DIR, f"{prefijo_descarga}*.csv")
        archivos_candidatos = glob.glob(patron_busqueda)
        archivos_validos = [f for f in archivos_candidatos if os.path.getmtime(f) >= tiempo_inicio_script]

        if archivos_validos:
            archivo_reciente = max(archivos_validos, key=os.path.getmtime)
            df = pd.read_csv(archivo_reciente, skiprows=1, encoding='utf-16', sep='\t')
            
            nuevos_nombres = {df.columns[0]: 'Año', df.columns[1]: 'Mes'}
            df.rename(columns=nuevos_nombres, inplace=True)
            
            try: os.remove(archivo_reciente)
            except: pass
                
            ruta_salida = os.path.join(INTERMEDIATE_DIR, "puestos_imss.csv") 
            df.to_csv(ruta_salida, index=False, encoding='utf-8-sig')
            
            driver.quit()
            return f"✅ [Puestos IMSS] Completado. Archivo guardado."
        else:
            driver.quit()
            return "⚠️ [Puestos IMSS] No se detectó ningún archivo CSV descargado."
            
    except Exception as e:
        if driver: driver.quit()
        return f"❌ [Puestos IMSS] Error general: {e}"

# ==========================================
# MÓDULO 11: REMESAS (Banxico API)
# ==========================================
TOKEN_BANXICO = "3cf05ba180ebc8fa6bac83d6473f5c287fd4a5d28c8d0411ec9c2e896b844b3e"

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
            response = requests.get(url, headers=headers, timeout=10)
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
    print("⏳ [Remesas] Iniciando extracción trimestral de Banxico...")
    dates = pd.date_range(start="2003-01-01", end=pd.Timestamp.today(), freq="QS")
    df_master = pd.DataFrame({"fecha": dates})
    errores = 0
    
    # Se agrega leave=True y un desc espaciado para alinear con tu TQDM
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
        df_master = df_master.sort_values(by='fecha').reset_index(drop=True)
        df_master['fecha'] = df_master['fecha'].dt.strftime('%Y-%m-%d')
        ruta_salida = os.path.join(INTERMEDIATE_DIR, "remesas_entidad.csv")
        df_master.to_csv(ruta_salida, index=False, encoding='utf-8-sig')
        return f"✅ [Remesas] Completado ({len(df_master)} periodos)."
    return "⚠️ [Remesas] No se pudieron extraer los datos."

# ==========================================
# POP-UP SELECCIÓN
# ==========================================

def mostrar_interfaz_seleccion(modulos_disponibles):
    seleccion = []
    
    root = tk.Tk()
    root.title("Selección de Módulos ETL")
    root.geometry("320x450")
    root.attributes('-topmost', True) # Mantiene la ventana siempre visible
    
    tk.Label(root, text="Selecciona los módulos a actualizar:", font=("Arial", 11, "bold")).pack(pady=10)
    
    variables_checkbox = {}
    
    # Crear un checkbox por cada módulo disponible
    for modulo in modulos_disponibles:
        var = tk.BooleanVar(value=False) # Por defecto, todos están marcados
        variables_checkbox[modulo] = var
        chk = tk.Checkbutton(root, text=modulo, variable=var, font=("Arial", 10))
        chk.pack(anchor='w', padx=40)
        
    def ejecutar_seleccion():
        for mod, var in variables_checkbox.items():
            if var.get():
                seleccion.append(mod)
        
        if not seleccion:
            messagebox.showwarning("Advertencia", "Debes seleccionar al menos un módulo.")
            return
            
        root.destroy()
        
    btn_iniciar = tk.Button(root, text="Iniciar ETL", command=ejecutar_seleccion, bg="#0078D7", fg="white", font=("Arial", 10, "bold"), width=15)
    btn_iniciar.pack(pady=20)
    
    root.mainloop()
    return seleccion

# ==========================================
# ORQUESTADOR
# ==========================================
def main():
    print("\n🚀 CONFIGURANDO ETL ESTATAL UNIFICADO 🚀\n")
    
    # Diccionario para relacionar nombres bonitos con tus funciones
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
    
    # Lanzar pop-up
    nombres_seleccionados = mostrar_interfaz_seleccion(list(mapa_tareas.keys()))
    
    # Si se cerró la ventana sin seleccionar o lanzar
    if not nombres_seleccionados:
        print("⚠️ Operación cancelada. No se ejecutarán módulos.")
        return
        
    tareas_a_ejecutar = [mapa_tareas[nombre] for nombre in nombres_seleccionados]
    
    inicio = time.time()
    print(f"Iniciando extracción para {len(tareas_a_ejecutar)} módulos seleccionados...")
    
    # El Executor solo recibe las tareas que pasaron el filtro
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futuros = {executor.submit(t): t.__name__ for t in tareas_a_ejecutar}
        for futuro in concurrent.futures.as_completed(futuros):
            tqdm.write(f"{futuro.result()}") # <--- IMPRESIÓN SEGURA
                
    print(f"\n✨ PROCESO TERMINADO EN {time.time()-inicio:.2f} SEGUNDOS ✨")
    print(f"📂 Archivos en: {INTERMEDIATE_DIR}")

if __name__ == "__main__":
    main()