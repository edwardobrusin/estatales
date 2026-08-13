import pandas as pd
import os

# 1. Catálogo de estados
STATE_MAP = {
    1: 'Aguascalientes', 2: 'Baja California', 3: 'Baja California Sur', 4: 'Campeche',
    5: 'Coahuila', 6: 'Colima', 7: 'Chiapas', 8: 'Chihuahua',
    9: 'Ciudad de México', 10: 'Durango', 11: 'Guanajuato', 12: 'Guerrero',
    13: 'Hidalgo', 14: 'Jalisco', 15: 'México', 16: 'Michoacán',
    17: 'Morelos', 18: 'Nayarit', 19: 'Nuevo León', 20: 'Oaxaca',
    21: 'Puebla', 22: 'Querétaro', 23: 'Quintana Roo', 24: 'San Luis Potosí',
    25: 'Sinaloa', 26: 'Sonora', 27: 'Tabasco', 28: 'Tamaulipas',
    29: 'Tlaxcala', 30: 'Veracruz', 31: 'Yucatán', 32: 'Zacatecas'
}

# 2. Regla 1 y 3: Ignorar Primario y Comercio de Terciario
SUBSECTORES_VALIDOS_PIB = [
    "Minería", 
    "Generación, transmisión y distribución de energía eléctrica, agua y gas", 
    "Construcción", 
    "Industrias manufactureras",
    "Transportes, correos y almacenamiento", 
    "Información en medios masivos", 
    "Servicios financieros y de seguros", 
    "Servicios inmobiliarios y de alquiler de bienes", 
    "Servicios profesionales, científicos y técnicos", 
    "Corporativos", 
    "Servicios de apoyo a los negocios y manejo de residuos", 
    "Servicios educativos", 
    "Servicios de salud y de asistencia social", 
    "Servicios de esparcimiento culturales y deportivos", 
    "Servicios de alojamiento temporal y de preparación de alimentos y bebidas", 
    "Otros servicios excepto actividades gubernamentales", 
    "Actividades legislativas, gubernamentales"
]

MANUFACTURA_ACTS = [
    "Industria alimentaria", "Bebidas y tabaco", "Insumos, acabados y productos textiles", 
    "Prendas de vestir y productos de cuero y piel", "Industria de la madera", "Industria del papel", 
    "Productos derivados del petróleo y carbón, química, plástico y hule", 
    "Productos a base de minerales no metálicos", "Metálicas básicas y productos metálicos", 
    "Maquinaria y equipo, computación, electrónicos y accesorios", "Muebles, colchones y persianas", 
    "Otras industrias manufactureras"
]

# Regla 2: Ignorar agro en exportaciones (palabras clave para excluir)
AGRO_KEYWORDS = ['agricultura', 'cría', 'explotación de animales', 'pesca', 'caza', 'aprovechamiento forestal', 'agro', 'primari']

def get_val(df, ind):
    row = df[df['Indicador'] == ind]
    if row.empty:
        row = df[df['Indicador'].str.contains(ind[:20], na=False, regex=False)]
    return row['Valor'].sum() if not row.empty else 0.0

def generar_reporte():
    # Rutas basadas en el código fuente
    ruta_pib = "data/intermediate/pib_entidad.csv"
    ruta_exp = "data/intermediate/exportaciones_entidad.csv"
    
    if not os.path.exists(ruta_pib) or not os.path.exists(ruta_exp):
        print("Error: No se encontraron los archivos CSV. Asegúrate de ejecutar el script en la raíz del proyecto.")
        return

    df_pib = pd.read_csv(ruta_pib)
    df_exp = pd.read_csv(ruta_exp)

    # Filtros temporales (Regla 6)
    df_pib_2024 = df_pib[df_pib['Periodo'] == 2024]
    
    df_exp['Year'] = df_exp['Periodo'].astype(str).str[:4]
    df_exp['Quarter'] = df_exp['Periodo'].astype(str).str[-2:]
    df_exp_1t26 = df_exp[(df_exp['Year'] == '2026') & (df_exp['Quarter'].isin(['01', '1', 'Q1', '1T']))]

    for state_id, state_name in STATE_MAP.items():
        # Separador para fácil copiado
        print(f"ESTADO: {state_name.upper()}\n")
        
        # ==========================================
        # SECCIÓN PIB
        # ==========================================
        print("PIB:\n")
        df_pib_st = df_pib_2024[df_pib_2024['Estado_ID'] == state_id]
        
        pib_total_estado = get_val(df_pib_st, "Total Nacional")
        if pib_total_estado == 0: pib_total_estado = 1
        
        sectores_vals = []
        for sub in SUBSECTORES_VALIDOS_PIB:
            val = get_val(df_pib_st, sub)
            sectores_vals.append({'Sector': sub, 'Valor': val})
            
        df_top_pib = pd.DataFrame(sectores_vals).sort_values('Valor', ascending=False).head(3)
        
        for pib_idx, (_, row) in enumerate(df_top_pib.iterrows()):
            sector = row['Sector']
            valor_mmp = row['Valor'] / 1000
            pct_total = (row['Valor'] / pib_total_estado) * 100
            
            print(f"{pib_idx + 1}. {sector} | ${valor_mmp:,.0f} MMP ({pct_total:.1f}%)")
            
            # Regla 4: Desglose único para Manufacturas si está en el top 3
            if "manufactureras" in sector.lower() and row['Valor'] > 0:
                man_vals = []
                for act in MANUFACTURA_ACTS:
                    man_vals.append({'Act': act, 'Valor': get_val(df_pib_st, act)})
                
                df_top_man = pd.DataFrame(man_vals).sort_values('Valor', ascending=False).head(3)
                
                # Regla Estructura Idéntica (incluye el guion en todos los elementos)
                for idx, (_, m_row) in enumerate(df_top_man.iterrows()):
                    pct_man = (m_row['Valor'] / row['Valor']) * 100
                    print(f"- {m_row['Act']} | ({pct_man:.1f}% de manufactura)")
            print("")

        # ==========================================
        # SECCIÓN EXPORTACIONES
        # ==========================================
        print("Exportaciones:\n")
        df_exp_st = df_exp_1t26[df_exp_1t26['Estado_ID'].astype(str).str.zfill(2) == str(state_id).zfill(2)]
        
        # Reproducimos el denominador del dashboard sumando los sectores reales en lugar de la fila "Total"
        total_exp_estado = df_exp_st[df_exp_st['Sector'] != 'Total']['Valor'].sum()
        if total_exp_estado == 0: total_exp_estado = 1
        
        # Ignorar total, sectores agro (Regla 2) y "No especificado"
        df_exp_st_filt = df_exp_st[df_exp_st['Sector'] != 'Total']
        df_exp_st_filt = df_exp_st_filt[~df_exp_st_filt['Sector'].str.lower().str.contains('|'.join(AGRO_KEYWORDS))]
        df_exp_st_filt = df_exp_st_filt[~df_exp_st_filt['Sector'].str.contains('No especificado', case=False, na=False)]
        
        df_top_exp = df_exp_st_filt.groupby('Sector')['Valor'].sum().reset_index().sort_values('Valor', ascending=False)
        
        # Filtramos para omitir todo lo que sea exactamente igual a 0
        df_top_exp = df_top_exp[df_top_exp['Valor'] > 0].head(3)
        
        for exp_idx, (_, row) in enumerate(df_top_exp.iterrows()):
            val_mdd = row['Valor'] / 1000
            pct_exp = (row['Valor'] / total_exp_estado) * 100
            
            # Regla para valores menores a 1 MDD pero mayores a 0
            if val_mdd < 1:
                str_val = "< 1"
            else:
                str_val = f"{val_mdd:,.0f}"
                
            print(f"{exp_idx + 1}. {row['Sector']} | ${str_val} MDD ({pct_exp:.1f}%)\n")
            
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    generar_reporte()
