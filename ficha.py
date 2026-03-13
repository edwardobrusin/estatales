import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import textwrap

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Ficha Técnica Estatal",
    page_icon="🇲🇽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
<style>
    /* Diseño de menú estilo "Tabs" para los botones del Sidebar */
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 0px 6px 6px 0px; /* Borde plano a la izquierda, curvo a la derecha */
        border: none;
        border-left: 4px solid transparent; /* Borde invisible por defecto */
        justify-content: flex-start; /* Texto alineado a la izquierda */
        text-align: left;
        padding: 10px 15px;
        background-color: transparent;
        box-shadow: none;
        margin-bottom: 2px;
        transition: all 0.2s ease;
    }

    /* Efecto al pasar el mouse por los estados inactivos */
    [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
        background-color: rgba(150, 150, 150, 0.1);
        border-left: 4px solid #cccccc;
    }

    /* Estilo exacto de tu imagen para el estado ACTIVO */
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background-color: #ffffff !important;
        color: #0f172a !important; /* Texto oscuro */
        border-left: 4px solid #0056b3 !important; /* Borde azul a la izquierda */
        font-weight: 800 !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1) !important;
    }
    .metric-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        height: 100%;
    }
    .metric-title {
        color: #555;
        font-size: 0.9rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .metric-rank {
        background-color: #007bff;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        vertical-align: middle;
        margin-left: 5px;
    }
    .metric-value {
        color: #212529;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 5px 0;
    }
    .metric-delta-pos { color: #198754; font-weight: 600; font-size: 0.9rem; }
    .metric-delta-neg { color: #dc3545; font-weight: 600; font-size: 0.9rem; }
    .metric-sub { color: #6c757d; font-size: 0.85rem; }
    hr { margin: 10px 0; border-top: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CATÁLOGOS Y MAPEOS
# ==========================================
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
NAME_TO_ID = {v: k for k, v in STATE_MAP.items()}

NAME_NORMALIZER = {
    'Coahuila de Zaragoza': 'Coahuila', 
    'Michoacán de Ocampo': 'Michoacán', 
    'Veracruz de Ignacio de la Llave': 'Veracruz', 
    'Estado de México': 'México',
    'Mexico': 'México'
}

# ==========================================
# 3. CARGA DE DATOS
# ==========================================
@st.cache_data
def load_data():
    path = os.path.join("data", "intermediate")
    raw = os.path.join("data", "raw")
    data = {}
    
    try:
        # Carga de CSVs
        data['pib'] = pd.read_csv(os.path.join(path, "pib_entidad.csv"))
        data['export'] = pd.read_csv(os.path.join(path, "exportaciones_entidad.csv"))
        data['pob'] = pd.read_csv(os.path.join(path, "poblacion_edad.csv"))
        data['enoe'] = pd.read_csv(os.path.join(path, "enoe_indicadores.csv"))
        data['imss_sal'] = pd.read_csv(os.path.join(path, "salarios_imss.csv"))
        data['imss_pue'] = pd.read_csv(os.path.join(path, "puestos_imss.csv"))
        
        # IED (Totales y Detalle)
        data['ied_tot'] = pd.read_csv(os.path.join(path, "ied_totales.csv"))
        data['ied_det'] = pd.read_csv(os.path.join(path, "ied_top3_sectores.csv"))
        
        # EDUCACIÓN (Actualizado a 3 archivos)
        data['edu_tot'] = pd.read_csv(os.path.join(path, "educacion_totales.csv"))
        data['edu_mat'] = pd.read_csv(os.path.join(path, "educacion_top3_matricula.csv")) # Nuevo
        data['edu_egr'] = pd.read_csv(os.path.join(path, "educacion_top3_egresados.csv")) # Nuevo
        
        data['saic'] = pd.read_csv(os.path.join(path, "saic_productividad.csv"))
        data['imco_g'] = pd.read_csv(os.path.join(path, "imco_general_final.csv"))
        data['imco_d'] = pd.read_csv(os.path.join(path, "imco_desagregado_final.csv"))
        
        # Ratings
        rat_path = os.path.join(raw, "ratings_estatales.xlsx")
        if os.path.exists(rat_path):
            data['ratings'] = pd.read_excel(rat_path)
        else:
            data['ratings'] = pd.DataFrame()
        
        gob_path = os.path.join(raw, "gob_sedeco.xlsx")
        if os.path.exists(gob_path):
            data['gob_sedeco'] = pd.read_excel(gob_path)
        else:
            data['gob_sedeco'] = pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None
    return data

DATA = load_data()
if not DATA: st.stop()

# ==========================================
# 4. SIDEBAR
# ==========================================
st.sidebar.markdown("### Selecciona Entidad")

# 1. Inicializamos la memoria para guardar el estado seleccionado
if 'estado_seleccionado' not in st.session_state:
    st.session_state['estado_seleccionado'] = 'Aguascalientes'

# 2. Función que actualiza la memoria cuando haces clic
def cambiar_estado(nuevo_estado):
    st.session_state['estado_seleccionado'] = nuevo_estado

# 3. Creamos un botón tipo bloque para cada estado
for estado in list(STATE_MAP.values()):
    # Pintamos de azul (primary) el seleccionado, y gris (secondary) los demás
    btn_type = "primary" if st.session_state['estado_seleccionado'] == estado else "secondary"
    
    st.sidebar.button(
        label=estado, 
        key=f"btn_{estado}", 
        use_container_width=True, # Hace que el botón abarque todo el ancho (cuadro)
        type=btn_type, 
        on_click=cambiar_estado, 
        args=(estado,)
    )

# 4. Asignamos el estado elegido a las variables que usa el resto de tu código
selected_name = st.session_state['estado_seleccionado']
state_norm = NAME_NORMALIZER.get(selected_name, selected_name)
state_id = NAME_TO_ID.get(state_norm)
state_id_str = str(state_id).zfill(2)

st.title(f"Ficha Técnica: {selected_name}")
if 'gob_sedeco' in DATA and not DATA['gob_sedeco'].empty:
    df_gob = DATA['gob_sedeco']
    # Buscamos el estado asegurándonos de limpiar espacios en blanco
    info_estado = df_gob[df_gob['Estado'].astype(str).str.strip() == selected_name]
    
    if not info_estado.empty:
        gobernador = info_estado['Gobernador/a'].values[0]
        sedeco = info_estado['SEDECO'].values[0]
        partido = info_estado['Partido'].values[0]
        st.markdown(f"**Gobernador/a:** {gobernador} &nbsp;&nbsp;|&nbsp;&nbsp; **SEDECO:** {sedeco} &nbsp;&nbsp;|&nbsp;&nbsp; **Partido:** {partido}")

# --- NUEVA LEYENDA ---
st.markdown("<p style='text-align: left; color: #888; font-size: 0.85rem; margin-top: -5px; margin-bottom: -20px;'><i>MDP: Millones de Pesos &nbsp;|&nbsp; MDD: Millones de Dólares</i></p>", unsafe_allow_html=True)

# ==========================================
# 5. FUNCIONES LÓGICAS
# ==========================================

def format_mm_pesos(val_millones):
    return f"${val_millones:,.2f} <span style='font-size: 0.5em;'>MDP</span>"

def format_mm_usd(val_miles): 
    val = val_miles / 1000 
    return f"${val:,.2f} <span style='font-size: 0.5em;'>MDD</span>"

def format_mm_usd_ied(val_millones): 
    return f"${val_millones:,.2f} <span style='font-size: 0.5em;'>MDD</span>"

def render_card(title, val_str, rank, top1, part, growth, growth_nac):
    c_g = "metric-delta-pos" if growth >= 0 else "metric-delta-neg"
    i_g = "▲" if growth >= 0 else "▼"
    c_gn = "metric-delta-pos" if growth_nac >= 0 else "metric-delta-neg"
    i_gn = "▲" if growth_nac >= 0 else "▼"
    
    title_html = title.replace(" (", "<br>(")
    
    st.markdown(f"""
    <div class="metric-container">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px;">
            <div class="metric-title" style="margin-bottom: 0; line-height: 1.2;">{title_html}</div>
            <div class="metric-rank" style="margin-left: 10px; flex-shrink: 0;">#{rank}</div>
        </div>
        <div class="metric-sub" style="margin-bottom: 2px;">#1 {top1}</div>
        <div class="metric-value" style="margin: 2px 0;">{val_str}</div>
        <div class="metric-sub" style="margin-bottom: 2px;">Participación Nacional: <b>{part:.2f}%</b></div>
        <hr style="margin: 8px 0; border-top: 1px solid #eee;">
        <div class="metric-sub">
            <div style="margin-bottom: 3px;">Var. Estatal: <span class="{c_g}">{i_g} {growth:.2f}%</span></div>
            <div>Var. Nacional: <span class="{c_gn}">{i_gn} {growth_nac:.2f}%</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Métricas PIB ---
def get_pib_metrics(df, indicador, id_estado_int):
    df = df.copy()
    df['Estado_ID'] = pd.to_numeric(df['Estado_ID'], errors='coerce').fillna(-1).astype(int)
    df_ind = df[df['Indicador'] == indicador]
    if df_ind.empty: return None
    
    max_period = df_ind['Periodo'].max()
    prev_period = max_period - 1
    
    nac_curr = df_ind[(df_ind['Estado_ID'] == 0) & (df_ind['Periodo'] == max_period)]['Valor'].sum()
    nac_prev = df_ind[(df_ind['Estado_ID'] == 0) & (df_ind['Periodo'] == prev_period)]['Valor'].sum()
    
    est_curr = df_ind[(df_ind['Estado_ID'] == id_estado_int) & (df_ind['Periodo'] == max_period)]['Valor'].sum()
    est_prev = df_ind[(df_ind['Estado_ID'] == id_estado_int) & (df_ind['Periodo'] == prev_period)]['Valor'].sum()
    
    growth_est = ((est_curr - est_prev)/est_prev * 100) if est_prev > 0 else 0
    growth_nac = ((nac_curr - nac_prev)/nac_prev * 100) if nac_prev > 0 else 0
    part_nac = (est_curr / nac_curr * 100) if nac_curr > 0 else 0
    
    df_rank = df_ind[(df_ind['Periodo'] == max_period) & (df_ind['Estado_ID'] != 0)].copy()
    df_rank['Rank'] = df_rank['Valor'].rank(ascending=False)
    
    try:
        rank = int(df_rank[df_rank['Estado_ID'] == id_estado_int]['Rank'].values[0])
        top1_row = df_rank[df_rank['Rank'] == 1].iloc[0]
        top1_name = STATE_MAP.get(top1_row['Estado_ID'], "N/A")
    except: rank=0; top1_name="-"
        
    return est_curr, part_nac, growth_est, growth_nac, rank, top1_name, max_period

# --- Métricas Exportaciones ---
def get_export_metrics(df, id_estado_str):
    df['Year'] = df['Periodo'].astype(str).str[:4].astype(int)
    df['Quarter'] = df['Periodo'].astype(str).str[-2:]
    
    max_year = df['Year'].max()
    quarters_avail = df[df['Year'] == max_year]['Quarter'].unique()
    
    df_total = df[df['Sector'] == 'Total']
    
    est_curr = df_total[(df_total['Year'] == max_year) & (df_total['Estado_ID'].astype(str).str.zfill(2) == id_estado_str)]['Valor'].sum()
    est_prev = df_total[(df_total['Year'] == (max_year-1)) & (df_total['Estado_ID'].astype(str).str.zfill(2) == id_estado_str) & (df_total['Quarter'].isin(quarters_avail))]['Valor'].sum()
    
    nac_curr = df_total[df_total['Year'] == max_year]['Valor'].sum()
    nac_prev = df_total[(df_total['Year'] == (max_year-1)) & (df_total['Quarter'].isin(quarters_avail))]['Valor'].sum()
    
    growth_est = ((est_curr - est_prev)/est_prev * 100) if est_prev > 0 else 0
    growth_nac = ((nac_curr - nac_prev)/nac_prev * 100) if nac_prev > 0 else 0
    part_nac = (est_curr / nac_curr * 100) if nac_curr > 0 else 0
    
    df_agg = df_total[df_total['Year'] == max_year].groupby('Estado_ID')['Valor'].sum().reset_index()
    df_agg['Rank'] = df_agg['Valor'].rank(ascending=False)
    
    try:
        df_agg['ID_Str'] = df_agg['Estado_ID'].astype(str).str.zfill(2)
        rank = int(df_agg[df_agg['ID_Str'] == id_estado_str]['Rank'].values[0])
        top1_row = df_agg[df_agg['Rank'] == 1].iloc[0]
        top1_name = STATE_MAP.get(int(top1_row['Estado_ID']), "N/A")
    except: rank=0; top1_name="-"
    
    # Lógica para definir el texto del trimestre (Ej. "1T-3T 2025" o "1T 2025")
    num_trimestres = len(quarters_avail)
    if num_trimestres <= 1:
        trim_str = f"1T {max_year}"
    else:
        trim_str = f"1T-{num_trimestres}T {max_year}"
        
    return est_curr, part_nac, growth_est, growth_nac, rank, top1_name, trim_str

# --- Métricas IED (AGREGADO) ---
def get_ied_metrics(df_tot, state_norm):
    df_tot = df_tot.copy()
    df_tot['Estado_Norm'] = df_tot['Estado'].replace(NAME_NORMALIZER)
    
    try:
        max_year = int(df_tot['Anio'].max())
        max_trim = int(df_tot['Trimestre'].max())
        trim_str = f"{max_trim}T {max_year}"
    except:
        trim_str = "N/A"
    
    # 1. Agrupar por Estado para tener el Gran Total (suma de sectores)
    df_agg = df_tot.groupby('Estado_Norm')[['Inversion', 'Inversion_Anterior']].sum().reset_index()
    
    # 2. Calcular Ranking
    df_agg['Rank'] = df_agg['Inversion'].rank(ascending=False)
    
    # 3. Nacionales
    nac_curr = df_agg['Inversion'].sum()
    nac_prev = df_agg['Inversion_Anterior'].sum()
    growth_nac = ((nac_curr - nac_prev)/nac_prev * 100) if nac_prev > 0 else 0
    
    # 4. Estatal
    row = df_agg[df_agg['Estado_Norm'] == state_norm]
    if row.empty: return None
    
    est_curr = row['Inversion'].values[0]
    est_prev = row['Inversion_Anterior'].values[0]
    
    growth_est = ((est_curr - est_prev)/est_prev * 100) if est_prev > 0 else 0
    part_nac = (est_curr / nac_curr * 100) if nac_curr > 0 else 0
    
    rank = int(row['Rank'].values[0])
    top1 = df_agg.sort_values('Inversion', ascending=False).iloc[0]['Estado_Norm']
    
    return est_curr, part_nac, growth_est, growth_nac, rank, top1, trim_str

# ==========================================
# SECCIÓN 1: RESUMEN EJECUTIVO
# ==========================================
st.markdown("---")
st.header("1. Resumen Ejecutivo")
st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: PIB por Entidad Federativa (INEGI), Exportaciones por Entidad Federativa (INEGI) e Inversión Extranjera Directa (Secretaría de Economía)</div>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    res = get_pib_metrics(DATA['pib'], "Total Nacional", state_id)
    if res:
        v, p, g, gn, r, t1, yr = res
        render_card(f"PIB ({yr})", format_mm_pesos(v), r, t1, p, g, gn)
    else: st.warning("Sin datos PIB")

with col2:
    res = get_pib_metrics(DATA['pib'], "Industrias manufactureras", state_id)
    if res:
        v, p, g, gn, r, t1, yr = res
        render_card(f"PIB Manufactura ({yr})", format_mm_pesos(v), r, t1, p, g, gn)
    else: st.warning("Sin datos Manufactura")

with col3:
    res = get_export_metrics(DATA['export'], state_id_str)
    if res:
        v, p, g, gn, r, t1, trim_str = res
        render_card(f"Exportaciones ({trim_str})", format_mm_usd(v), r, t1, p, g, gn)
    else: st.warning("Sin datos Exportación")

with col4:
    res = get_ied_metrics(DATA['ied_tot'], state_norm)
    if res:
        v, p, g, gn, r, t1, trim_str = res
        render_card(f"IED ({trim_str})", format_mm_usd_ied(v), r, t1, p, g, gn)
    else: st.warning("Sin datos IED")

# ==========================================
# SECCIÓN 2: DETALLE IED (VERTICAL)
# ==========================================
st.markdown("---") # Línea divisoria agregada
try:
    trim_ied = int(DATA['ied_tot']['Trimestre'].max())
    anio_ied = int(DATA['ied_tot']['Anio'].max())
    texto_periodo_ied = f"({trim_ied}T {anio_ied})"
except:
    texto_periodo_ied = ""

# Cambiamos markdown por header y actualizamos el número
st.header(f"2. Inversión Extranjera Directa {texto_periodo_ied}")
st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: Inversión Extranjera Directa (Secretaría de Economía)</div>", unsafe_allow_html=True)
df_ied_det = DATA['ied_det']
df_ied_tot = DATA['ied_tot'] # Archivo con totales por sector

# Filtros por Estado
df_ied_st_det = df_ied_det[df_ied_det['Estado'].replace(NAME_NORMALIZER) == state_norm]
df_ied_st_tot = df_ied_tot[df_ied_tot['Estado'].replace(NAME_NORMALIZER) == state_norm]

if not df_ied_st_det.empty:
    def render_sector_block(sector_name, color_bar):
        # 1. Obtener Total del Sector
        row_tot = df_ied_st_tot[df_ied_st_tot['Sector'] == sector_name]
        total_sector_val = row_tot['Inversion'].sum() if not row_tot.empty else 0.0
        
        # 2. Obtener Actividades (Top) y filtrar las que son 0 o menores
        subset = df_ied_st_det[df_ied_st_det['Sector'] == sector_name].sort_values('Inversion', ascending=False)
        subset = subset[subset['Inversion'] > 0] # <--- NUEVO: FILTRO PARA OMITIR CEROS
        
        # Eliminamos sangrías en el HTML para evitar conflictos con Markdown
        html_head = f"""<div style="border-left: 5px solid {color_bar}; padding-left: 15px; margin-bottom: 20px; background-color: #f8f9fa; padding-top: 10px; padding-bottom: 10px; border-radius: 0 5px 5px 0;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<h5 style="margin:0; color:#333;">{sector_name}</h5>
<span style="font-size:0.9rem; font-weight:700; color:{color_bar}; background:white; padding:2px 8px; border-radius:4px; border:1px solid #ddd;">
Total: ${total_sector_val:,.2f} MDD
</span>
</div>
<hr style="margin:5px 0 10px 0; border-color:#e9ecef;">"""
        st.markdown(html_head, unsafe_allow_html=True)
        
        if not subset.empty:
            for _, r in subset.iterrows():
                html_row = f"""<div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px;">
<span style="font-weight: 500;">• {r['Actividad']}</span>
<span style="white-space: nowrap; font-weight:600;">
${r['Inversion']:,.2f} MDD
</span>
</div>"""
                st.markdown(html_row, unsafe_allow_html=True)
        else:
            st.caption("Sin inversión registrada.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    render_sector_block("Primaria", "#28a745")    # Verde
    render_sector_block("Secundaria", "#007bff")  # Azul
    render_sector_block("Terciaria", "#fd7e14")   # Naranja
    
    st.info("ℹ️ Nota: El monto de algunas actividades individuales puede superar al Total del Sector debido a que existen flujos negativos (desinversiones) en otras actividades que restan al acumulado total.")

else:
    st.info("No hay detalle de sectores de IED disponible.")

# ==========================================
# SECCIÓN 3: ESTRUCTURA ECONÓMICA
# ==========================================
st.markdown("---")

# --- PREPARACIÓN DE DATOS ---
df_pib = DATA['pib']
max_period = df_pib['Periodo'].max()

st.header(f"3. Estructura Económica (PIB {max_period})")
st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: PIB por Entidad Federativa (INEGI)</div>", unsafe_allow_html=True)

# 1. Datos Estatales (df_curr)
df_curr = df_pib[(df_pib['Estado_ID'] == state_id) & (df_pib['Periodo'] == max_period)].copy()

# 2. Datos Nacionales (df_nac) - Para calcular participaciones correctas
df_nac = df_pib[(df_pib['Estado_ID'] == 0) & (df_pib['Periodo'] == max_period)].copy()

# Definición de Jerarquías
HIERARCHY = {
    "Primario": {
        "Total": "Actividades Primarias",
        "Subsectores": ["Agricultura, cría y explotación de animales, aprovechamiento forestal, pesca y caza"],
        "Actividades": ["Agricultura", "Cría y explotación de animales", "Pesca, caza y captura", "Aprovechamiento forestal"]
    },
    "Secundario": {
        "Total": "Actividades Secundarias",
        "Subsectores": ["Minería", "Generación, transmisión y distribución de energía eléctrica, agua y gas", "Construcción", "Industrias manufactureras"],
        "Manufactura_Actividades": ["Industria alimentaria", "Bebidas y tabaco", "Insumos, acabados y productos textiles", "Prendas de vestir y productos de cuero y piel", "Industria de la madera", "Industria del papel", "Productos derivados del petróleo y carbón, química, plástico y hule", "Productos a base de minerales no metálicos", "Metálicas básicas y productos metálicos", "Maquinaria y equipo, computación, electrónicos y accesorios", "Muebles, colchones y persianas", "Otras industrias manufactureras"]
    },
    "Terciario": {
        "Total": "Actividades Terciarias",
        "Subsectores": ["Comercio al por mayor", "Comercio al por menor", "Transportes, correos y almacenamiento", "Información en medios masivos", "Servicios financieros y de seguros", "Servicios inmobiliarios y de alquiler de bienes", "Servicios profesionales, científicos y técnicos", "Corporativos", "Servicios de apoyo a los negocios y manejo de residuos", "Servicios educativos", "Servicios de salud y de asistencia social", "Servicios de esparcimiento culturales y deportivos", "Servicios de alojamiento temporal y de preparación de alimentos y bebidas", "Otros servicios excepto actividades gubernamentales", "Actividades legislativas, gubernamentales"]
    }
}

# Funciones Helper
def get_val(df, indicador_name):
    # Busca coincidencia exacta o contiene
    row = df[df['Indicador'] == indicador_name]
    if row.empty:
        row = df[df['Indicador'].str.contains(indicador_name[:20], na=False, regex=False)]
    return row['Valor'].sum() if not row.empty else 0.0

def get_ranked_list(lista_indicadores, total_compare, top_n=None):
    res = []
    for ind in lista_indicadores:
        v = get_val(df_curr, ind)
        s = (v / total_compare * 100) if total_compare > 0 else 0.0
        res.append({'Nombre': ind, 'Valor': v, 'Share': s})
    df_res = pd.DataFrame(res).sort_values('Valor', ascending=False)
    if top_n: return df_res.head(top_n)
    return df_res

# --- CÁLCULO TOTAL PIB ESTATAL (MODIFICADO) ---
# Usamos "Total Nacional" que corresponde al PIB Total de la entidad en la base de datos
pib_estatal_total = get_val(df_curr, "Total Nacional") 

# Valores absolutos de los sectores
val_prim_total = get_val(df_curr, HIERARCHY["Primario"]["Total"])
val_sec_total = get_val(df_curr, HIERARCHY["Secundario"]["Total"])
val_ter_total = get_val(df_curr, HIERARCHY["Terciario"]["Total"])

# Cálculo de Impuestos (Diferencia)
val_impuestos = pib_estatal_total - (val_prim_total + val_sec_total + val_ter_total)
pct_impuestos = (val_impuestos / pib_estatal_total * 100) if pib_estatal_total > 0 else 0

# --- RENDERIZADO ---
c1, c2, c3 = st.columns(3)

# Datos de empleo (ENOE) para usar en las tarjetas
df_enoe_est = DATA['enoe'][DATA['enoe']['Estado'].replace(NAME_NORMALIZER) == state_norm]
tot_emp = 0
if not df_enoe_est.empty:
    tot_emp = (df_enoe_est['Sector Primario'] + df_enoe_est['Sector Secundario'] + df_enoe_est['Sector Terciario'] + df_enoe_est['No especificado']).values[0]

# --- 1. PRIMARIO ---
with c1:
    meta = HIERARCHY["Primario"]
    val_est = get_val(df_curr, meta["Total"])
    val_nac_sec = get_val(df_nac, meta["Total"]) # Valor Nacional del mismo sector
    
    # Participación Nacional
    part_nac = (val_est / val_nac_sec * 100) if val_nac_sec > 0 else 0
    # Participación Estatal (Base: PIB Estatal Total)
    part_estatal = (val_est / pib_estatal_total * 100) if pib_estatal_total > 0 else 0
    
    # Empleo
    emp_part = 0
    if not df_enoe_est.empty and tot_emp > 0:
        emp_part = (df_enoe_est['Sector Primario'].values[0] / tot_emp * 100)

    st.markdown(f"""
    <div style="border-left: 4px solid #28a745; padding-left: 12px; margin-bottom: 15px;">
        <div style="font-weight:700; color:#555;">SECTOR PRIMARIO</div>
        <div style="font-size:1.4rem; font-weight:800;">{format_mm_pesos(val_est)}</div>
        <div style="font-size:0.85rem;">🇲🇽 Part. Nacional: <b>{part_nac:.2f}%</b></div>
        <div style="font-size:0.85rem;">📍 Part. Estatal: <b>{part_estatal:.2f}%</b></div>
        <div style="font-size:0.85rem;">👷 <b>{emp_part:.2f}%</b> del Empleo Estatal</div>
    </div>
    """, unsafe_allow_html=True)

    sub_df = get_ranked_list(meta["Subsectores"], val_est)
    act_df = get_ranked_list(meta["Actividades"], val_est, top_n=3)
    
    st.markdown("**Estructura:**")
    # Bullets para Primario (Un solo subsector)
    for _, r in sub_df.iterrows():
        st.markdown(f"""
        <div style="margin-bottom:8px;">
            <div style="font-weight:600; font-size:0.95rem;">• {r['Nombre']}</div>
            <div style="color:#666; font-size:0.85rem; margin-left:15px;">${r['Valor']/1000:,.2f} MM ({r['Share']:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
        for _, act in act_df.iterrows():
            st.markdown(f"""
            <div style="margin-left: 20px; font-size: 0.85rem; border-left: 2px solid #ddd; padding-left: 8px; margin-bottom: 4px;">
                <span>{act['Nombre']}</span> <br> <span style="font-weight:700; color:#28a745;">{act['Share']:.1f}%</span> del sector
            </div>
            """, unsafe_allow_html=True)

# --- 2. SECUNDARIO ---
with c2:
    meta = HIERARCHY["Secundario"]
    val_est = get_val(df_curr, meta["Total"])
    val_nac_sec = get_val(df_nac, meta["Total"])
    part_nac = (val_est / val_nac_sec * 100) if val_nac_sec > 0 else 0
    # Participación Estatal
    part_estatal = (val_est / pib_estatal_total * 100) if pib_estatal_total > 0 else 0
    
    emp_part = 0
    if not df_enoe_est.empty and tot_emp > 0:
        emp_part = (df_enoe_est['Sector Secundario'].values[0] / tot_emp * 100)

    st.markdown(f"""
    <div style="border-left: 4px solid #007bff; padding-left: 12px; margin-bottom: 15px;">
        <div style="font-weight:700; color:#555;">SECTOR SECUNDARIO</div>
        <div style="font-size:1.4rem; font-weight:800;">{format_mm_pesos(val_est)}</div>
        <div style="font-size:0.85rem;">🇲🇽 Part. Nacional: <b>{part_nac:.2f}%</b></div>
        <div style="font-size:0.85rem;">📍 Part. Estatal: <b>{part_estatal:.2f}%</b></div>
        <div style="font-size:0.85rem;">👷 <b>{emp_part:.2f}%</b> del Empleo Estatal</div>
    </div>
    """, unsafe_allow_html=True)

    sub_df = get_ranked_list(meta["Subsectores"], val_est, top_n=3)
    st.markdown("**Principales Subsectores:**")
    
    # Números para Secundario
    for i, (_, r) in enumerate(sub_df.iterrows()):
        is_manuf = "manufactureras" in r['Nombre'].lower()
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <div style="font-weight:600; font-size:0.95rem;">{i+1}. {r['Nombre']}</div>
            <div style="color:#666; font-size:0.85rem; margin-left:15px;">${r['Valor']/1000:,.2f} MM ({r['Share']:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
        if is_manuf:
            manuf_acts = get_ranked_list(meta["Manufactura_Actividades"], r['Valor'], top_n=3)
            for _, m_act in manuf_acts.iterrows():
                st.markdown(f"""
                <div style="margin-left: 20px; font-size: 0.85rem; border-left: 2px solid #aecbeb; padding-left: 8px; margin-bottom: 4px;">
                    <span>{m_act['Nombre']}</span> <br> <span style="font-weight:700; color:#007bff;">{m_act['Share']:.1f}%</span> de manufactura
                </div>
                """, unsafe_allow_html=True)

# --- 3. TERCIARIO ---
with c3:
    meta = HIERARCHY["Terciario"]
    val_est = get_val(df_curr, meta["Total"])
    val_nac_sec = get_val(df_nac, meta["Total"])
    part_nac = (val_est / val_nac_sec * 100) if val_nac_sec > 0 else 0
    # Participación Estatal
    part_estatal = (val_est / pib_estatal_total * 100) if pib_estatal_total > 0 else 0
    
    emp_part = 0
    if not df_enoe_est.empty and tot_emp > 0:
        emp_part = (df_enoe_est['Sector Terciario'].values[0] / tot_emp * 100)

    st.markdown(f"""
    <div style="border-left: 4px solid #fd7e14; padding-left: 12px; margin-bottom: 15px;">
        <div style="font-weight:700; color:#555;">SECTOR TERCIARIO</div>
        <div style="font-size:1.4rem; font-weight:800;">{format_mm_pesos(val_est)}</div>
        <div style="font-size:0.85rem;">🇲🇽 Part. Nacional: <b>{part_nac:.2f}%</b></div>
        <div style="font-size:0.85rem;">📍 Part. Estatal: <b>{part_estatal:.2f}%</b></div>
        <div style="font-size:0.85rem;">👷 <b>{emp_part:.2f}%</b> del Empleo Estatal</div>
    </div>
    """, unsafe_allow_html=True)

    sub_df = get_ranked_list(meta["Subsectores"], val_est, top_n=3)
    st.markdown("**Principales Subsectores:**")
    
    # Números para Terciario
    for i, (_, r) in enumerate(sub_df.iterrows()):
        display_name = r['Nombre'][:37] + "..." if len(r['Nombre']) > 40 else r['Nombre']
        st.markdown(f"""
        <div style="margin-bottom:8px;">
            <div style="font-weight:600; font-size:0.95rem;">{i+1}. {display_name}</div>
            <div style="color:#666; font-size:0.85rem; margin-left:15px;">${r['Valor']/1000:,.2f} MM ({r['Share']:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

# --- NOTA DE IMPUESTOS ---
st.info(f"ℹ️ **Nota:** La suma del PIB sectorial no equivale al total, pues no considera impuestos, cuyo valor de **{val_impuestos/1000:.2f}** MMP representa el **{pct_impuestos:.2f}%** de la participación estatal.")

# ==========================================
# SECCIÓN 4: POBLACIÓN
# ==========================================
st.markdown("---")
try:
    anio_enoe = DATA['enoe']['Anio'].iloc[0]
    # Convierte "trim3" a "3T"
    trim_str = str(DATA['enoe']['Trimestre'].iloc[0]).replace('trim', '')
    periodo_enoe = f"{trim_str}T {anio_enoe}"
except:
    periodo_enoe = ""

try:
    periodo_pob = DATA['pob']['Periodo'].max()
except:
    periodo_pob = ""
st.header("4. Demografía y Mercado Laboral")
st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: ENOE (INEGI), CPV (INEGI), Puestos de Trabajo (IMSS) y Cifras de Salario (IMSS)</div>", unsafe_allow_html=True)

# Función auxiliar para renderizar métricas con el estilo solicitado
def render_custom_metric(label, value, sub_text, color="#212529"):
    st.markdown(f"""
    <div style="background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin-bottom: 10px; height: 100%;">
        <div style="color: #666; font-size: 0.85rem; text-transform: uppercase; font-weight: 600;">{label}</div>
        <div style="color: {color}; font-size: 1.8rem; font-weight: 800; margin: 5px 0;">{value}</div>
        <div style="color: #888; font-size: 0.8rem;">{sub_text}</div>
    </div>
    """, unsafe_allow_html=True)

# Layout general: Izquierda (Métricas), Derecha (Pirámide)
col_metrics, col_chart = st.columns([1, 1])

# --- PREPARACIÓN DE DATOS ---
# 1. Filtrar registros Estatal y Nacional
df_enoe_est = DATA['enoe'][DATA['enoe']['Estado'].replace(NAME_NORMALIZER) == state_norm]
df_enoe_nac = DATA['enoe'][DATA['enoe']['Estado'] == 'Nacional']

if not df_enoe_est.empty and not df_enoe_nac.empty:
    rec_est = df_enoe_est.iloc[0]
    rec_nac = df_enoe_nac.iloc[0]
    
    # ---------------------------------------------------------
    # DATOS ESTATALES
    # ---------------------------------------------------------
    est_pob = rec_est['Poblacion Total']
    est_pea = rec_est['PEA']
    est_des = rec_est['Desocupada']
    
    # Tasas Estatales
    t_des_est = (est_des / est_pea * 100) if est_pea > 0 else 0
    t_inf_est = rec_est['Informalidad TIL1']
    
    # Desempleo Superior (Estatal)
    des_sup_abs = rec_est.get('Educacion Sup', 0)
    t_des_sup = (des_sup_abs / est_des * 100) if est_des > 0 else 0
    
    # Edad Promedio (Estatal)
    edad_prom_est = rec_est.get('Edad Promedio PEA', 0) 

    # ---------------------------------------------------------
    # DATOS NACIONALES (Extraídos del registro 'Nacional')
    # ---------------------------------------------------------
    nac_pob = rec_nac['Poblacion Total']
    nac_pea = rec_nac['PEA']
    nac_des = rec_nac['Desocupada']
    nac_des_sup_abs = rec_nac.get('Educacion Sup', 0)
    
    # Tasas Nacionales (Calculadas con los datos del registro Nacional)
    t_des_sup_nac = (nac_des_sup_abs / nac_des * 100) if nac_des > 0 else 0
    t_des_nac = (nac_des / nac_pea * 100) if nac_pea > 0 else 0
    t_inf_nac = rec_nac['Informalidad TIL1'] # Dato directo
    edad_prom_nac = rec_nac.get('Edad Promedio PEA', 0) # Dato directo

    # --- LÓGICA DE COLORES ---
    # Rojo (#dc3545) si es mayor al nacional, Verde (#28a745) si es menor.
    color_des = "#dc3545" if t_des_est > t_des_nac else "#28a745"
    color_inf = "#dc3545" if t_inf_est > t_inf_nac else "#28a745"
    color_des_sup = "#dc3545" if t_des_sup > t_des_sup_nac else "#28a745"

    # --- RENDERIZADO DE MÉTRICAS (6 Cuadros) ---
    with col_metrics:
        st.markdown(f"<div style='text-align: center; color: #FFF; font-weight: 700; margin-bottom: 15px;'>Periodo: {periodo_enoe}</div>", unsafe_allow_html=True)
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            part_pob = (est_pob/nac_pob*100) if nac_pob > 0 else 0
            render_custom_metric(
                "Población Total", 
                f"{est_pob:,.0f}", 
                f"{part_pob:.2f}% del Nacional"
            )
        with r1c2:
            part_pea = (est_pea/nac_pea*100) if nac_pea > 0 else 0
            render_custom_metric(
                "PEA", 
                f"{est_pea:,.0f}", 
                f"{part_pea:.2f}% del Nacional"
            )
        
        # Fila 2: Tasas (Con Color en el Valor Principal)
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            render_custom_metric(
                "Tasa Desocupación", 
                f"{t_des_est:.2f}%", 
                f"Nacional: {t_des_nac:.2f}%", # Texto gris simple
                color=color_des 
            )
        with r2c2:
            render_custom_metric(
                "Tasa Informalidad", 
                f"{t_inf_est:.2f}%", 
                f"Nacional: {t_inf_nac:.2f}%", # Texto gris simple
                color=color_inf
            )
        
        # Fila 3: Desempleo Superior y Edad Promedio
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            render_custom_metric(
                "Desempleo Nivel Superior",         # 1. Nombre corregido
                f"{t_des_sup:.1f}%", 
                f"Nacional: {t_des_sup_nac:.1f}%",  # 2. Dato nacional comparativo
                color=color_des_sup                 # 3. Color dinámico (Rojo/Verde)
            )
        with r3c2:
            render_custom_metric(
                "Edad Promedio PEA", 
                f"{edad_prom_est:.1f} años", 
                f"Nacional: {edad_prom_nac:.1f} años"
            )

elif df_enoe_est.empty:
    st.warning(f"No se encontraron datos ENOE para la entidad: {state_norm}")
elif df_enoe_nac.empty:
    st.warning("No se encontró el registro 'Nacional' en los datos ENOE.")

# --- RENDERIZADO DE PIRÁMIDE POBLACIONAL ---
with col_chart:
    df_pob = DATA['pob']
    df_st = df_pob[df_pob['Estado_ID'].astype(int) == state_id].copy()
    
    if not df_st.empty:
        # Extraemos el rango base sin el género para evitar problemas de matching
        df_st['Rango_Exacto'] = df_st['Indicador'].str.replace(r' \(Hombres\)', '', regex=True).str.replace(r' \(Mujeres\)', '', regex=True)
        
        # Helper con lógica de exactitud para evitar cruces en nombres similares (ej. 4 y 40)
        def map_age(rango):
            if rango in ['0 a 4 años', '5 a 9 años', '10 a 14 años']: return '0 a 14 años'
            if rango in ['15 a 19 años', '20 a 24 años']: return '15 a 24 años'
            if rango in ['25 a 29 años', '30 a 34 años']: return '25 a 34 años'
            if rango in ['35 a 39 años', '40 a 44 años']: return '35 a 44 años'
            if rango in ['45 a 49 años', '50 a 54 años']: return '45 a 54 años'
            if rango in ['55 a 59 años', '60 a 64 años']: return '55 a 64 años'
            if rango in ['65 a 69 años', '70 a 74 años']: return '65 a 74 años'
            return '75 años y más'
        
        df_st['Rango'] = df_st['Rango_Exacto'].apply(map_age)
        df_st['Sexo'] = df_st['Indicador'].apply(lambda x: 'Hombres' if '(Hombres)' in x else 'Mujeres')
        
        # Orden correcto de categorías para Plotly
        category_order = [
            '0 a 14 años', '15 a 24 años', '25 a 34 años', 
            '35 a 44 años', '45 a 54 años', '55 a 64 años', 
            '65 a 74 años', '75 años y más'
        ]
        
        # Agrupar
        grp = df_st.groupby(['Rango', 'Sexo'])['Valor'].sum().reset_index()
        total_pob_state = grp['Valor'].sum()
        
        # Cálculos para gráfica
        grp['Valor_Plot'] = grp.apply(lambda x: -x['Valor'] if x['Sexo']=='Hombres' else x['Valor'], axis=1)
        grp['Porcentaje_Real'] = (grp['Valor'] / total_pob_state) * 100
        
        # Etiqueta de texto visible: "Valor (X%)"
        grp['Label_Text'] = grp.apply(lambda x: f"{x['Valor']/1000:.1f}k<br>({x['Porcentaje_Real']:.1f}%)", axis=1)

        fig = go.Figure()
        
        # Serie Hombres
        df_h = grp[grp['Sexo']=='Hombres']
        fig.add_trace(go.Bar(
            y=df_h['Rango'], 
            x=df_h['Valor_Plot'], 
            name='Hombres', 
            orientation='h', 
            marker_color='#007bff',
            text=df_h['Label_Text'],      # Texto visible
            textposition='inside',        # Posición dentro de la barra
            insidetextanchor='middle',
            customdata=df_h[['Valor', 'Porcentaje_Real']],
            hovertemplate="<b>Hombres</b><br>Población: %{customdata[0]:,.0f}<br>Share: %{customdata[1]:.2f}%<extra></extra>"
        ))
        
        # Serie Mujeres
        df_m = grp[grp['Sexo']=='Mujeres']
        fig.add_trace(go.Bar(
            y=df_m['Rango'], 
            x=df_m['Valor_Plot'], 
            name='Mujeres', 
            orientation='h', 
            marker_color='#28a745',
            text=df_m['Label_Text'],      # Texto visible
            textposition='inside',        # Posición dentro de la barra
            insidetextanchor='middle',
            customdata=df_m[['Valor', 'Porcentaje_Real']],
            hovertemplate="<b>Mujeres</b><br>Población: %{customdata[0]:,.0f}<br>Share: %{customdata[1]:.2f}%<extra></extra>"
        ))
        
        fig.update_layout(
            title=f"Pirámide Poblacional ({periodo_pob})", 
            barmode='overlay', 
            bargap=0.1, 
            yaxis={'categoryorder':'array', 'categoryarray': category_order}, 
            xaxis={'showticklabels':False, 'title': '% respecto al total poblacional'},
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            uniformtext_minsize=8, 
            uniformtext_mode='hide',
            height=450,  # <-- Altura forzada para que coincida con las 3 filas de tarjetas
            margin=dict(t=50, b=30, l=0, r=0)  # <-- Reducción de márgenes en blanco
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4.5 GRÁFICAS HISTÓRICAS (IMSS)
# ==========================================
st.markdown("<br>", unsafe_allow_html=True) # Espacio para separar de la pirámide y métricas
col_hist_izq, col_hist_der = st.columns(2)

with col_hist_izq:
    # --- Gráfica Histórica Puestos IMSS ---
    import plotly.graph_objects as go
    
    df_pue = DATA['imss_pue'].copy()
    col_pue = next((c for c in df_pue.columns if NAME_NORMALIZER.get(c, c) == state_norm), None)
    
    # 1. ESPÍA A SALARIOS: Calculamos cuántas líneas usará la gráfica de salarios
    df_sal_temp = DATA['imss_sal'].copy()
    col_sal_temp = next((c for c in df_sal_temp.columns if NAME_NORMALIZER.get(c, c) == state_norm), None)
    num_lineas_target = 6 
    
    if col_sal_temp:
        df_sal_temp[col_sal_temp] = pd.to_numeric(df_sal_temp[col_sal_temp].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('$', '', regex=False), errors='coerce')
        df_sal_temp[['Mes_Str', 'Año']] = df_sal_temp['Fecha'].str.split(' ', expand=True)
        df_sal_temp['Date'] = pd.to_datetime(df_sal_temp['Año'] + '-' + df_sal_temp['Mes_Str'].str.lower().str.strip().map({'enero':1, 'febrero':2, 'marzo':3, 'abril':4, 'mayo':5, 'junio':6, 'julio':7, 'agosto':8, 'septiembre':9, 'octubre':10, 'noviembre':11, 'diciembre':12}).astype(str).str.zfill(2) + '-01')
        df_sal_temp = df_sal_temp[df_sal_temp['Date'].dt.year >= 2000]
        if not df_sal_temp.empty:
            min_s = df_sal_temp[col_sal_temp].min()
            max_s = df_sal_temp[col_sal_temp].max()
            y_min_s = (min_s // 100) * 100
            y_max_s = ((max_s // 100) + 1) * 100
            num_lineas_target = len(range(int(y_min_s), int(y_max_s) + 1, 100))
    
    if col_pue:
        df_pue[col_pue] = pd.to_numeric(df_pue[col_pue].astype(str).str.replace(',', '').str.replace(' ', ''), errors='coerce')
        meses_map = {'enero':1, 'febrero':2, 'marzo':3, 'abril':4, 'mayo':5, 'junio':6, 'julio':7, 'agosto':8, 'septiembre':9, 'octubre':10, 'noviembre':11, 'diciembre':12}
        df_pue['Mes_Num'] = df_pue['Mes'].str.lower().str.strip().map(meses_map)
        df_pue['Date'] = pd.to_datetime(df_pue['Año'].astype(str) + '-' + df_pue['Mes_Num'].astype(str).str.zfill(2) + '-01')
        df_pue = df_pue[df_pue['Año'] >= 2000].sort_values('Date').reset_index(drop=True)
        
        min_pue = df_pue[col_pue].min()
        max_pue = df_pue[col_pue].max()
        
        # --- ALGORITMO MEJORADO: Saltos de 10k en 10k hasta 500k ---
        allowed_steps = [i * 10000 for i in range(1, 51)] + [i * 100000 for i in range(6, 51)]
        best_step = allowed_steps[0]
        best_diff = float('inf')
        
        for S in allowed_steps:
            temp_min = (min_pue // S) * S
            temp_max = ((max_pue // S) + 1) * S
            lines_count = int((temp_max - temp_min) / S) + 1
            diff = abs(lines_count - num_lineas_target)
            if diff < best_diff:
                best_diff = diff
                best_step = S
                
        y_min_pue = (min_pue // best_step) * best_step
        y_max_pue = ((max_pue // best_step) + 1) * best_step
        hitos_pue = list(range(int(y_min_pue), int(y_max_pue) + 1, best_step))
        
        val_curr = df_pue[col_pue].iloc[-1]
        val_prev_m = df_pue[col_pue].iloc[-2] if len(df_pue) > 1 else val_curr
        val_prev_y = df_pue[col_pue].iloc[-13] if len(df_pue) > 12 else val_curr
        var_m = (val_curr - val_prev_m) / val_prev_m * 100 if val_prev_m else 0
        var_y = (val_curr - val_prev_y) / val_prev_y * 100 if val_prev_y else 0
        fecha_str = f"{df_pue['Mes'].iloc[-1].capitalize()} {df_pue['Año'].iloc[-1]}"
        
        # --- NUEVO: RANKING PUESTOS ---
        excluir_pue = ['Año', 'Mes', 'Date', 'Mes_Num', 'Nacional', 'Total', '(Todo)']
        state_cols_pue = [c for c in df_pue.columns if c not in excluir_pue]
        last_row_pue = df_pue.iloc[-1][state_cols_pue].astype(str).str.replace(',', '').str.replace(' ', '')
        last_row_pue = pd.to_numeric(last_row_pue, errors='coerce')
        
        rk_pue = int(last_row_pue.rank(ascending=False, method='min')[col_pue])
        top1_pue = last_row_pue.idxmax()
        rank_html_pue = f"<br>Rank: <b>#{rk_pue}</b>" if rk_pue == 1 else f"<br>Rank: <b>#{rk_pue}</b> <span style='font-size:11px; color:#666;'>(1º {top1_pue})</span>"
        
        fig_pue = px.line(df_pue, x='Date', y=col_pue)
        fig_pue.update_traces(line_color='#007bff', line_width=2.5)
        
        valor_inicial_pue = df_pue[col_pue].iloc[0]
        for hito in hitos_pue:
            # Forzar dibujo de línea horizontal de extremo a extremo
            fig_pue.add_hline(y=hito, line_color='rgba(255,255,255,0.2)', line_width=1, layer='below')
            
            if valor_inicial_pue < hito: 
                cruce = df_pue[df_pue[col_pue] >= hito]
                if not cruce.empty:
                    primer_cruce = cruce.iloc[0]
                    texto_etiqueta = f"{primer_cruce['Mes'][:3].capitalize()} {primer_cruce['Año']}"
                    
                    fig_pue.add_trace(go.Scatter(
                        x=[primer_cruce['Date']], y=[primer_cruce[col_pue]], mode='markers+text',
                        marker=dict(color='white', size=9, line=dict(color='#007bff', width=2)),
                        text=[texto_etiqueta], textposition="top left",
                        textfont=dict(color="#007bff", size=11, weight="bold"),
                        showlegend=False, hoverinfo='skip',
                        cliponaxis=False 
                    ))
        
        ficha_pue_html = f"<b>{fecha_str}</b>{rank_html_pue}<br><span style='font-size:16px;'><b>{val_curr:,.0f}</b></span> puestos<br>Var Mensual: <span style='color:{'#28a745' if var_m >=0 else '#dc3545'}'>{var_m:+.2f}%</span><br>Var Anual: <span style='color:{'#28a745' if var_y >=0 else '#dc3545'}'>{var_y:+.2f}%</span>"
        fig_pue.add_annotation(
            x=0.02, y=0.95, xref='paper', yref='paper', text=ficha_pue_html, showarrow=False, align='left', 
            bgcolor='rgba(255, 255, 255, 0.95)', bordercolor='#007bff', borderwidth=2, borderpad=8, font=dict(color='black', size=12)
        )

        fig_pue.update_layout(
            title=dict(text="PUESTOS DE TRABAJO (IMSS)", font=dict(color='white', size=14), x=0.0),
            xaxis_title="", yaxis_title="", height=450, margin=dict(t=50, b=20, l=10, r=10),
            xaxis=dict(
                showticklabels=True, tickformat="%Y", gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#ccc'),
                showline=False # Apagamos líneas de borde inferior nativas
            ),
            yaxis=dict(
                range=[y_min_pue, y_max_pue], autorange=False, 
                tickmode='array', tickvals=hitos_pue, 
                showgrid=False, # --- Apagamos el grid nativo porque usamos add_hline ---
                tickformat=",.0f", tickfont=dict(color='#ccc'),
                showline=False, zeroline=False # --- Cero bordes laterales ---
            ),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pue, use_container_width=True)
    else:
        st.info("Datos históricos de puestos no disponibles.")

with col_hist_der:
    # --- Gráfica Histórica Salarios IMSS ---
    df_sal = DATA['imss_sal'].copy()
    col_sal = next((c for c in df_sal.columns if NAME_NORMALIZER.get(c, c) == state_norm), None)
    
    if col_sal:
        df_sal[col_sal] = pd.to_numeric(df_sal[col_sal].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('$', '', regex=False), errors='coerce')
        df_sal[['Mes_Str', 'Año']] = df_sal['Fecha'].str.split(' ', expand=True)
        meses_map = {'enero':1, 'febrero':2, 'marzo':3, 'abril':4, 'mayo':5, 'junio':6, 'julio':7, 'agosto':8, 'septiembre':9, 'octubre':10, 'noviembre':11, 'diciembre':12}
        df_sal['Mes_Num'] = df_sal['Mes_Str'].str.lower().str.strip().map(meses_map)
        df_sal['Date'] = pd.to_datetime(df_sal['Año'] + '-' + df_sal['Mes_Num'].astype(str).str.zfill(2) + '-01')
        df_sal = df_sal[df_sal['Date'].dt.year >= 2000].sort_values('Date').reset_index(drop=True)
        
        min_sal = df_sal[col_sal].min()
        max_sal = df_sal[col_sal].max()
        
        y_min_sal = (min_sal // 100) * 100
        y_max_sal = ((max_sal // 100) + 1) * 100
        hitos_sal = list(range(int(y_min_sal), int(y_max_sal) + 1, 100))
        
        val_curr = df_sal[col_sal].iloc[-1]
        val_prev_m = df_sal[col_sal].iloc[-2] if len(df_sal) > 1 else val_curr
        val_prev_y = df_sal[col_sal].iloc[-13] if len(df_sal) > 12 else val_curr
        var_m = (val_curr - val_prev_m) / val_prev_m * 100 if val_prev_m else 0
        var_y = (val_curr - val_prev_y) / val_prev_y * 100 if val_prev_y else 0
        fecha_str = df_sal['Fecha'].iloc[-1].title()
        
        # --- NUEVO: RANKING SALARIOS ---
        excluir_sal = ['Fecha', 'Año', 'Mes_Str', 'Mes_Num', 'Date', 'Nacional', 'Total', '(Todo)']
        state_cols_sal = [c for c in df_sal.columns if c not in excluir_sal]
        last_row_sal = df_sal.iloc[-1][state_cols_sal].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('$', '', regex=False)
        last_row_sal = pd.to_numeric(last_row_sal, errors='coerce')
        
        rk_sal = int(last_row_sal.rank(ascending=False, method='min')[col_sal])
        top1_sal = last_row_sal.idxmax()
        rank_html_sal = f"<br>Rank: <b>#{rk_sal}</b>" if rk_sal == 1 else f"<br>Rank: <b>#{rk_sal}</b> <span style='font-size:11px; color:#666;'>(1º {top1_sal})</span>"
        
        fig_sal = px.line(df_sal, x='Date', y=col_sal)
        fig_sal.update_traces(line_color='#28a745', line_width=2.5)
        
        valor_inicial_sal = df_sal[col_sal].iloc[0]
        for hito in hitos_sal:
            # Forzar dibujo de línea horizontal de extremo a extremo
            fig_sal.add_hline(y=hito, line_color='rgba(255,255,255,0.2)', line_width=1, layer='below')

            if valor_inicial_sal < hito: 
                cruce = df_sal[df_sal[col_sal] >= hito]
                if not cruce.empty:
                    primer_cruce = cruce.iloc[0]
                    texto_etiqueta = f"{primer_cruce['Mes_Str'][:3].capitalize()} {primer_cruce['Año']}"
                    
                    fig_sal.add_trace(go.Scatter(
                        x=[primer_cruce['Date']], y=[primer_cruce[col_sal]], mode='markers+text',
                        marker=dict(color='white', size=9, line=dict(color='#28a745', width=2)),
                        text=[texto_etiqueta], textposition="top left",
                        textfont=dict(color="#28a745", size=11, weight="bold"),
                        showlegend=False, hoverinfo='skip',
                        cliponaxis=False 
                    ))

        ficha_sal_html = f"<b>{fecha_str}</b>{rank_html_sal}<br><span style='font-size:16px;'><b>${val_curr:,.2f}</b></span> MXN<br>Var Mensual: <span style='color:{'#28a745' if var_m >=0 else '#dc3545'}'>{var_m:+.2f}%</span><br>Var Anual: <span style='color:{'#28a745' if var_y >=0 else '#dc3545'}'>{var_y:+.2f}%</span>"
        fig_sal.add_annotation(
            x=0.02, y=0.95, xref='paper', yref='paper', text=ficha_sal_html, showarrow=False, align='left', 
            bgcolor='rgba(255, 255, 255, 0.95)', bordercolor='#28a745', borderwidth=2, borderpad=8, font=dict(color='black', size=12)
        )

        fig_sal.update_layout(
            title=dict(text="SALARIO BASE DE COTIZACIÓN (IMSS)", font=dict(color='white', size=14), x=0.0),
            xaxis_title="", yaxis_title="", height=450, margin=dict(t=50, b=20, l=10, r=10),
            xaxis=dict(
                showticklabels=True, tickformat="%Y", gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#ccc'),
                showline=False # Apagamos líneas de borde inferior nativas
            ),
            yaxis=dict(
                range=[y_min_sal, y_max_sal], autorange=False, 
                tickmode='array', tickvals=hitos_sal, 
                showgrid=False, # --- Apagamos el grid nativo porque usamos add_hline ---
                tickformat="$ ,.0f", tickfont=dict(color='#ccc'),
                showline=False, zeroline=False # --- Cero bordes laterales ---
            ),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_sal, use_container_width=True)
    else:
        st.info("Datos históricos de salarios no disponibles.")

# ==========================================
# SECCIÓN 5: EDUCACIÓN
# ==========================================
st.markdown("---")

try:
    ciclo_edu = DATA['edu_tot']['Ciclo'].iloc[0]
    texto_ciclo = f" ({ciclo_edu})"
except:
    texto_ciclo = ""

st.header(f"5. Educación Superior{texto_ciclo}")
st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: Anuario Estadístico de la Población Escolar en Educación Superior (ANUIES)</div>", unsafe_allow_html=True)

try:
    df_tot = DATA['edu_tot'].copy()
    df_mat = DATA['edu_mat'].copy()
    df_egr = DATA['edu_egr'].copy()

    def clean_cols(df, cols):
        for col in cols:
            if col in df.columns and df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '').astype(float)
        return df

    df_tot = clean_cols(df_tot, ['Matrícula Total', 'Egresados Total'])
    df_mat = clean_cols(df_mat, ['Matrícula Total', 'Participacion_Matricula'])
    df_egr = clean_cols(df_egr, ['Egresados Total', 'Participacion_Egresados'])

    def clean_entidad(name):
        return NAME_NORMALIZER.get(str(name).strip().title(), str(name).strip().title())

    def get_edu_context(df_full, val_col, state_target, nivel=None, campo=None):
        df_f = df_full.copy()
        if nivel: df_f = df_f[df_f['Nivel_Agrupado'] == nivel]
        if campo: df_f = df_f[df_f['CAMPO AMPLIO'] == campo]

        df_f['ENTIDAD_NORM'] = df_f['ENTIDAD'].apply(clean_entidad)
        state_tgt_norm = clean_entidad(state_target)
        
        agg = df_f.groupby('ENTIDAD_NORM')[val_col].sum().reset_index()
        tot_nac = agg[val_col].sum()

        if tot_nac == 0 or agg.empty:
            return 0, 0, "-", 0

        agg['Rank'] = agg[val_col].rank(ascending=False, method='min')
        agg = agg.sort_values('Rank')
        top1 = agg.iloc[0]['ENTIDAD_NORM']

        st_row = agg[agg['ENTIDAD_NORM'].str.upper() == state_tgt_norm.upper()]
        if st_row.empty:
            return 0, 0, top1, 0

        val = st_row.iloc[0][val_col]
        rank = int(st_row.iloc[0]['Rank'])
        share = (val / tot_nac) * 100
        return val, rank, top1, share

    # Renderizador HTML para el Valor Total (Más ancho y con candado de espacio)
    def main_stat_html(title, data_tuple, target_state, color_main):
        val, rank, top1, share = data_tuple
        top_str_clean = f"<b>#1 {top1}</b>"
        
        return f"""<div style="min-width: 260px; flex-shrink: 0; padding-right: 15px; border-right: 1px solid #dee2e6; margin-right: 5px; display: flex; flex-direction: column;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 15px;">
<div style="font-size:2.2rem; font-weight:800; color:{color_main}; line-height: 1.1;">{val:,.0f}</div>
<div style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: bold; margin-top: 5px;">#{rank}</div>
</div>
<div style="font-size:0.95rem; color:#444; text-transform: uppercase; font-weight:800; margin-bottom: 8px; margin-top: 5px;">{title}</div>
<div style="font-size:0.8rem; color:#555;">
<div style="margin-bottom: 2px;">{top_str_clean}</div>
<div>Participación Nacional: <span style="font-weight:700; color:#212529;">{share:.1f}%</span></div>
</div>
</div>"""

    # Renderizador HTML para los Niveles Internos
    def sub_box_html(title, data_tuple, target_state, color_main):
        val, rank, top1, share = data_tuple
        top_str_clean = f"<b>#1 {top1}</b>"
        
        return f"""<div style="background: white; padding: 10px 12px; border-radius: 8px; border: 1px solid #dee2e6; flex: 1; min-width: 130px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
<div>
<div style="display: flex; justify-content: space-between; align-items: flex-start;">
<div style="font-size: 0.75rem; color: #555; text-transform: uppercase; font-weight: 800;">{title}</div>
<div style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold;">#{rank}</div>
</div>
<div style="font-weight: 800; color: {color_main}; font-size: 1.25rem; margin-top: 2px;">{val:,.0f}</div>
</div>
<div style="font-size: 0.75rem; color: #555; margin-top: 8px; line-height: 1.4; border-top: 1px solid #f0f0f0; padding-top: 6px;">
<div style="margin-bottom: 2px;">{top_str_clean}</div>
<div>Participación Nacional: <span style="font-weight:700; color:#212529;">{share:.1f}%</span></div>
</div>
</div>"""

    state_target = state_norm 

    df_tot_est = df_tot[df_tot['ENTIDAD'].apply(clean_entidad).str.upper() == state_target.upper()]
    
    if not df_tot_est.empty:
        
        ctx_mat_tot = get_edu_context(df_tot, 'Matrícula Total', state_target)
        ctx_mat_lic = get_edu_context(df_tot, 'Matrícula Total', state_target, 'Licenciatura')
        ctx_mat_tsu = get_edu_context(df_tot, 'Matrícula Total', state_target, 'Técnico Superior')
        ctx_mat_mae = get_edu_context(df_tot, 'Matrícula Total', state_target, 'Maestría')
        ctx_mat_doc = get_edu_context(df_tot, 'Matrícula Total', state_target, 'Doctorado')

        ctx_egr_tot = get_edu_context(df_tot, 'Egresados Total', state_target)
        ctx_egr_lic = get_edu_context(df_tot, 'Egresados Total', state_target, 'Licenciatura')
        ctx_egr_tsu = get_edu_context(df_tot, 'Egresados Total', state_target, 'Técnico Superior')
        ctx_egr_mae = get_edu_context(df_tot, 'Egresados Total', state_target, 'Maestría')
        ctx_egr_doc = get_edu_context(df_tot, 'Egresados Total', state_target, 'Doctorado')

        html_general = f"""<div style="border-left: 5px solid #17a2b8; padding-left: 20px; margin-bottom: 30px; background-color: #f8f9fa; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
<h3 style="color:#0056b3; margin-top:0; margin-bottom:20px;">Panorama General</h3>
<div style="display: flex; flex-direction: column; gap: 20px;">
<div style="display: flex; align-items: stretch; flex-wrap: nowrap; gap: 15px; border-bottom: 1px solid #dee2e6; padding-bottom: 20px; overflow-x: auto;">
{main_stat_html("Matrícula", ctx_mat_tot, state_target, "#212529")}
{sub_box_html("Licenciatura", ctx_mat_lic, state_target, "#17a2b8")}
{sub_box_html("Técnico Sup.", ctx_mat_tsu, state_target, "#17a2b8")}
{sub_box_html("Maestría", ctx_mat_mae, state_target, "#17a2b8")}
{sub_box_html("Doctorado", ctx_mat_doc, state_target, "#17a2b8")}
</div>
<div style="display: flex; align-items: stretch; flex-wrap: nowrap; gap: 15px; overflow-x: auto;">
{main_stat_html("Egresados", ctx_egr_tot, state_target, "#28a745")}
{sub_box_html("Licenciatura", ctx_egr_lic, state_target, "#28a745")}
{sub_box_html("Técnico Sup.", ctx_egr_tsu, state_target, "#28a745")}
{sub_box_html("Maestría", ctx_egr_mae, state_target, "#28a745")}
{sub_box_html("Doctorado", ctx_egr_doc, state_target, "#28a745")}
</div>
</div>
</div>"""
        
        st.markdown(html_general, unsafe_allow_html=True)

        st.markdown("#### Principal Campo de Formación por Nivel Educativo")
        col_mat, col_egr = st.columns(2)

        niveles_orden = ['Licenciatura', 'Técnico Superior', 'Maestría', 'Doctorado']

        df_top_mat_est = df_mat[df_mat['ENTIDAD'].apply(clean_entidad).str.upper() == state_target.upper()]
        df_top_egr_est = df_egr[df_egr['ENTIDAD'].apply(clean_entidad).str.upper() == state_target.upper()]

        def get_top1_by_level(df, nivel, val_col, share_col):
            subset = df[df['Nivel_Agrupado'] == nivel]
            if not subset.empty:
                row = subset.sort_values(val_col, ascending=False).iloc[0]
                return row['CAMPO AMPLIO'], row[val_col], row[share_col]
            return None, 0, 0

        def campo_card_html(nivel, campo, val_est, share_est, ctx_tuple, color_main, label_val):
            val_nac, rk_nac, top1_nac, sh_nac = ctx_tuple
            top_str_clean = f"<b>#1 {top1_nac}</b>"
            
            return f"""<div style="background: white; padding: 15px; border-radius: 8px; border-left: 5px solid {color_main}; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;">
<div style="display: flex; justify-content: space-between; align-items: flex-start;">
<div style="font-size:0.8rem; color:#555; font-weight:800; text-transform: uppercase; margin-bottom:5px; letter-spacing: 0.5px;">{nivel}</div>
<div style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: bold;">#{rk_nac}</div>
</div>
<div style="font-weight:700; font-size:1.05rem; color:#212529; margin-bottom:10px; line-height: 1.2;">{campo}</div>
<div style="display:flex; justify-content:space-between; align-items:center; background: #f8f9fa; padding: 8px 10px; border-radius: 6px; margin-bottom: 10px;">
<div style="text-align: center;">
<div style="color:{color_main}; font-weight:800; font-size:1.1rem;">{share_est:.1f}%</div>
<div style="font-size:0.7rem; color:#555; text-transform: uppercase;">Del Estado</div>
</div>
<div style="width: 1px; background: #dee2e6; height: 30px;"></div>
<div style="text-align: center;">
<div style="color:#212529; font-weight:800; font-size:1.1rem;">{val_est:,.0f}</div>
<div style="font-size:0.7rem; color:#555; text-transform: uppercase;">{label_val}</div>
</div>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; font-size: 0.8rem; color: #555; border-top: 1px dashed #dee2e6; padding-top: 8px;">
<span>{top_str_clean}</span>
<span>Participación Nac.: <span style="font-weight:700; color:#212529;">{sh_nac:.1f}%</span></span>
</div>
</div>"""

        with col_mat:
            st.markdown(f"<div style='margin-bottom:15px; font-weight:800; color:#0056b3; font-size:1.1rem;'>Por Matrícula</div>", unsafe_allow_html=True)
            for nivel in niveles_orden:
                campo, val, share = get_top1_by_level(df_top_mat_est, nivel, 'Matrícula Total', 'Participacion_Matricula')
                if campo:
                    ctx_campo = get_edu_context(df_mat, 'Matrícula Total', state_target, nivel, campo)
                    st.markdown(campo_card_html(nivel, campo, val, share, ctx_campo, "#17a2b8", "Alumnos"), unsafe_allow_html=True)

        with col_egr:
            st.markdown(f"<div style='margin-bottom:15px; font-weight:800; color:#198754; font-size:1.1rem;'>Por Egresados</div>", unsafe_allow_html=True)
            for nivel in niveles_orden:
                campo, val, share = get_top1_by_level(df_top_egr_est, nivel, 'Egresados Total', 'Participacion_Egresados')
                if campo:
                    ctx_campo = get_edu_context(df_egr, 'Egresados Total', state_target, nivel, campo)
                    st.markdown(campo_card_html(nivel, campo, val, share, ctx_campo, "#28a745", "Egresados"), unsafe_allow_html=True)

    else:
        st.info(f"No se encontraron datos de Educación Superior para {state_norm}.")

except Exception as e:
    st.error(f"Error procesando módulo de educación: {str(e)}")

# ==========================================
# SECCIÓN 6: PRODUCTIVIDAD
# ==========================================
st.markdown("---")

df_saic = DATA['saic'].copy() 

# 1. Extraemos el año censal para el título
try:
    anio_saic = df_saic['Anio_Censal'].iloc[0]
    texto_anio_saic = f" ({anio_saic})"
except:
    texto_anio_saic = ""

st.header(f"6. Productividad Laboral{texto_anio_saic}")
st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: Censos Económicos (INEGI)</div>", unsafe_allow_html=True)

df_saic['Entidad_Norm'] = df_saic['Entidad'].str.strip().replace(NAME_NORMALIZER)
df_saic['Rank'] = df_saic['Indicador_Productividad'].rank(ascending=False)

row = df_saic[df_saic['Entidad_Norm'] == state_norm]

if not row.empty:
    val = row['Indicador_Productividad'].values[0]
    rk = int(row['Rank'].values[0])
    nombre_estado = row['Entidad'].values[0]
    
    top1 = df_saic.sort_values('Indicador_Productividad', ascending=False).iloc[0]
    avg = df_saic['Indicador_Productividad'].mean()
    
    # 4. Condicional de color para el valor estatal
    val_color = "#28a745" if val > avg else "#dc3545" # Verde si es mayor, rojo si es menor
    
    card_html = """
    <div style="background-color: white; padding: 15px; border-radius: 8px; text-align: center; color: black; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 0px;">
        <p style="margin: 0; font-size: 14px; color: #6c757d; font-weight: bold;">{title}</p>
        <p style="margin: 0; font-size: 22px; font-weight: bold; color: {color_val};">{value}</p>
    </div>
    """
    
    c1, c2, c3, c4 = st.columns(4)
    # 3. Agregamos el separador de miles a toda la sección (,{.2f})
    c1.markdown(card_html.format(title="Posición", value=f"#{rk}", color_val="#212529"), unsafe_allow_html=True)
    c2.markdown(card_html.format(title=nombre_estado, value=f"{val:,.2f}", color_val=val_color), unsafe_allow_html=True)
    c3.markdown(card_html.format(title="Promedio Nacional", value=f"{avg:,.2f}", color_val="#212529"), unsafe_allow_html=True)
    c4.markdown(card_html.format(title=f"1er Lugar ({top1['Entidad']})", value=f"{top1['Indicador_Productividad']:,.2f}", color_val="#212529"), unsafe_allow_html=True)
    
    df_sorted = df_saic.sort_values('Indicador_Productividad', ascending=False).reset_index(drop=True)
    
    # 6. Usamos el color azul del IMSS para remarcar la entidad
    colors = ['#007bff' if x == state_norm else '#e9ecef' for x in df_sorted['Entidad_Norm']]
    
    fig = px.bar(df_sorted, x='Entidad', y='Indicador_Productividad')
    fig.update_traces(marker_color=colors, hovertemplate="%{y:,.2f}<extra></extra>")
    
    # 5. Renombramos a "Promedio Nacional"
    fig.add_hline(y=avg, line_dash="dot", line_color="white", annotation_text="Promedio Nacional", annotation_font_color="white")
    
    # 2. Recuadro con la fórmula dentro de la gráfica
    fig.add_annotation(
        x=0.99, y=0.95, xref='paper', yref='paper', 
        text="Indicador = Producción Bruta / Personal Ocupado", 
        showarrow=False, align='right', 
        bgcolor='rgba(255, 255, 255, 0.95)', bordercolor='#dee2e6', borderwidth=1, borderpad=8, font=dict(color='#555', size=12)
    )
    
    fig.update_layout(
        yaxis_title="Productividad",
        xaxis_title="",
        xaxis_tickangle=-90,
        margin=dict(t=20, b=0, l=0, r=0),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# SECCIÓN 7: IMCO
# ==========================================
st.markdown("---")

df_g = DATA['imco_g'].copy()

# 1. Extraemos el año para el título (Ajustado para fechas como "01/01/2025")
try:
    # Buscamos la columna que represente el año (Año, AÃ±o, etc.)
    col_anio_candidatas = [c for c in df_g.columns if str(c).strip().upper().startswith('A') and str(c).strip().lower().endswith('o')]
    col_anio = col_anio_candidatas[0] if col_anio_candidatas else 'AÃ±o'
    
    val_bruto = str(df_g[col_anio].iloc[0]).strip()
    
    # Extraemos el año si viene en formato de fecha (ej. 01/01/2025)
    if '/' in val_bruto:
        anio_imco = val_bruto.split('/')[-1]
    elif '-' in val_bruto:
        anio_imco = val_bruto.split('-')[0]
    else:
        anio_imco = val_bruto
        
    texto_anio_imco = f" ({anio_imco})"
except Exception as e:
    texto_anio_imco = ""

st.header(f"7. Competitividad{texto_anio_imco}")
st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: Índice de Competitividad Estatal (IMCO)</div>", unsafe_allow_html=True)

df_g['Entidad_Norm'] = df_g['Entidad'].str.strip().replace(NAME_NORMALIZER)
row = df_g[df_g['Entidad_Norm'] == state_norm]

if not row.empty:
    val = row['Valor'].values[0]
    rk = int(row['Ranking'].values[0])
    nombre_estado = row['Entidad'].values[0]
    
    top1 = df_g.sort_values('Valor', ascending=False).iloc[0]
    avg = df_g['Valor'].mean()
    
    card_html = """
    <div style="background-color: white; padding: 15px; border-radius: 8px; text-align: center; color: black; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 0px;">
        <p style="margin: 0; font-size: 14px; color: #6c757d; font-weight: bold;">{title}</p>
        <p style="margin: 0; font-size: 22px; font-weight: bold; color: #212529;">{value}</p>
    </div>
    """
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(card_html.format(title="Posición", value=f"#{rk}"), unsafe_allow_html=True)
    c2.markdown(card_html.format(title=nombre_estado, value=f"{val:.2f}"), unsafe_allow_html=True)
    c3.markdown(card_html.format(title="Promedio Nacional", value=f"{avg:.2f}"), unsafe_allow_html=True)
    c4.markdown(card_html.format(title=f"1er Lugar ({top1['Entidad']})", value=f"{top1['Valor']:.2f}"), unsafe_allow_html=True)
    
    df_sorted = df_g.sort_values('Valor', ascending=False).reset_index(drop=True)
    
    # Usamos el color verde de la gráfica del IMSS (#28a745) para el estado
    colors = ['#28a745' if x == state_norm else '#e9ecef' for x in df_sorted['Entidad_Norm']]
    
    fig = px.bar(df_sorted, x='Entidad', y='Valor')
    fig.update_traces(marker_color=colors, hovertemplate="%{y:,.2f}<extra></extra>")
    
    # Línea con el texto "Promedio Nacional"
    fig.add_hline(y=avg, line_dash="dot", line_color="white", annotation_text="Promedio Nacional", annotation_font_color="white")
    
    fig.update_layout(
        yaxis_title="Competitividad",
        xaxis_title="",
        xaxis_tickangle=-90,
        margin=dict(t=20, b=0, l=0, r=0),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

df_d = DATA['imco_d'].copy()
df_d['Entidad_Norm'] = df_d['Entidad'].str.strip().replace(NAME_NORMALIZER)
st_d = df_d[df_d['Entidad_Norm'] == state_norm].copy()

# --- CONFIGURACIÓN DE FILTROS Y CORRECCIONES ---

INDICADORES_IGNORADOS = [
     "Acceso a internet"
]

CORRECCION_NOMBRES = {
    "Perc. de corrupción estatal": "Percepción de corrupción estatal"
}

if not st_d.empty:
    st_d = st_d[~st_d['Indicador'].isin(INDICADORES_IGNORADOS)].copy()
    st_d['Indicador'] = st_d['Indicador'].replace(CORRECCION_NOMBRES)

    TIPO_INDICADOR = {
        "Acceso a instituciones de salud": "Directo",
        "Acceso a internet": "Directo",
        "Camas de hospital": "Directo",
        "Captación de ahorro": "Directo",
        "Carga aérea": "Directo",
        "Cobertura educativa": "Directo",
        "Competencia en servicios notariales": "Directo",
        "Consulta info finanzas públicas": "Directo",
        "Crecimiento de UE >50 empleados": "Directo",
        "Crecimiento del PIB": "Directo",
        "Crecimiento puestos de trabajo (IMSS)": "Directo",
        "Diversificación económica": "Directo",
        "Esperanza de vida": "Directo",
        "Flujo de pasajeros aéreos": "Directo",
        "Grado de escolaridad": "Directo",
        "Ingreso promedio de tiempo completo": "Directo",
        "Ingresos propios": "Directo",
        "Mujeres económicamente activas": "Directo",
        "Participación ciudadana en elecciones": "Directo",
        "Patentes": "Directo",
        "Percepción de seguridad": "Directo",
        "Personal médico con especialidad": "Directo",
        "Personal médico y de enfermería": "Directo",
        "Población con educación superior": "Directo",
        "Tasa de participación": "Directo",
        "Terminales punto de venta": "Directo",
        "Uso de banca móvil": "Directo",
        "Agresiones a periodistas": "Inverso",
        "Brecha de ingresos por género": "Inverso",
        "Costo promedio de la deuda": "Inverso",
        "Delitos no denunciados": "Inverso",
        "Desigualdad salarial": "Inverso",
        "Deuda estatal y organismos": "Inverso",
        "Diferencia de informalidad laboral H-M": "Inverso",
        "Heridos en accidentes de tránsito terrestre": "Inverso",
        "Homicidios": "Inverso",
        "Incidencia delictiva": "Inverso",
        "Informalidad laboral": "Inverso",
        "Jornadas laborales >48h": "Inverso",
        "Morbilidad respiratoria": "Inverso",
        "Percepción de corrupción estatal": "Inverso",
        "Personas con ingresos debajo de la línea de bienestar": "Inverso",
        "Robo de vehículos": "Inverso"
    }

    def calc_puntaje(row):
        ind = str(row['Indicador']).strip()
        tipo = TIPO_INDICADOR.get(ind, "Directo") 
        return row['Rank'] if tipo == "Directo" else 33 - row['Rank']

    def calc_cambio(row):
        ind = str(row['Indicador']).strip()
        tipo = TIPO_INDICADOR.get(ind, "Directo")
        return row['Cambio_Posicion'] if tipo == "Directo" else -row['Cambio_Posicion']

    st_d['Puntaje_Fortaleza'] = st_d.apply(calc_puntaje, axis=1)
    st_d['Cambio_Ajustado'] = st_d.apply(calc_cambio, axis=1)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**✅ Top 5 Fortalezas**")
        for _, r in st_d.sort_values('Puntaje_Fortaleza').head(5).iterrows():
            ch = r['Cambio_Ajustado']
            if ch > 0: badge = f"<span style='background-color:#28a745; color:white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left:5px;'>▲ {int(abs(ch))}</span>"
            elif ch < 0: badge = f"<span style='background-color:#dc3545; color:white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left:5px;'>▼ {int(abs(ch))}</span>"
            else: badge = f"<span style='background-color:#007bff; color:white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left:5px;'>=</span>"
            
            st.markdown(f"- **#{int(r['Rank'])}** {r['Indicador']} {badge}", unsafe_allow_html=True)
    with c2:
        st.markdown("**⚠️ Top 5 Áreas de oportunidad**")
        for _, r in st_d.sort_values('Puntaje_Fortaleza', ascending=False).head(5).iterrows():
            ch = r['Cambio_Ajustado']
            if ch > 0: badge = f"<span style='background-color:#28a745; color:white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left:5px;'>▲ {int(abs(ch))}</span>"
            elif ch < 0: badge = f"<span style='background-color:#dc3545; color:white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left:5px;'>▼ {int(abs(ch))}</span>"
            else: badge = f"<span style='background-color:#007bff; color:white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left:5px;'>=</span>"
            
            st.markdown(f"- **#{int(r['Rank'])}** {r['Indicador']} {badge}", unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("ℹ️ **Nota:** El cambio de posiciones mostrado corresponde a la variación respecto al año anterior.")

# ==========================================
# SECCIÓN 8: RATINGS
# ==========================================
if "Tlaxcala" not in selected_name:
    st.markdown("---")
    st.header("8. Calificación Crediticia")
    
    df_r = DATA['ratings']
    match = pd.DataFrame()
    
    # Texto por defecto (por si no hay datos o archivo)
    fuente_str = "Calificación Crediticia (HR Ratings y/o Fitch Ratings)"
    
    if not df_r.empty:
        col_ent = [c for c in df_r.columns if "Entidad" in c][0]
        # Filtramos primero los datos para saber qué agencias existen para este estado
        match = df_r[df_r[col_ent].astype(str).apply(lambda x: NAME_NORMALIZER.get(x, x)) == state_norm].copy()
        
        if not match.empty:
            # Detectamos qué agencias están presentes en la columna 'Calificadora'
            agencias = match['Calificadora'].astype(str).unique()
            has_hr = any("HR" in ag for ag in agencias)
            has_fitch = any("Fitch" in ag for ag in agencias)
            
            # Definimos el texto de la fuente según lo encontrado
            if has_hr and has_fitch:
                fuente_str = "Calificación Crediticia (HR Ratings y Fitch Ratings)"
            elif has_fitch:
                fuente_str = "Calificación Crediticia (Fitch Ratings)"
            elif has_hr:
                fuente_str = "Calificación Crediticia (HR Ratings)"
    
    # Imprimimos la fuente dinámica justo debajo del título
    st.markdown(f"<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: {fuente_str}</div>", unsafe_allow_html=True)
    
    # Renderizamos la tabla si hay datos
    if not match.empty:
        # Renombramos y unificamos los nombres de las columnas para mayor presentación
        match = match.rename(columns={
            "Fecha Publicacion": "Fecha de Publicación",
            "Fecha de Publicacion": "Fecha de Publicación",
            "Fecha Publicación": "Fecha de Publicación",
            "Calificacion": "Calificación",
            "Descripcion": "Descripción"
        })
        
        # Reordenamos las columnas quitando Entidad y agregando Descripción
        columnas_deseadas = [
            "Calificadora", 
            "Calificación", 
            "Perspectiva", 
            "Descripción", 
            "Fecha de Publicación"
        ]
        
        # Filtramos solo las columnas que realmente existan en el DataFrame 
        columnas_finales = [c for c in columnas_deseadas if c in match.columns]
        
        # Mostramos el dataframe ocupando todo el ancho del contenedor
        st.dataframe(match[columnas_finales], hide_index=True, use_container_width=True)
        
    elif not df_r.empty:
        st.info("Sin calificación.")
    else: 
        st.info("Archivo no disponible.")

# ==========================================
# SECCIÓN 9: TOP EXPORTACIONES
# ==========================================
st.markdown("---")
if "Tlaxcala" in selected_name:
    st.header("8. Principales Sectores de Exportación")
    st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: Exportaciones por Entidad Federativa (INEGI)</div>", unsafe_allow_html=True)
else:
    st.header("9. Principales Sectores de Exportación")
    st.markdown("<div style='font-size: 0.75rem; color: #888; font-style: italic; margin-top: -15px; margin-bottom: 20px;'>Fuente: Exportaciones por Entidad Federativa (INEGI)</div>", unsafe_allow_html=True)

df_e = DATA['export'].copy()
df_e['Year'] = df_e['Periodo'].astype(str).str[:4].astype(int)
df_e['Quarter'] = df_e['Periodo'].astype(str).str[-2:]
max_y = df_e['Year'].max()

# Obtenemos los trimestres disponibles del año actual (ej. 1T, 2T, 3T)
quarters_avail = df_e[df_e['Year'] == max_y]['Quarter'].unique()

# Filtro Actual y Previo
st_e_curr = df_e[(df_e['Estado_ID'].astype(str).str.zfill(2) == state_id_str) & (df_e['Year'] == max_y) & (df_e['Sector'] != 'Total')]
st_e_prev = df_e[(df_e['Estado_ID'].astype(str).str.zfill(2) == state_id_str) & (df_e['Year'] == (max_y - 1)) & (df_e['Quarter'].isin(quarters_avail)) & (df_e['Sector'] != 'Total')]

if not st_e_curr.empty:
    # Top 10 del año actual
    top10 = st_e_curr.groupby('Sector')['Valor'].sum().reset_index().sort_values('Valor', ascending=False).head(10)
    tot_curr = top10['Valor'].sum()
    top10['Part'] = (top10['Valor']/tot_curr*100) if tot_curr > 0 else 0
    
    # Unir valores del año anterior para esos mismos sectores
    if not st_e_prev.empty:
        prev_agg = st_e_prev.groupby('Sector')['Valor'].sum().reset_index().rename(columns={'Valor': 'Valor_Prev'})
        top10 = top10.merge(prev_agg, on='Sector', how='left')
    else:
        top10['Valor_Prev'] = 0
    top10['Valor_Prev'] = top10['Valor_Prev'].fillna(0)
    
    # Ranks Nacionales del Año Actual
    nac_curr_agg = df_e[(df_e['Year'] == max_y) & (df_e['Sector'] != 'Total')].groupby(['Sector', 'Estado_ID'])['Valor'].sum().reset_index()
    rks = []
    for s in top10['Sector']:
        d_s = nac_curr_agg[nac_curr_agg['Sector'] == s].copy()
        d_s['Rank'] = d_s['Valor'].rank(ascending=False)
        try: r = int(d_s[d_s['Estado_ID'].astype(str).str.zfill(2) == state_id_str]['Rank'].values[0])
        except: r = "-"
        rks.append(r)
    top10['Rank Nac'] = rks

    # Max val global para escalar el 100% de la barra
    max_val_scale = max(top10['Valor'].max(), top10['Valor_Prev'].max())
    
    # Lógica para la leyenda de trimestres (Ej. "1T-3T 2025")
    q_len = len(quarters_avail)
    q_prefix = f"1T-{q_len}T" if q_len > 1 else "1T"
    label_curr = f"{q_prefix} {max_y}"
    label_prev = f"{q_prefix} {max_y - 1}"
    
    # IMPORTANTE: Todo este HTML debe ir sin espacios iniciales para que Markdown no lo tome como código
    html_export = f"""<div style="background-color: transparent; width: 100%; margin-top: 10px; font-family: sans-serif; color: #ffffff;">
<div style="display: flex; justify-content: flex-start; margin-bottom:15px; font-size: 0.85rem; color: #ffffff;">
<div style="display:flex; align-items:center; margin-right:15px;"><div style="width:12px; height:12px; background-color:#007bff; margin-right:5px; border-radius:2px;"></div> {label_curr}</div>
<div style="display:flex; align-items:center;"><div style="width:12px; height:12px; background-color:#28a745; margin-right:5px; border-radius:2px;"></div> {label_prev}</div>
</div>
<div style="display: flex; width: 100%; margin-bottom: 20px; font-weight: bold; text-align: center; font-size: 0.95rem; justify-content: flex-start; gap: 15px; color: #ffffff;">
<div style="width: 25%; text-align: left; padding-left: 5px;">Sector</div>
<div style="width: 40%; text-align: left; padding-left: 0px;">Millones de Dólares</div>
<div style="width: 120px;">% en el total<br>estatal</div>
<div style="width: 120px;">Ranking<br>nacional</div>
</div>"""
    
    for _, r in top10.iterrows():
        pct_curr = max((r['Valor'] / max_val_scale) * 100 if max_val_scale > 0 else 0, 0.5) # Min 0.5% para que se vea una rayita
        pct_prev = max((r['Valor_Prev'] / max_val_scale) * 100 if max_val_scale > 0 else 0, 0.5)
        
        val_curr_m = r['Valor'] / 1000
        val_prev_m = r['Valor_Prev'] / 1000
        
        sector_wrapped = '<br>'.join(textwrap.wrap(r['Sector'], width=38))
        
        html_export += f"""<div style="display: flex; width: 100%; align-items: stretch; margin-bottom: 16px; justify-content: flex-start; gap: 15px;">
<div style="width: 25%; text-align: left; padding-left: 5px; font-size: 0.85rem; display: flex; align-items: center; justify-content: flex-start;">
<span style="display: inline-block; line-height: 1.2; color: #ffffff; font-weight: 500;">{sector_wrapped}</span>
</div>
<div style="width: 40%; border-left: 2px solid #555; padding-left: 0; display: flex; flex-direction: column; justify-content: center; gap: 8px;">
<div style="display:flex; align-items:center; width: 100%;">
<div style="flex-grow: 1;"><div style="background-color: #007bff; width: {pct_curr}%; height: 18px; border-radius: 0 4px 4px 0; box-shadow: 1px 1px 2px rgba(0,0,0,0.1);"></div></div>
<span style="width: 65px; margin-left: 8px; flex-shrink: 0; text-align: left; font-weight: 800; font-size: 0.85rem; color: #ffffff;">{val_curr_m:,.0f}</span>
</div>
<div style="display:flex; align-items:center; width: 100%;">
<div style="flex-grow: 1;"><div style="background-color: #28a745; width: {pct_prev}%; height: 14px; border-radius: 0 4px 4px 0; opacity: 0.85;"></div></div>
<span style="width: 65px; margin-left: 8px; flex-shrink: 0; text-align: left; font-weight: 600; font-size: 0.75rem; color: #ffffff;">{val_prev_m:,.0f}</span>
</div>
</div>
<div style="width: 120px; display: flex; justify-content: center; align-items: center;">
<div style="border: 1px solid #dee2e6; background-color: #ffffff; border-radius: 6px; padding: 4px 0; width: 100%; font-weight: bold; font-size: 0.9rem; color: #212529; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
{r['Part']:.1f}%
</div>
</div>
<div style="width: 120px; display: flex; justify-content: center; align-items: center;">
<div style="border: 1px solid #dee2e6; background-color: #ffffff; border-radius: 6px; padding: 4px 0; width: 100%; font-weight: bold; font-size: 0.9rem; color: #212529; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
{r['Rank Nac']}°
</div>
</div>
</div>"""
        
    html_export += "</div>"
    st.markdown(html_export, unsafe_allow_html=True)