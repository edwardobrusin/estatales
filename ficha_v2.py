import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import textwrap

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA (BRANDING NAFIN/BANCOMEXT)
# ==========================================
st.set_page_config(
    page_title="Ficha Técnica Estatal | NAFIN - BANCOMEXT",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Avanzados - Identidad Institucional
st.markdown("""
<style>
    /* Fondo general de la aplicación ligeramente gris para resaltar las tarjetas blancas */
    .stApp {
        background-color: #F8FAFC;
    }

    /* Diseño de menú estilo "Tabs" para los botones del Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #E2E8F0;
    }
    
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 8px; /* Bordes suaves */
        border: none;
        justify-content: flex-start; 
        text-align: left;
        padding: 10px 15px;
        background-color: transparent;
        color: #475569;
        box-shadow: none;
        margin-bottom: 4px;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
    }

    /* Efecto al pasar el mouse por los estados inactivos */
    [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
        background-color: #F1F5F9;
        color: #006A71; /* Teal institucional */
    }

    /* Estado ACTIVO con el color institucional NAFIN/Bancomext */
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background-color: #006A71 !important; /* Teal NAFIN */
        color: #ffffff !important; /* Texto blanco */
        font-weight: 700 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 106, 113, 0.2), 0 2px 4px -1px rgba(0, 106, 113, 0.1) !important;
    }
    
    /* Contenedores de Métricas Premium */
    .metric-container {
        background-color: #ffffff;
        border: 1px solid #E2E8F0;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        margin-bottom: 15px;
        height: 100%;
        transition: transform 0.2s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    }
    
    /* Tipografía institucional */
    .metric-title {
        color: #64748B;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }
    .metric-rank {
        background-color: #006A71; /* Teal NAFIN */
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        vertical-align: middle;
        margin-left: 5px;
    }
    .metric-value {
        color: #0F172A;
        font-size: 2rem;
        font-weight: 800;
        margin: 5px 0;
        letter-spacing: -0.5px;
    }
    
    /* Colores financieros estándar (Positivo/Negativo) */
    .metric-delta-pos { color: #059669; font-weight: 700; font-size: 0.9rem; } /* Verde esmeralda */
    .metric-delta-neg { color: #DC2626; font-weight: 700; font-size: 0.9rem; } /* Rojo carmesí */
    .metric-sub { color: #64748B; font-size: 0.85rem; }
    
    hr { margin: 15px 0; border-top: 1px solid #E2E8F0; }
    
    /* Títulos de sección */
    h1, h2, h3 { color: #0F172A !important; font-weight: 800 !important; letter-spacing: -0.5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CATÁLOGOS Y MAPEOS (SIN CAMBIOS)
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
# 3. CARGA DE DATOS (SIN CAMBIOS)
# ==========================================
@st.cache_data
def load_data():
    path = os.path.join("data", "intermediate")
    raw = os.path.join("data", "raw")
    data = {}
    
    try:
        data['pib'] = pd.read_csv(os.path.join(path, "pib_entidad.csv"))
        data['export'] = pd.read_csv(os.path.join(path, "exportaciones_entidad.csv"))
        data['pob'] = pd.read_csv(os.path.join(path, "poblacion_edad.csv"))
        data['enoe'] = pd.read_csv(os.path.join(path, "enoe_indicadores.csv"))
        data['imss_sal'] = pd.read_csv(os.path.join(path, "salarios_imss.csv"))
        data['imss_pue'] = pd.read_csv(os.path.join(path, "puestos_imss.csv"))
        data['ied_tot'] = pd.read_csv(os.path.join(path, "ied_totales.csv"))
        data['ied_det'] = pd.read_csv(os.path.join(path, "ied_top3_sectores.csv"))
        data['edu_tot'] = pd.read_csv(os.path.join(path, "educacion_totales.csv"))
        data['edu_mat'] = pd.read_csv(os.path.join(path, "educacion_top3_matricula.csv")) 
        data['edu_egr'] = pd.read_csv(os.path.join(path, "educacion_top3_egresados.csv")) 
        data['saic'] = pd.read_csv(os.path.join(path, "saic_productividad.csv"))
        data['imco_g'] = pd.read_csv(os.path.join(path, "imco_general_final.csv"))
        data['imco_d'] = pd.read_csv(os.path.join(path, "imco_desagregado_final.csv"))
        
        rat_path = os.path.join(raw, "ratings_estatales.xlsx")
        data['ratings'] = pd.read_excel(rat_path) if os.path.exists(rat_path) else pd.DataFrame()
        
        gob_path = os.path.join(raw, "gob_sedeco.xlsx")
        data['gob_sedeco'] = pd.read_excel(gob_path) if os.path.exists(gob_path) else pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None
    return data

DATA = load_data()
if not DATA: st.stop()

# ==========================================
# 4. LOGOS INSTITUCIONALES & SIDEBAR
# ==========================================
# Inyectar Logos de NAFIN y Bancomext en el Sidebar
col_logo1, col_logo2 = st.sidebar.columns(2)
try:
    with col_logo1:
        st.image("logos/logo-01.png", use_container_width=True)
    with col_logo2:
        st.image("logos/logo-02.png", use_container_width=True)
except Exception as e:
    st.sidebar.warning("Logos no encontrados en ruta 'logos/'")

st.sidebar.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
st.sidebar.markdown("<h3 style='font-size: 1.1rem; color:#0F172A; margin-bottom: 10px;'>Selecciona Entidad</h3>", unsafe_allow_html=True)

if 'estado_seleccionado' not in st.session_state:
    st.session_state['estado_seleccionado'] = 'Aguascalientes'

def cambiar_estado(nuevo_estado):
    st.session_state['estado_seleccionado'] = nuevo_estado

for estado in list(STATE_MAP.values()):
    btn_type = "primary" if st.session_state['estado_seleccionado'] == estado else "secondary"
    st.sidebar.button(
        label=estado, 
        key=f"btn_{estado}", 
        use_container_width=True, 
        type=btn_type, 
        on_click=cambiar_estado, 
        args=(estado,)
    )

selected_name = st.session_state['estado_seleccionado']
state_norm = NAME_NORMALIZER.get(selected_name, selected_name)
state_id = NAME_TO_ID.get(state_norm)
state_id_str = str(state_id).zfill(2)

# Encabezado Principal
st.markdown(f"<h1 style='color: #006A71; font-size: 2.8rem;'>Ficha Técnica Estatal: {selected_name}</h1>", unsafe_allow_html=True)

if 'gob_sedeco' in DATA and not DATA['gob_sedeco'].empty:
    df_gob = DATA['gob_sedeco']
    info_estado = df_gob[df_gob['Estado'].astype(str).str.strip() == selected_name]
    if not info_estado.empty:
        gobernador = info_estado['Gobernador/a'].values[0]
        sedeco = info_estado['SEDECO'].values[0]
        partido = info_estado['Partido'].values[0]
        st.markdown(f"""
        <div style='background-color: #E2E8F0; padding: 10px 15px; border-radius: 8px; margin-bottom: 20px; display: inline-block;'>
            <span style='color: #475569; font-size: 0.9rem;'>
            <b>Gobernador/a:</b> {gobernador} &nbsp;&nbsp;|&nbsp;&nbsp; <b>SEDECO:</b> {sedeco} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Partido:</b> {partido}
            </span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<p style='text-align: right; color: #94A3B8; font-size: 0.85rem; margin-top: -10px;'><i>MDP: Millones de Pesos &nbsp;|&nbsp; MDD: Millones de Dólares</i></p>", unsafe_allow_html=True)

# ==========================================
# 5. FUNCIONES LÓGICAS (SIN CAMBIOS)
# ==========================================
def format_mm_pesos(val_millones):
    return f"${val_millones:,.2f} <span style='font-size: 0.5em; color:#64748B;'>MDP</span>"

def format_mm_usd(val_miles): 
    val = val_miles / 1000 
    return f"${val:,.2f} <span style='font-size: 0.5em; color:#64748B;'>MDD</span>"

def format_mm_usd_ied(val_millones): 
    return f"${val_millones:,.2f} <span style='font-size: 0.5em; color:#64748B;'>MDD</span>"

def render_card(title, val_str, rank, top1, part, growth, growth_nac):
    c_g = "metric-delta-pos" if growth >= 0 else "metric-delta-neg"
    i_g = "▲" if growth >= 0 else "▼"
    c_gn = "metric-delta-pos" if growth_nac >= 0 else "metric-delta-neg"
    i_gn = "▲" if growth_nac >= 0 else "▼"
    
    title_html = title.replace(" (", "<br>(")
    
    st.markdown(f"""
    <div class="metric-container">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
            <div class="metric-title" style="margin-bottom: 0; line-height: 1.2;">{title_html}</div>
            <div class="metric-rank" style="margin-left: 10px; flex-shrink: 0;">#{rank}</div>
        </div>
        <div class="metric-sub" style="margin-bottom: 5px; color:#94A3B8;">#1 {top1}</div>
        <div class="metric-value">{val_str}</div>
        <div class="metric-sub" style="margin-bottom: 5px;">Participación Nacional: <b style='color:#0F172A;'>{part:.2f}%</b></div>
        <hr>
        <div class="metric-sub" style="background-color: #F8FAFC; padding: 8px; border-radius: 6px;">
            <div style="margin-bottom: 3px; display:flex; justify-content: space-between;"><span>Var. Estatal:</span> <span class="{c_g}">{i_g} {growth:.2f}%</span></div>
            <div style="display:flex; justify-content: space-between;"><span>Var. Nacional:</span> <span class="{c_gn}">{i_gn} {growth_nac:.2f}%</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    num_trimestres = len(quarters_avail)
    trim_str = f"1T {max_year}" if num_trimestres <= 1 else f"1T-{num_trimestres}T {max_year}"
    return est_curr, part_nac, growth_est, growth_nac, rank, top1_name, trim_str

def get_ied_metrics(df_tot, state_norm):
    df_tot = df_tot.copy()
    df_tot['Estado_Norm'] = df_tot['Estado'].replace(NAME_NORMALIZER)
    try:
        max_year = int(df_tot['Anio'].max())
        max_trim = int(df_tot['Trimestre'].max())
        trim_str = f"{max_trim}T {max_year}"
    except: trim_str = "N/A"
    df_agg = df_tot.groupby('Estado_Norm')[['Inversion', 'Inversion_Anterior']].sum().reset_index()
    df_agg['Rank'] = df_agg['Inversion'].rank(ascending=False)
    nac_curr = df_agg['Inversion'].sum()
    nac_prev = df_agg['Inversion_Anterior'].sum()
    growth_nac = ((nac_curr - nac_prev)/nac_prev * 100) if nac_prev > 0 else 0
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
st.markdown("<hr style='border-color: #006A71; border-width: 2px;'>", unsafe_allow_html=True)
st.header("1. Resumen Ejecutivo")
st.markdown("<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: INEGI y Secretaría de Economía</div>", unsafe_allow_html=True)
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
# SECCIÓN 2: DETALLE IED
# ==========================================
st.markdown("<hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)
try:
    trim_ied = int(DATA['ied_tot']['Trimestre'].max())
    anio_ied = int(DATA['ied_tot']['Anio'].max())
    texto_periodo_ied = f"({trim_ied}T {anio_ied})"
except: texto_periodo_ied = ""

st.header(f"2. Inversión Extranjera Directa {texto_periodo_ied}")
st.markdown("<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: Secretaría de Economía</div>", unsafe_allow_html=True)
df_ied_det = DATA['ied_det']
df_ied_tot = DATA['ied_tot']

df_ied_st_det = df_ied_det[df_ied_det['Estado'].replace(NAME_NORMALIZER) == state_norm]
df_ied_st_tot = df_ied_tot[df_ied_tot['Estado'].replace(NAME_NORMALIZER) == state_norm]

if not df_ied_st_det.empty:
    def render_sector_block(sector_name, color_bar, bg_color):
        row_tot = df_ied_st_tot[df_ied_st_tot['Sector'] == sector_name]
        total_sector_val = row_tot['Inversion'].sum() if not row_tot.empty else 0.0
        subset = df_ied_st_det[df_ied_st_det['Sector'] == sector_name].sort_values('Inversion', ascending=False)
        subset = subset[subset['Inversion'] > 0]
        
        html_head = f"""<div style="border-left: 6px solid {color_bar}; padding: 15px 20px; margin-bottom: 20px; background-color: {bg_color}; border-radius: 0 12px 12px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
<div style="display:flex; justify-content:space-between; align-items:center;">
<h5 style="margin:0; color:#0F172A; font-weight:800; font-size:1.1rem;">{sector_name}</h5>
<span style="font-size:0.95rem; font-weight:800; color:{color_bar}; background:white; padding:4px 12px; border-radius:20px; border:1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
Total: ${total_sector_val:,.2f} MDD
</span>
</div>
<hr style="margin:12px 0; border-color:rgba(0,0,0,0.05);">"""
        st.markdown(html_head, unsafe_allow_html=True)
        
        if not subset.empty:
            for _, r in subset.iterrows():
                html_row = f"""<div style="display: flex; justify-content: space-between; font-size: 0.95rem; margin-bottom: 8px; color:#334155;">
<span style="font-weight: 500;">• {r['Actividad']}</span>
<span style="white-space: nowrap; font-weight:700; color:#0F172A;">${r['Inversion']:,.2f} MDD</span>
</div>"""
                st.markdown(html_row, unsafe_allow_html=True)
        else:
            st.caption("Sin inversión registrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Colores NAFIN/Financieros
    render_sector_block("Primaria", "#4C7273", "#F1F5F9")    # Verde Pizarra
    render_sector_block("Secundaria", "#006A71", "#E6F0F1")  # Teal NAFIN
    render_sector_block("Terciaria", "#D4A373", "#FDF8F3")   # Dorado NAFIN
    
    st.info("ℹ️ Nota: El monto de algunas actividades individuales puede superar al Total del Sector debido a desinversiones en otras actividades.")
else: st.info("No hay detalle de sectores de IED disponible.")

# ==========================================
# SECCIÓN 3: ESTRUCTURA ECONÓMICA
# ==========================================
st.markdown("<hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)

df_pib = DATA['pib']
max_period = df_pib['Periodo'].max()

st.header(f"3. Estructura Económica (PIB {max_period})")
st.markdown("<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: INEGI</div>", unsafe_allow_html=True)

df_curr = df_pib[(df_pib['Estado_ID'] == state_id) & (df_pib['Periodo'] == max_period)].copy()
df_nac = df_pib[(df_pib['Estado_ID'] == 0) & (df_pib['Periodo'] == max_period)].copy()

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

def get_val(df, indicador_name):
    row = df[df['Indicador'] == indicador_name]
    if row.empty: row = df[df['Indicador'].str.contains(indicador_name[:20], na=False, regex=False)]
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

pib_estatal_total = get_val(df_curr, "Total Nacional") 
val_prim_total = get_val(df_curr, HIERARCHY["Primario"]["Total"])
val_sec_total = get_val(df_curr, HIERARCHY["Secundario"]["Total"])
val_ter_total = get_val(df_curr, HIERARCHY["Terciario"]["Total"])
val_impuestos = pib_estatal_total - (val_prim_total + val_sec_total + val_ter_total)
pct_impuestos = (val_impuestos / pib_estatal_total * 100) if pib_estatal_total > 0 else 0

c1, c2, c3 = st.columns(3)

df_enoe_est = DATA['enoe'][DATA['enoe']['Estado'].replace(NAME_NORMALIZER) == state_norm]
tot_emp = 0
if not df_enoe_est.empty:
    tot_emp = (df_enoe_est['Sector Primario'] + df_enoe_est['Sector Secundario'] + df_enoe_est['Sector Terciario'] + df_enoe_est['No especificado']).values[0]

def render_sector_col(col, meta_key, color_hex, df_curr, df_nac, pib_estatal_total, tot_emp, df_enoe_est, enoe_key):
    meta = HIERARCHY[meta_key]
    val_est = get_val(df_curr, meta["Total"])
    val_nac_sec = get_val(df_nac, meta["Total"])
    part_nac = (val_est / val_nac_sec * 100) if val_nac_sec > 0 else 0
    part_estatal = (val_est / pib_estatal_total * 100) if pib_estatal_total > 0 else 0
    emp_part = (df_enoe_est[enoe_key].values[0] / tot_emp * 100) if not df_enoe_est.empty and tot_emp > 0 else 0

    col.markdown(f"""
    <div style="background: white; border-top: 5px solid {color_hex}; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 20px; height: 100%;">
        <div style="font-weight:800; color:{color_hex}; font-size:1rem; text-transform:uppercase; letter-spacing:0.5px;">SECTOR {meta_key.upper()}</div>
        <div style="font-size:1.8rem; font-weight:800; color:#0F172A; margin: 10px 0;">{format_mm_pesos(val_est)}</div>
        <div style="font-size:0.9rem; color:#475569; margin-bottom:4px;">🇲🇽 Part. Nacional: <b style="color:#0F172A;">{part_nac:.2f}%</b></div>
        <div style="font-size:0.9rem; color:#475569; margin-bottom:4px;">📍 Part. Estatal: <b style="color:#0F172A;">{part_estatal:.2f}%</b></div>
        <div style="font-size:0.9rem; color:#475569; margin-bottom:15px;">👷 <b style="color:#0F172A;">{emp_part:.2f}%</b> del Empleo Estatal</div>
        <hr style="border-color:#E2E8F0; margin:15px 0;">
        <div style="font-weight:700; color:#334155; margin-bottom:10px;">Composición Principal:</div>
    """, unsafe_allow_html=True)

    if meta_key == "Primario":
        sub_df = get_ranked_list(meta["Subsectores"], val_est)
        act_df = get_ranked_list(meta["Actividades"], val_est, top_n=3)
        for _, r in sub_df.iterrows():
            col.markdown(f"<div style='font-weight:600; font-size:0.95rem; color:#0F172A;'>• {r['Nombre']}</div><div style='color:#64748B; font-size:0.85rem; margin-bottom:8px;'>${r['Valor']/1000:,.2f} MM ({r['Share']:.1f}%)</div>", unsafe_allow_html=True)
            for _, act in act_df.iterrows():
                col.markdown(f"<div style='margin-left: 15px; font-size: 0.85rem; border-left: 2px solid {color_hex}; padding-left: 10px; margin-bottom: 6px; color:#475569;'><span>{act['Nombre']}</span> <br> <span style='font-weight:700; color:{color_hex};'>{act['Share']:.1f}%</span> del sector</div>", unsafe_allow_html=True)
    else:
        sub_df = get_ranked_list(meta["Subsectores"], val_est, top_n=3)
        for i, (_, r) in enumerate(sub_df.iterrows()):
            display_name = r['Nombre'][:37] + "..." if len(r['Nombre']) > 40 else r['Nombre']
            col.markdown(f"<div style='margin-bottom:12px;'><div style='font-weight:600; font-size:0.95rem; color:#0F172A;'>{i+1}. {display_name}</div><div style='color:#64748B; font-size:0.85rem;'>${r['Valor']/1000:,.2f} MM ({r['Share']:.1f}%)</div></div>", unsafe_allow_html=True)
            if meta_key == "Secundario" and "manufactureras" in r['Nombre'].lower():
                manuf_acts = get_ranked_list(meta["Manufactura_Actividades"], r['Valor'], top_n=3)
                for _, m_act in manuf_acts.iterrows():
                    col.markdown(f"<div style='margin-left: 15px; font-size: 0.85rem; border-left: 2px solid {color_hex}; padding-left: 10px; margin-bottom: 6px; color:#475569;'><span>{m_act['Nombre']}</span> <br> <span style='font-weight:700; color:{color_hex};'>{m_act['Share']:.1f}%</span> de manufactura</div>", unsafe_allow_html=True)
    
    col.markdown("</div>", unsafe_allow_html=True)

render_sector_col(c1, "Primario", "#4C7273", df_curr, df_nac, pib_estatal_total, tot_emp, df_enoe_est, 'Sector Primario')
render_sector_col(c2, "Secundario", "#006A71", df_curr, df_nac, pib_estatal_total, tot_emp, df_enoe_est, 'Sector Secundario')
render_sector_col(c3, "Terciario", "#D4A373", df_curr, df_nac, pib_estatal_total, tot_emp, df_enoe_est, 'Sector Terciario')

st.info(f"ℹ️ **Nota:** La suma del PIB sectorial no equivale al total, pues no considera impuestos, cuyo valor de **{val_impuestos/1000:.2f}** MMP representa el **{pct_impuestos:.2f}%** de la participación estatal.")

# ==========================================
# SECCIÓN 4: POBLACIÓN
# ==========================================
st.markdown("<hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)
try:
    anio_enoe = DATA['enoe']['Anio'].iloc[0]
    trim_str = str(DATA['enoe']['Trimestre'].iloc[0]).replace('trim', '')
    periodo_enoe = f"{trim_str}T {anio_enoe}"
except: periodo_enoe = ""

try: periodo_pob = DATA['pob']['Periodo'].max()
except: periodo_pob = ""

st.header("4. Demografía y Mercado Laboral")
st.markdown("<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: INEGI e IMSS</div>", unsafe_allow_html=True)

def render_custom_metric(label, value, sub_text, color="#0F172A"):
    st.markdown(f"""
    <div style="background-color: #ffffff; border: 1px solid #E2E8F0; padding: 18px; border-radius: 12px; margin-bottom: 12px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
        <div style="color: #64748B; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">{label}</div>
        <div style="color: {color}; font-size: 2rem; font-weight: 800; margin: 8px 0; letter-spacing: -0.5px;">{value}</div>
        <div style="color: #94A3B8; font-size: 0.85rem; font-weight: 500;">{sub_text}</div>
    </div>
    """, unsafe_allow_html=True)

col_metrics, col_chart = st.columns([1, 1])

df_enoe_est = DATA['enoe'][DATA['enoe']['Estado'].replace(NAME_NORMALIZER) == state_norm]
df_enoe_nac = DATA['enoe'][DATA['enoe']['Estado'] == 'Nacional']

if not df_enoe_est.empty and not df_enoe_nac.empty:
    rec_est = df_enoe_est.iloc[0]
    rec_nac = df_enoe_nac.iloc[0]
    
    est_pob, est_pea, est_des = rec_est['Poblacion Total'], rec_est['PEA'], rec_est['Desocupada']
    t_des_est = (est_des / est_pea * 100) if est_pea > 0 else 0
    t_inf_est = rec_est['Informalidad TIL1']
    des_sup_abs = rec_est.get('Educacion Sup', 0)
    t_des_sup = (des_sup_abs / est_des * 100) if est_des > 0 else 0
    edad_prom_est = rec_est.get('Edad Promedio PEA', 0) 

    nac_pob, nac_pea, nac_des = rec_nac['Poblacion Total'], rec_nac['PEA'], rec_nac['Desocupada']
    nac_des_sup_abs = rec_nac.get('Educacion Sup', 0)
    t_des_sup_nac = (nac_des_sup_abs / nac_des * 100) if nac_des > 0 else 0
    t_des_nac = (nac_des / nac_pea * 100) if nac_pea > 0 else 0
    t_inf_nac = rec_nac['Informalidad TIL1']
    edad_prom_nac = rec_nac.get('Edad Promedio PEA', 0)

    color_des = "#DC2626" if t_des_est > t_des_nac else "#059669"
    color_inf = "#DC2626" if t_inf_est > t_inf_nac else "#059669"
    color_des_sup = "#DC2626" if t_des_sup > t_des_sup_nac else "#059669"

    with col_metrics:
        st.markdown(f"<div style='text-align: left; color: #006A71; font-weight: 800; margin-bottom: 15px; font-size:1.1rem;'>Datos ENOE: {periodo_enoe}</div>", unsafe_allow_html=True)
        r1c1, r1c2 = st.columns(2)
        with r1c1: render_custom_metric("Población Total", f"{est_pob:,.0f}", f"{(est_pob/nac_pob*100):.2f}% del Nacional")
        with r1c2: render_custom_metric("PEA", f"{est_pea:,.0f}", f"{(est_pea/nac_pea*100):.2f}% del Nacional")
        
        r2c1, r2c2 = st.columns(2)
        with r2c1: render_custom_metric("Tasa Desocupación", f"{t_des_est:.2f}%", f"Nacional: {t_des_nac:.2f}%", color=color_des)
        with r2c2: render_custom_metric("Tasa Informalidad", f"{t_inf_est:.2f}%", f"Nacional: {t_inf_nac:.2f}%", color=color_inf)
        
        r3c1, r3c2 = st.columns(2)
        with r3c1: render_custom_metric("Desempleo Superior", f"{t_des_sup:.1f}%", f"Nacional: {t_des_sup_nac:.1f}%", color=color_des_sup)
        with r3c2: render_custom_metric("Edad Promedio PEA", f"{edad_prom_est:.1f} años", f"Nacional: {edad_prom_nac:.1f} años")

elif df_enoe_est.empty: st.warning(f"No se encontraron datos ENOE para: {state_norm}")
elif df_enoe_nac.empty: st.warning("No se encontró el registro 'Nacional' en ENOE.")

with col_chart:
    df_pob = DATA['pob']
    df_st = df_pob[df_pob['Estado_ID'].astype(int) == state_id].copy()
    
    if not df_st.empty:
        df_st['Rango_Exacto'] = df_st['Indicador'].str.replace(r' \(Hombres\)', '', regex=True).str.replace(r' \(Mujeres\)', '', regex=True)
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
        
        category_order = ['0 a 14 años', '15 a 24 años', '25 a 34 años', '35 a 44 años', '45 a 54 años', '55 a 64 años', '65 a 74 años', '75 años y más']
        grp = df_st.groupby(['Rango', 'Sexo'])['Valor'].sum().reset_index()
        total_pob_state = grp['Valor'].sum()
        
        grp['Valor_Plot'] = grp.apply(lambda x: -x['Valor'] if x['Sexo']=='Hombres' else x['Valor'], axis=1)
        grp['Porcentaje_Real'] = (grp['Valor'] / total_pob_state) * 100
        grp['Label_Text'] = grp.apply(lambda x: f"{x['Valor']/1000:.1f}k<br>({x['Porcentaje_Real']:.1f}%)", axis=1)

        fig = go.Figure()
        
        df_h = grp[grp['Sexo']=='Hombres']
        fig.add_trace(go.Bar(
            y=df_h['Rango'], x=df_h['Valor_Plot'], name='Hombres', orientation='h', 
            marker_color='#006A71', # Teal NAFIN
            text=df_h['Label_Text'], textposition='inside', insidetextanchor='middle',
            customdata=df_h[['Valor', 'Porcentaje_Real']],
            hovertemplate="<b>Hombres</b><br>Población: %{customdata[0]:,.0f}<br>Share: %{customdata[1]:.2f}%<extra></extra>"
        ))
        
        df_m = grp[grp['Sexo']=='Mujeres']
        fig.add_trace(go.Bar(
            y=df_m['Rango'], x=df_m['Valor_Plot'], name='Mujeres', orientation='h', 
            marker_color='#5CA4A9', # Teal Claro
            text=df_m['Label_Text'], textposition='inside', insidetextanchor='middle',
            customdata=df_m[['Valor', 'Porcentaje_Real']],
            hovertemplate="<b>Mujeres</b><br>Población: %{customdata[0]:,.0f}<br>Share: %{customdata[1]:.2f}%<extra></extra>"
        ))
        
        fig.update_layout(
            title=dict(text=f"Pirámide Poblacional ({periodo_pob})", font=dict(color='#0F172A', size=16, family="sans-serif"), x=0.5),
            barmode='overlay', bargap=0.15, 
            yaxis={'categoryorder':'array', 'categoryarray': category_order, 'tickfont': dict(color='#475569', size=12)}, 
            xaxis={'showticklabels':False, 'title': ''},
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, font=dict(color='#475569')),
            uniformtext_minsize=8, uniformtext_mode='hide',
            height=480, margin=dict(t=80, b=10, l=10, r=10),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4.5 GRÁFICAS HISTÓRICAS (IMSS)
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
col_hist_izq, col_hist_der = st.columns(2)

with col_hist_izq:
    df_pue = DATA['imss_pue'].copy()
    col_pue = next((c for c in df_pue.columns if NAME_NORMALIZER.get(c, c) == state_norm), None)
    
    if col_pue:
        df_pue[col_pue] = pd.to_numeric(df_pue[col_pue].astype(str).str.replace(',', '').str.replace(' ', ''), errors='coerce')
        meses_map = {'enero':1, 'febrero':2, 'marzo':3, 'abril':4, 'mayo':5, 'junio':6, 'julio':7, 'agosto':8, 'septiembre':9, 'octubre':10, 'noviembre':11, 'diciembre':12}
        df_pue['Mes_Num'] = df_pue['Mes'].str.lower().str.strip().map(meses_map)
        df_pue['Date'] = pd.to_datetime(df_pue['Año'].astype(str) + '-' + df_pue['Mes_Num'].astype(str).str.zfill(2) + '-01')
        df_pue = df_pue[df_pue['Año'] >= 2000].sort_values('Date').reset_index(drop=True)
        
        min_pue, max_pue = df_pue[col_pue].min(), df_pue[col_pue].max()
        
        # Algoritmo de pasos
        allowed_steps = [i * 10000 for i in range(1, 51)] + [i * 100000 for i in range(6, 51)]
        best_step = allowed_steps[0]
        best_diff = float('inf')
        for S in allowed_steps:
            temp_min = (min_pue // S) * S
            temp_max = ((max_pue // S) + 1) * S
            lines_count = int((temp_max - temp_min) / S) + 1
            diff = abs(lines_count - 6) # Target 6 lines
            if diff < best_diff: best_diff = diff; best_step = S
                
        y_min_pue = (min_pue // best_step) * best_step
        y_max_pue = ((max_pue // best_step) + 1) * best_step
        hitos_pue = list(range(int(y_min_pue), int(y_max_pue) + 1, best_step))
        
        val_curr = df_pue[col_pue].iloc[-1]
        val_prev_m = df_pue[col_pue].iloc[-2] if len(df_pue) > 1 else val_curr
        val_prev_y = df_pue[col_pue].iloc[-13] if len(df_pue) > 12 else val_curr
        var_m = (val_curr - val_prev_m) / val_prev_m * 100 if val_prev_m else 0
        var_y = (val_curr - val_prev_y) / val_prev_y * 100 if val_prev_y else 0
        fecha_str = f"{df_pue['Mes'].iloc[-1].capitalize()} {df_pue['Año'].iloc[-1]}"
        
        excluir_pue = ['Año', 'Mes', 'Date', 'Mes_Num', 'Nacional', 'Total', '(Todo)']
        state_cols_pue = [c for c in df_pue.columns if c not in excluir_pue]
        last_row_pue = pd.to_numeric(df_pue.iloc[-1][state_cols_pue].astype(str).str.replace(',', '').str.replace(' ', ''), errors='coerce')
        rk_pue = int(last_row_pue.rank(ascending=False, method='min')[col_pue])
        top1_pue = last_row_pue.idxmax()
        
        fig_pue = px.line(df_pue, x='Date', y=col_pue)
        fig_pue.update_traces(line_color='#006A71', line_width=3) # Teal NAFIN
        
        for hito in hitos_pue:
            fig_pue.add_hline(y=hito, line_color='#E2E8F0', line_width=1, layer='below')
            if df_pue[col_pue].iloc[0] < hito: 
                cruce = df_pue[df_pue[col_pue] >= hito]
                if not cruce.empty:
                    primer_cruce = cruce.iloc[0]
                    fig_pue.add_trace(go.Scatter(
                        x=[primer_cruce['Date']], y=[primer_cruce[col_pue]], mode='markers+text',
                        marker=dict(color='white', size=8, line=dict(color='#006A71', width=2)),
                        text=[f"{primer_cruce['Mes'][:3].capitalize()} {primer_cruce['Año']}"], textposition="top left",
                        textfont=dict(color="#006A71", size=10, weight="bold"), showlegend=False, hoverinfo='skip'
                    ))
        
        rank_html = f"Rank: <b>#{rk_pue}</b>" if rk_pue == 1 else f"Rank: <b>#{rk_pue}</b> <span style='font-size:10px; color:#94A3B8;'>(1º {top1_pue})</span>"
        color_m = '#059669' if var_m >=0 else '#DC2626'
        color_y = '#059669' if var_y >=0 else '#DC2626'
        
        html_box = f"<div style='background:white; border:1px solid #E2E8F0; border-radius:8px; padding:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05);'>" \
                   f"<div style='color:#64748B; font-size:11px; font-weight:bold; text-transform:uppercase;'>{fecha_str} | {rank_html}</div>" \
                   f"<div style='color:#0F172A; font-size:18px; font-weight:900;'>{val_curr:,.0f} <span style='font-size:12px; font-weight:normal; color:#475569;'>puestos</span></div>" \
                   f"<div style='font-size:11px; color:#475569;'>Var M: <span style='color:{color_m}; font-weight:bold;'>{var_m:+.2f}%</span> | Var A: <span style='color:{color_y}; font-weight:bold;'>{var_y:+.2f}%</span></div></div>"
        
        fig_pue.add_annotation(
            x=0.02, y=0.98, xref='paper', yref='paper', text=html_box, showarrow=False, align='left'
        )

        fig_pue.update_layout(
            title=dict(text="PUESTOS DE TRABAJO (IMSS)", font=dict(color='#0F172A', size=14, family="sans-serif", weight="bold"), x=0.0),
            xaxis_title="", yaxis_title="", height=400, margin=dict(t=50, b=20, l=10, r=10),
            xaxis=dict(showticklabels=True, tickformat="%Y", tickfont=dict(color='#64748B', size=11), showgrid=False, showline=False),
            yaxis=dict(range=[y_min_pue, y_max_pue], tickmode='array', tickvals=hitos_pue, showgrid=False, tickformat=",.0f", tickfont=dict(color='#94A3B8', size=11), showline=False, zeroline=False),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pue, use_container_width=True)

with col_hist_der:
    df_sal = DATA['imss_sal'].copy()
    col_sal = next((c for c in df_sal.columns if NAME_NORMALIZER.get(c, c) == state_norm), None)
    
    if col_sal:
        df_sal[col_sal] = pd.to_numeric(df_sal[col_sal].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('$', '', regex=False), errors='coerce')
        df_sal[['Mes_Str', 'Año']] = df_sal['Fecha'].str.split(' ', expand=True)
        meses_map = {'enero':1, 'febrero':2, 'marzo':3, 'abril':4, 'mayo':5, 'junio':6, 'julio':7, 'agosto':8, 'septiembre':9, 'octubre':10, 'noviembre':11, 'diciembre':12}
        df_sal['Mes_Num'] = df_sal['Mes_Str'].str.lower().str.strip().map(meses_map)
        df_sal['Date'] = pd.to_datetime(df_sal['Año'] + '-' + df_sal['Mes_Num'].astype(str).str.zfill(2) + '-01')
        df_sal = df_sal[df_sal['Date'].dt.year >= 2000].sort_values('Date').reset_index(drop=True)
        
        min_sal, max_sal = df_sal[col_sal].min(), df_sal[col_sal].max()
        y_min_sal = (min_sal // 100) * 100
        y_max_sal = ((max_sal // 100) + 1) * 100
        hitos_sal = list(range(int(y_min_sal), int(y_max_sal) + 1, 100))
        
        val_curr = df_sal[col_sal].iloc[-1]
        val_prev_m = df_sal[col_sal].iloc[-2] if len(df_sal) > 1 else val_curr
        val_prev_y = df_sal[col_sal].iloc[-13] if len(df_sal) > 12 else val_curr
        var_m = (val_curr - val_prev_m) / val_prev_m * 100 if val_prev_m else 0
        var_y = (val_curr - val_prev_y) / val_prev_y * 100 if val_prev_y else 0
        fecha_str = df_sal['Fecha'].iloc[-1].title()
        
        excluir_sal = ['Fecha', 'Año', 'Mes_Str', 'Mes_Num', 'Date', 'Nacional', 'Total', '(Todo)']
        state_cols_sal = [c for c in df_sal.columns if c not in excluir_sal]
        last_row_sal = pd.to_numeric(df_sal.iloc[-1][state_cols_sal].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('$', '', regex=False), errors='coerce')
        rk_sal = int(last_row_sal.rank(ascending=False, method='min')[col_sal])
        top1_sal = last_row_sal.idxmax()
        
        fig_sal = px.line(df_sal, x='Date', y=col_sal)
        fig_sal.update_traces(line_color='#D4A373', line_width=3) # Dorado NAFIN
        
        for hito in hitos_sal:
            fig_sal.add_hline(y=hito, line_color='#E2E8F0', line_width=1, layer='below')
            if df_sal[col_sal].iloc[0] < hito: 
                cruce = df_sal[df_sal[col_sal] >= hito]
                if not cruce.empty:
                    primer_cruce = cruce.iloc[0]
                    fig_sal.add_trace(go.Scatter(
                        x=[primer_cruce['Date']], y=[primer_cruce[col_sal]], mode='markers+text',
                        marker=dict(color='white', size=8, line=dict(color='#D4A373', width=2)),
                        text=[f"{primer_cruce['Mes_Str'][:3].capitalize()} {primer_cruce['Año']}"], textposition="top left",
                        textfont=dict(color="#D4A373", size=10, weight="bold"), showlegend=False, hoverinfo='skip'
                    ))

        rank_html_sal = f"Rank: <b>#{rk_sal}</b>" if rk_sal == 1 else f"Rank: <b>#{rk_sal}</b> <span style='font-size:10px; color:#94A3B8;'>(1º {top1_sal})</span>"
        color_m = '#059669' if var_m >=0 else '#DC2626'
        color_y = '#059669' if var_y >=0 else '#DC2626'
        
        html_box_sal = f"<div style='background:white; border:1px solid #E2E8F0; border-radius:8px; padding:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05);'>" \
                       f"<div style='color:#64748B; font-size:11px; font-weight:bold; text-transform:uppercase;'>{fecha_str} | {rank_html_sal}</div>" \
                       f"<div style='color:#0F172A; font-size:18px; font-weight:900;'>${val_curr:,.2f} <span style='font-size:12px; font-weight:normal; color:#475569;'>MXN</span></div>" \
                       f"<div style='font-size:11px; color:#475569;'>Var M: <span style='color:{color_m}; font-weight:bold;'>{var_m:+.2f}%</span> | Var A: <span style='color:{color_y}; font-weight:bold;'>{var_y:+.2f}%</span></div></div>"
        
        fig_sal.add_annotation(
            x=0.02, y=0.98, xref='paper', yref='paper', text=html_box_sal, showarrow=False, align='left'
        )

        fig_sal.update_layout(
            title=dict(text="SALARIO BASE COTIZACIÓN (IMSS)", font=dict(color='#0F172A', size=14, family="sans-serif", weight="bold"), x=0.0),
            xaxis_title="", yaxis_title="", height=400, margin=dict(t=50, b=20, l=10, r=10),
            xaxis=dict(showticklabels=True, tickformat="%Y", tickfont=dict(color='#64748B', size=11), showgrid=False, showline=False),
            yaxis=dict(range=[y_min_sal, y_max_sal], tickmode='array', tickvals=hitos_sal, showgrid=False, tickformat="$ ,.0f", tickfont=dict(color='#94A3B8', size=11), showline=False, zeroline=False),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_sal, use_container_width=True)

# ==========================================
# SECCIÓN 5: EDUCACIÓN
# ==========================================
st.markdown("<hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)

try:
    ciclo_edu = DATA['edu_tot']['Ciclo'].iloc[0]
    texto_ciclo = f" ({ciclo_edu})"
except: texto_ciclo = ""

st.header(f"5. Educación Superior{texto_ciclo}")
st.markdown("<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: ANUIES</div>", unsafe_allow_html=True)

try:
    df_tot, df_mat, df_egr = DATA['edu_tot'].copy(), DATA['edu_mat'].copy(), DATA['edu_egr'].copy()

    def clean_cols(df, cols):
        for col in cols:
            if col in df.columns and df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '').astype(float)
        return df

    df_tot = clean_cols(df_tot, ['Matrícula Total', 'Egresados Total'])
    df_mat = clean_cols(df_mat, ['Matrícula Total', 'Participacion_Matricula'])
    df_egr = clean_cols(df_egr, ['Egresados Total', 'Participacion_Egresados'])

    def clean_entidad(name): return NAME_NORMALIZER.get(str(name).strip().title(), str(name).strip().title())

    def get_edu_context(df_full, val_col, state_target, nivel=None, campo=None):
        df_f = df_full.copy()
        if nivel: df_f = df_f[df_f['Nivel_Agrupado'] == nivel]
        if campo: df_f = df_f[df_f['CAMPO AMPLIO'] == campo]
        df_f['ENTIDAD_NORM'] = df_f['ENTIDAD'].apply(clean_entidad)
        state_tgt_norm = clean_entidad(state_target)
        agg = df_f.groupby('ENTIDAD_NORM')[val_col].sum().reset_index()
        tot_nac = agg[val_col].sum()
        if tot_nac == 0 or agg.empty: return 0, 0, "-", 0
        agg['Rank'] = agg[val_col].rank(ascending=False, method='min')
        agg = agg.sort_values('Rank')
        top1 = agg.iloc[0]['ENTIDAD_NORM']
        st_row = agg[agg['ENTIDAD_NORM'].str.upper() == state_tgt_norm.upper()]
        if st_row.empty: return 0, 0, top1, 0
        return st_row.iloc[0][val_col], int(st_row.iloc[0]['Rank']), top1, (st_row.iloc[0][val_col] / tot_nac) * 100

    def main_stat_html(title, data_tuple, color_main):
        val, rank, top1, share = data_tuple
        return f"""<div style="min-width: 240px; flex-shrink: 0; padding-right: 20px; border-right: 1px solid #E2E8F0; margin-right: 10px; display: flex; flex-direction: column;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">
<div style="font-size:2.4rem; font-weight:900; color:{color_main}; line-height: 1.1; letter-spacing:-1px;">{val:,.0f}</div>
<div style="background-color: {color_main}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; margin-top: 5px;">#{rank}</div>
</div>
<div style="font-size:0.9rem; color:#64748B; text-transform: uppercase; font-weight:800; margin-bottom: 8px; margin-top: 5px; letter-spacing:0.5px;">{title}</div>
<div style="font-size:0.8rem; color:#475569;">
<div style="margin-bottom: 2px;"><b>#1 {top1}</b></div>
<div>Part. Nacional: <span style="font-weight:700; color:#0F172A;">{share:.1f}%</span></div>
</div>
</div>"""

    def sub_box_html(title, data_tuple, color_main):
        val, rank, top1, share = data_tuple
        return f"""<div style="background: white; padding: 15px; border-radius: 10px; border: 1px solid #E2E8F0; flex: 1; min-width: 140px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
<div>
<div style="display: flex; justify-content: space-between; align-items: flex-start;">
<div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 800; letter-spacing:0.5px;">{title}</div>
<div style="background-color: {color_main}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold;">#{rank}</div>
</div>
<div style="font-weight: 800; color: #0F172A; font-size: 1.4rem; margin-top: 5px;">{val:,.0f}</div>
</div>
<div style="font-size: 0.75rem; color: #475569; margin-top: 10px; border-top: 1px solid #F1F5F9; padding-top: 8px;">
<div style="margin-bottom: 2px;"><b>#1 {top1}</b></div>
<div>Part. Nac.: <span style="font-weight:700; color:#0F172A;">{share:.1f}%</span></div>
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

        html_general = f"""<div style="border-left: 6px solid #006A71; margin-bottom: 30px; background-color: #ffffff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border: 1px solid #E2E8F0;">
<h3 style="color:#0F172A; margin-top:0; margin-bottom:20px; font-weight:800;">Panorama General</h3>
<div style="display: flex; flex-direction: column; gap: 25px;">
<div style="display: flex; align-items: stretch; flex-wrap: nowrap; gap: 15px; border-bottom: 1px dashed #E2E8F0; padding-bottom: 20px; overflow-x: auto;">
{main_stat_html("Matrícula", ctx_mat_tot, "#006A71")}
{sub_box_html("Licenciatura", ctx_mat_lic, "#4C7273")}
{sub_box_html("Técnico Sup.", ctx_mat_tsu, "#4C7273")}
{sub_box_html("Maestría", ctx_mat_mae, "#4C7273")}
{sub_box_html("Doctorado", ctx_mat_doc, "#4C7273")}
</div>
<div style="display: flex; align-items: stretch; flex-wrap: nowrap; gap: 15px; overflow-x: auto;">
{main_stat_html("Egresados", ctx_egr_tot, "#D4A373")}
{sub_box_html("Licenciatura", ctx_egr_lic, "#D4A373")}
{sub_box_html("Técnico Sup.", ctx_egr_tsu, "#D4A373")}
{sub_box_html("Maestría", ctx_egr_mae, "#D4A373")}
{sub_box_html("Doctorado", ctx_egr_doc, "#D4A373")}
</div>
</div>
</div>"""
        st.markdown(html_general, unsafe_allow_html=True)

        st.markdown("<h4 style='color:#0F172A; font-weight:800;'>Principal Campo de Formación por Nivel</h4>", unsafe_allow_html=True)
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
            return f"""<div style="background: white; padding: 20px; border-radius: 12px; border-top: 4px solid {color_main}; box-shadow: 0 4px 10px rgba(0,0,0,0.03); border-left:1px solid #E2E8F0; border-right:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0; margin-bottom: 15px;">
<div style="display: flex; justify-content: space-between; align-items: flex-start;">
<div style="font-size:0.8rem; color:#64748B; font-weight:800; text-transform: uppercase; margin-bottom:8px; letter-spacing: 0.5px;">{nivel}</div>
<div style="background-color: {color_main}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;">#{rk_nac} Nacional</div>
</div>
<div style="font-weight:800; font-size:1.1rem; color:#0F172A; margin-bottom:15px; line-height: 1.3;">{campo}</div>
<div style="display:flex; justify-content:space-between; align-items:center; background: #F8FAFC; padding: 12px; border-radius: 8px; margin-bottom: 12px; border:1px solid #F1F5F9;">
<div style="text-align: center; width: 45%;">
<div style="color:{color_main}; font-weight:900; font-size:1.2rem;">{share_est:.1f}%</div>
<div style="font-size:0.75rem; color:#64748B; font-weight:600;">DEL ESTADO</div>
</div>
<div style="width: 1px; background: #E2E8F0; height: 35px;"></div>
<div style="text-align: center; width: 45%;">
<div style="color:#0F172A; font-weight:900; font-size:1.2rem;">{val_est:,.0f}</div>
<div style="font-size:0.75rem; color:#64748B; font-weight:600;">{label_val.upper()}</div>
</div>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; font-size: 0.8rem; color: #475569;">
<span><b>#1 {top1_nac}</b></span>
<span>Part. Nac.: <span style="font-weight:700; color:#0F172A;">{sh_nac:.1f}%</span></span>
</div>
</div>"""

        with col_mat:
            st.markdown(f"<div style='margin-bottom:15px; font-weight:800; color:#006A71; font-size:1.1rem;'>Por Matrícula</div>", unsafe_allow_html=True)
            for nivel in niveles_orden:
                campo, val, share = get_top1_by_level(df_top_mat_est, nivel, 'Matrícula Total', 'Participacion_Matricula')
                if campo: st.markdown(campo_card_html(nivel, campo, val, share, get_edu_context(df_mat, 'Matrícula Total', state_target, nivel, campo), "#006A71", "Alumnos"), unsafe_allow_html=True)

        with col_egr:
            st.markdown(f"<div style='margin-bottom:15px; font-weight:800; color:#D4A373; font-size:1.1rem;'>Por Egresados</div>", unsafe_allow_html=True)
            for nivel in niveles_orden:
                campo, val, share = get_top1_by_level(df_top_egr_est, nivel, 'Egresados Total', 'Participacion_Egresados')
                if campo: st.markdown(campo_card_html(nivel, campo, val, share, get_edu_context(df_egr, 'Egresados Total', state_target, nivel, campo), "#D4A373", "Egresados"), unsafe_allow_html=True)

except Exception as e: st.error(f"Error procesando educación: {str(e)}")

# ==========================================
# SECCIÓN 6: PRODUCTIVIDAD
# ==========================================
st.markdown("<hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)

df_saic = DATA['saic'].copy() 
try:
    anio_saic = df_saic['Anio_Censal'].iloc[0]
    texto_anio_saic = f" ({anio_saic})"
except: texto_anio_saic = ""

st.header(f"6. Productividad Laboral{texto_anio_saic}")
st.markdown("<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: Censos Económicos (INEGI)</div>", unsafe_allow_html=True)

df_saic['Entidad_Norm'] = df_saic['Entidad'].str.strip().replace(NAME_NORMALIZER)
df_saic['Rank'] = df_saic['Indicador_Productividad'].rank(ascending=False)
row = df_saic[df_saic['Entidad_Norm'] == state_norm]

if not row.empty:
    val, rk, nombre_estado = row['Indicador_Productividad'].values[0], int(row['Rank'].values[0]), row['Entidad'].values[0]
    top1 = df_saic.sort_values('Indicador_Productividad', ascending=False).iloc[0]
    avg = df_saic['Indicador_Productividad'].mean()
    val_color = "#059669" if val > avg else "#DC2626"
    
    card_html = """
    <div style="background-color: white; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); height:100%;">
        <p style="margin: 0; font-size: 0.85rem; color: #64748B; font-weight: 700; text-transform:uppercase; letter-spacing:0.5px;">{title}</p>
        <p style="margin: 8px 0 0 0; font-size: 1.8rem; font-weight: 800; color: {color_val};">{value}</p>
    </div>
    """
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(card_html.format(title="Posición Nacional", value=f"#{rk}", color_val="#0F172A"), unsafe_allow_html=True)
    c2.markdown(card_html.format(title=nombre_estado, value=f"{val:,.2f}", color_val=val_color), unsafe_allow_html=True)
    c3.markdown(card_html.format(title="Promedio Nacional", value=f"{avg:,.2f}", color_val="#0F172A"), unsafe_allow_html=True)
    c4.markdown(card_html.format(title=f"1er Lugar ({top1['Entidad']})", value=f"{top1['Indicador_Productividad']:,.2f}", color_val="#0F172A"), unsafe_allow_html=True)
    
    df_sorted = df_saic.sort_values('Indicador_Productividad', ascending=False).reset_index(drop=True)
    colors = ['#006A71' if x == state_norm else '#CBD5E1' for x in df_sorted['Entidad_Norm']] # Teal NAFIN vs Gray
    
    fig = px.bar(df_sorted, x='Entidad', y='Indicador_Productividad')
    fig.update_traces(marker_color=colors, hovertemplate="%{y:,.2f}<extra></extra>")
    fig.add_hline(y=avg, line_dash="dash", line_color="#475569", annotation_text="Promedio Nacional", annotation_font_color="#475569")
    fig.add_annotation(
        x=0.99, y=0.95, xref='paper', yref='paper', text="Indicador = Producción Bruta / Personal Ocupado", 
        showarrow=False, align='right', bgcolor='rgba(255, 255, 255, 0.95)', bordercolor='#E2E8F0', borderwidth=1, borderpad=8, font=dict(color='#475569', size=11)
    )
    fig.update_layout(yaxis_title="Productividad", xaxis_title="", xaxis_tickangle=-90, margin=dict(t=30, b=0, l=0, r=0), showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# SECCIÓN 7: IMCO
# ==========================================
st.markdown("<hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)

df_g = DATA['imco_g'].copy()
try:
    col_anio_candidatas = [c for c in df_g.columns if str(c).strip().upper().startswith('A') and str(c).strip().lower().endswith('o')]
    col_anio = col_anio_candidatas[0] if col_anio_candidatas else 'AÃ±o'
    val_bruto = str(df_g[col_anio].iloc[0]).strip()
    if '/' in val_bruto: anio_imco = val_bruto.split('/')[-1]
    elif '-' in val_bruto: anio_imco = val_bruto.split('-')[0]
    else: anio_imco = val_bruto
    texto_anio_imco = f" ({anio_imco})"
except: texto_anio_imco = ""

st.header(f"7. Competitividad{texto_anio_imco}")
st.markdown("<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: IMCO</div>", unsafe_allow_html=True)

df_g['Entidad_Norm'] = df_g['Entidad'].str.strip().replace(NAME_NORMALIZER)
row = df_g[df_g['Entidad_Norm'] == state_norm]

if not row.empty:
    val, rk, nombre_estado = row['Valor'].values[0], int(row['Ranking'].values[0]), row['Entidad'].values[0]
    top1 = df_g.sort_values('Valor', ascending=False).iloc[0]
    avg = df_g['Valor'].mean()
    
    card_html = """
    <div style="background-color: white; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); height:100%;">
        <p style="margin: 0; font-size: 0.85rem; color: #64748B; font-weight: 700; text-transform:uppercase; letter-spacing:0.5px;">{title}</p>
        <p style="margin: 8px 0 0 0; font-size: 1.8rem; font-weight: 800; color: #0F172A;">{value}</p>
    </div>
    """
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(card_html.format(title="Posición", value=f"#{rk}"), unsafe_allow_html=True)
    c2.markdown(card_html.format(title=nombre_estado, value=f"{val:.2f}"), unsafe_allow_html=True)
    c3.markdown(card_html.format(title="Promedio Nacional", value=f"{avg:.2f}"), unsafe_allow_html=True)
    c4.markdown(card_html.format(title=f"1er Lugar ({top1['Entidad']})", value=f"{top1['Valor']:.2f}"), unsafe_allow_html=True)
    
    df_sorted = df_g.sort_values('Valor', ascending=False).reset_index(drop=True)
    colors = ['#006A71' if x == state_norm else '#CBD5E1' for x in df_sorted['Entidad_Norm']]
    
    fig = px.bar(df_sorted, x='Entidad', y='Valor')
    fig.update_traces(marker_color=colors, hovertemplate="%{y:,.2f}<extra></extra>")
    fig.add_hline(y=avg, line_dash="dash", line_color="#475569", annotation_text="Promedio Nacional", annotation_font_color="#475569")
    fig.update_layout(yaxis_title="Competitividad", xaxis_title="", xaxis_tickangle=-90, margin=dict(t=30, b=0, l=0, r=0), showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

df_d = DATA['imco_d'].copy()
df_d['Entidad_Norm'] = df_d['Entidad'].str.strip().replace(NAME_NORMALIZER)
st_d = df_d[df_d['Entidad_Norm'] == state_norm].copy()

INDICADORES_IGNORADOS = ["Acceso a internet"]
CORRECCION_NOMBRES = {"Perc. de corrupción estatal": "Percepción de corrupción estatal"}

if not st_d.empty:
    st_d = st_d[~st_d['Indicador'].isin(INDICADORES_IGNORADOS)].copy()
    st_d['Indicador'] = st_d['Indicador'].replace(CORRECCION_NOMBRES)

    TIPO_INDICADOR = {"Acceso a instituciones de salud": "Directo", "Camas de hospital": "Directo", "Captación de ahorro": "Directo", "Carga aérea": "Directo", "Cobertura educativa": "Directo", "Competencia en servicios notariales": "Directo", "Consulta info finanzas públicas": "Directo", "Crecimiento de UE >50 empleados": "Directo", "Crecimiento del PIB": "Directo", "Crecimiento puestos de trabajo (IMSS)": "Directo", "Diversificación económica": "Directo", "Esperanza de vida": "Directo", "Flujo de pasajeros aéreos": "Directo", "Grado de escolaridad": "Directo", "Ingreso promedio de tiempo completo": "Directo", "Ingresos propios": "Directo", "Mujeres económicamente activas": "Directo", "Participación ciudadana en elecciones": "Directo", "Patentes": "Directo", "Percepción de seguridad": "Directo", "Personal médico con especialidad": "Directo", "Personal médico y de enfermería": "Directo", "Población con educación superior": "Directo", "Tasa de participación": "Directo", "Terminales punto de venta": "Directo", "Uso de banca móvil": "Directo", "Agresiones a periodistas": "Inverso", "Brecha de ingresos por género": "Inverso", "Costo promedio de la deuda": "Inverso", "Delitos no denunciados": "Inverso", "Desigualdad salarial": "Inverso", "Deuda estatal y organismos": "Inverso", "Diferencia de informalidad laboral H-M": "Inverso", "Heridos en accidentes de tránsito terrestre": "Inverso", "Homicidios": "Inverso", "Incidencia delictiva": "Inverso", "Informalidad laboral": "Inverso", "Jornadas laborales >48h": "Inverso", "Morbilidad respiratoria": "Inverso", "Percepción de corrupción estatal": "Inverso", "Personas con ingresos debajo de la línea de bienestar": "Inverso", "Robo de vehículos": "Inverso"}

    def calc_puntaje(row): return row['Rank'] if TIPO_INDICADOR.get(str(row['Indicador']).strip(), "Directo") == "Directo" else 33 - row['Rank']
    def calc_cambio(row): return row['Cambio_Posicion'] if TIPO_INDICADOR.get(str(row['Indicador']).strip(), "Directo") == "Directo" else -row['Cambio_Posicion']

    st_d['Puntaje_Fortaleza'] = st_d.apply(calc_puntaje, axis=1)
    st_d['Cambio_Ajustado'] = st_d.apply(calc_cambio, axis=1)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    def badge_html(ch):
        if ch > 0: return f"<span style='background-color:#059669; color:white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight:bold; margin-left:8px;'>▲ {int(abs(ch))}</span>"
        elif ch < 0: return f"<span style='background-color:#DC2626; color:white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight:bold; margin-left:8px;'>▼ {int(abs(ch))}</span>"
        else: return f"<span style='background-color:#64748B; color:white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight:bold; margin-left:8px;'>=</span>"

    with c1:
        st.markdown("<div style='background:white; padding:20px; border-radius:12px; border-top:4px solid #006A71; box-shadow: 0 4px 6px rgba(0,0,0,0.02);'><h4 style='color:#0F172A; margin-top:0;'>✅ Top 5 Fortalezas</h4>", unsafe_allow_html=True)
        for _, r in st_d.sort_values('Puntaje_Fortaleza').head(5).iterrows():
            st.markdown(f"<div style='padding:8px 0; border-bottom:1px solid #F1F5F9; color:#334155;'><b style='color:#0F172A;'>#{int(r['Rank'])}</b> {r['Indicador']} {badge_html(r['Cambio_Ajustado'])}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:white; padding:20px; border-radius:12px; border-top:4px solid #D4A373; box-shadow: 0 4px 6px rgba(0,0,0,0.02);'><h4 style='color:#0F172A; margin-top:0;'>⚠️ Top 5 Áreas de oportunidad</h4>", unsafe_allow_html=True)
        for _, r in st_d.sort_values('Puntaje_Fortaleza', ascending=False).head(5).iterrows():
            st.markdown(f"<div style='padding:8px 0; border-bottom:1px solid #F1F5F9; color:#334155;'><b style='color:#0F172A;'>#{int(r['Rank'])}</b> {r['Indicador']} {badge_html(r['Cambio_Ajustado'])}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
            
    st.info("ℹ️ **Nota:** El cambio de posiciones corresponde a la variación respecto al año anterior.")

# ==========================================
# SECCIÓN 8: RATINGS
# ==========================================
if "Tlaxcala" not in selected_name:
    st.markdown("<hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)
    st.header("8. Calificación Crediticia")
    
    df_r = DATA['ratings']
    match = pd.DataFrame()
    fuente_str = "HR Ratings y/o Fitch Ratings"
    
    if not df_r.empty:
        col_ent = [c for c in df_r.columns if "Entidad" in c][0]
        match = df_r[df_r[col_ent].astype(str).apply(lambda x: NAME_NORMALIZER.get(x, x)) == state_norm].copy()
        if not match.empty:
            agencias = match['Calificadora'].astype(str).unique()
            if any("HR" in ag for ag in agencias) and any("Fitch" in ag for ag in agencias): fuente_str = "HR Ratings y Fitch Ratings"
            elif any("Fitch" in ag for ag in agencias): fuente_str = "Fitch Ratings"
            elif any("HR" in ag for ag in agencias): fuente_str = "HR Ratings"
    
    st.markdown(f"<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: {fuente_str}</div>", unsafe_allow_html=True)
    
    if not match.empty:
        match = match.rename(columns={"Fecha Publicacion": "Fecha de Publicación", "Fecha de Publicacion": "Fecha de Publicación", "Fecha Publicación": "Fecha de Publicación", "Calificacion": "Calificación", "Descripcion": "Descripción"})
        columnas_deseadas = ["Calificadora", "Calificación", "Perspectiva", "Descripción", "Fecha de Publicación"]
        columnas_finales = [c for c in columnas_deseadas if c in match.columns]
        st.dataframe(match[columnas_finales], hide_index=True, use_container_width=True)
    elif not df_r.empty: st.info("Sin calificación.")
    else: st.info("Archivo no disponible.")

# ==========================================
# SECCIÓN 9: TOP EXPORTACIONES
# ==========================================
st.markdown("<hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)
num_seccion = "8" if "Tlaxcala" in selected_name else "9"
st.header(f"{num_seccion}. Principales Sectores de Exportación")
st.markdown("<div style='font-size: 0.8rem; color: #94A3B8; margin-top: -15px; margin-bottom: 20px;'>Fuente: INEGI</div>", unsafe_allow_html=True)

df_e = DATA['export'].copy()
df_e['Year'] = df_e['Periodo'].astype(str).str[:4].astype(int)
df_e['Quarter'] = df_e['Periodo'].astype(str).str[-2:]
max_y = df_e['Year'].max()
quarters_avail = df_e[df_e['Year'] == max_y]['Quarter'].unique()

st_e_curr = df_e[(df_e['Estado_ID'].astype(str).str.zfill(2) == state_id_str) & (df_e['Year'] == max_y) & (df_e['Sector'] != 'Total')]
st_e_prev = df_e[(df_e['Estado_ID'].astype(str).str.zfill(2) == state_id_str) & (df_e['Year'] == (max_y - 1)) & (df_e['Quarter'].isin(quarters_avail)) & (df_e['Sector'] != 'Total')]

if not st_e_curr.empty:
    top10 = st_e_curr.groupby('Sector')['Valor'].sum().reset_index().sort_values('Valor', ascending=False).head(10)
    tot_curr = top10['Valor'].sum()
    top10['Part'] = (top10['Valor']/tot_curr*100) if tot_curr > 0 else 0
    
    if not st_e_prev.empty:
        prev_agg = st_e_prev.groupby('Sector')['Valor'].sum().reset_index().rename(columns={'Valor': 'Valor_Prev'})
        top10 = top10.merge(prev_agg, on='Sector', how='left')
    else: top10['Valor_Prev'] = 0
    top10['Valor_Prev'] = top10['Valor_Prev'].fillna(0)
    
    nac_curr_agg = df_e[(df_e['Year'] == max_y) & (df_e['Sector'] != 'Total')].groupby(['Sector', 'Estado_ID'])['Valor'].sum().reset_index()
    rks = []
    for s in top10['Sector']:
        d_s = nac_curr_agg[nac_curr_agg['Sector'] == s].copy()
        d_s['Rank'] = d_s['Valor'].rank(ascending=False)
        try: rks.append(int(d_s[d_s['Estado_ID'].astype(str).str.zfill(2) == state_id_str]['Rank'].values[0]))
        except: rks.append("-")
    top10['Rank Nac'] = rks

    max_val_scale = max(top10['Valor'].max(), top10['Valor_Prev'].max())
    q_len = len(quarters_avail)
    q_prefix = f"1T-{q_len}T" if q_len > 1 else "1T"
    label_curr = f"{q_prefix} {max_y}"
    label_prev = f"{q_prefix} {max_y - 1}"
    
    html_export = f"""<div style="background-color: white; padding:25px; border-radius:12px; border:1px solid #E2E8F0; box-shadow: 0 4px 15px rgba(0,0,0,0.03); width: 100%; font-family: sans-serif; color: #334155;">
<div style="display: flex; justify-content: flex-start; margin-bottom:20px; font-size: 0.85rem; color: #475569; font-weight:600;">
<div style="display:flex; align-items:center; margin-right:20px;"><div style="width:14px; height:14px; background-color:#006A71; margin-right:6px; border-radius:3px;"></div> {label_curr}</div>
<div style="display:flex; align-items:center;"><div style="width:14px; height:14px; background-color:#CBD5E1; margin-right:6px; border-radius:3px;"></div> {label_prev}</div>
</div>
<div style="display: flex; width: 100%; margin-bottom: 20px; font-weight: 800; text-align: center; font-size: 0.85rem; text-transform:uppercase; letter-spacing:0.5px; justify-content: flex-start; gap: 15px; color: #64748B; border-bottom:2px solid #F1F5F9; padding-bottom:10px;">
<div style="width: 25%; text-align: left; padding-left: 5px;">Sector</div>
<div style="width: 40%; text-align: left; padding-left: 0px;">Millones de Dólares</div>
<div style="width: 120px;">% Estatal</div>
<div style="width: 120px;">Rank Nacional</div>
</div>"""
    
    for _, r in top10.iterrows():
        pct_curr = max((r['Valor'] / max_val_scale) * 100 if max_val_scale > 0 else 0, 0.5)
        pct_prev = max((r['Valor_Prev'] / max_val_scale) * 100 if max_val_scale > 0 else 0, 0.5)
        sector_wrapped = '<br>'.join(textwrap.wrap(r['Sector'], width=38))
        
        html_export += f"""<div style="display: flex; width: 100%; align-items: stretch; margin-bottom: 18px; justify-content: flex-start; gap: 15px;">
<div style="width: 25%; text-align: left; padding-left: 5px; font-size: 0.85rem; display: flex; align-items: center; justify-content: flex-start;">
<span style="display: inline-block; line-height: 1.3; color: #0F172A; font-weight: 600;">{sector_wrapped}</span>
</div>
<div style="width: 40%; border-left: 2px solid #E2E8F0; padding-left: 15px; display: flex; flex-direction: column; justify-content: center; gap: 8px;">
<div style="display:flex; align-items:center; width: 100%;">
<div style="background-color: #006A71; width: {pct_curr}%; height: 20px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>
<span style="margin-left: 10px; font-weight: 800; font-size: 0.95rem; color: #0F172A;">{r['Valor'] / 1000:,.0f}</span>
</div>
<div style="display:flex; align-items:center; width: 100%;">
<div style="background-color: #CBD5E1; width: {pct_prev}%; height: 12px; border-radius: 4px;"></div>
<span style="margin-left: 10px; font-weight: 600; font-size: 0.8rem; color: #64748B;">{r['Valor_Prev'] / 1000:,.0f}</span>
</div>
</div>
<div style="width: 120px; display: flex; justify-content: center; align-items: center;">
<div style="background-color: #F8FAFC; border:1px solid #E2E8F0; border-radius: 8px; padding: 6px 0; width: 100%; font-weight: 800; font-size: 0.95rem; color: #006A71; text-align: center;">
{r['Part']:.1f}%
</div>
</div>
<div style="width: 120px; display: flex; justify-content: center; align-items: center;">
<div style="background-color: #F8FAFC; border:1px solid #E2E8F0; border-radius: 8px; padding: 6px 0; width: 100%; font-weight: 800; font-size: 0.95rem; color: #0F172A; text-align: center;">
#{r['Rank Nac']}
</div>
</div>
</div>"""
        
    html_export += "</div>"
    st.markdown(html_export, unsafe_allow_html=True)