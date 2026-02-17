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
st.markdown("---")

# ==========================================
# 5. FUNCIONES LÓGICAS
# ==========================================

def format_mm_pesos(val_millones):
    val = val_millones / 1000
    return f"${val:,.2f} <span style='font-size: 0.5em;'>MM MXN</span>"

def format_mm_usd(val_miles): 
    val = val_miles / 1000000 
    return f"${val:,.2f} <span style='font-size: 0.5em;'>MM USD</span>"

def format_mm_usd_ied(val_millones): 
    return f"${val_millones:,.2f} <span style='font-size: 0.5em;'>MM USD</span>"

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
        <div class="metric-sub" style="white-space: nowrap;">
            <b style="line-height: 1.2;">Variación:</b><br>
            Estatal: <span class="{c_g}">{i_g} {growth:.2f}%</span>
            <span style="color:#ccc">|</span> Nacional: <span class="{c_gn}">{i_gn} {growth_nac:.2f}%</span>
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
    
    return est_curr, part_nac, growth_est, growth_nac, rank, top1

# ==========================================
# SECCIÓN 1: RESUMEN EJECUTIVO
# ==========================================

st.header("1. Resumen Ejecutivo")
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
        render_card(f"PIB Manufacturero ({yr})", format_mm_pesos(v), r, t1, p, g, gn)
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
        v, p, g, gn, r, t1 = res
        # Se pone manual ya que el CSV de totales IED no guarda el periodo
        render_card("IED (3T 2025)", format_mm_usd_ied(v), r, t1, p, g, gn)
    else: st.warning("Sin datos IED")

# ==========================================
# SECCIÓN 1.5: DETALLE IED (VERTICAL)
# ==========================================
st.markdown("###### Principales Sectores de Inversión 3T 2025")
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
        
        # 2. Obtener Actividades (Top)
        subset = df_ied_st_det[df_ied_st_det['Sector'] == sector_name].sort_values('Inversion', ascending=False)
        
        st.markdown(f"""
        <div style="border-left: 5px solid {color_bar}; padding-left: 15px; margin-bottom: 20px; background-color: #f8f9fa; padding-top: 10px; padding-bottom: 10px; border-radius: 0 5px 5px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h5 style="margin:0; color:#333;">{sector_name}</h5>
                <span style="font-size:0.9rem; font-weight:700; color:{color_bar}; background:white; padding:2px 8px; border-radius:4px; border:1px solid #ddd;">
                    Total: ${total_sector_val:,.2f} M
                </span>
            </div>
            <hr style="margin:5px 0 10px 0; border-color:#e9ecef;">
        """, unsafe_allow_html=True)
        
        if not subset.empty:
            for _, r in subset.iterrows():
                # Formato: Nombre ... $M (Sin porcentaje)
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px;">
                    <span style="font-weight: 500;">• {r['Actividad']}</span>
                    <span style="white-space: nowrap; font-weight:600;">
                        ${r['Inversion']:,.2f} M
                    </span>
                </div>
                """, unsafe_allow_html=True)
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
# SECCIÓN 2: ESTRUCTURA ECONÓMICA
# ==========================================
st.markdown("---")
st.header("2. Estructura Económica")

# --- PREPARACIÓN DE DATOS ---
df_pib = DATA['pib']
max_period = df_pib['Periodo'].max()

# 1. Datos Estatales (df_curr)
df_curr = df_pib[(df_pib['Estado_ID'] == state_id) & (df_pib['Periodo'] == max_period)].copy()

# 2. Datos Nacionales (df_nac) - Para calcular participaciones correctas
df_nac = df_pib[(df_pib['Estado_ID'] == 0) & (df_pib['Periodo'] == max_period)].copy()

# Definición de Jerarquías (Mantenemos tu estructura)
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
    
    # Participación en el PIB Nacional del Sector
    part_nac = (val_est / val_nac_sec * 100) if val_nac_sec > 0 else 0
    
    # Empleo
    emp_part = 0
    if not df_enoe_est.empty and tot_emp > 0:
        emp_part = (df_enoe_est['Sector Primario'].values[0] / tot_emp * 100)

    st.markdown(f"""
    <div style="border-left: 4px solid #28a745; padding-left: 12px; margin-bottom: 15px;">
        <div style="font-weight:700; color:#555;">SECTOR PRIMARIO</div>
        <div style="font-size:1.4rem; font-weight:800;">{format_mm_pesos(val_est)}</div>
        <div style="font-size:0.85rem;">📊 Part. Nacional: <b>{part_nac:.2f}%</b></div>
        <div style="font-size:0.85rem;">👷 <b>{emp_part:.2f}%</b> del Empleo Estatal</div>
    </div>
    """, unsafe_allow_html=True)

    sub_df = get_ranked_list(meta["Subsectores"], val_est)
    act_df = get_ranked_list(meta["Actividades"], val_est, top_n=3)
    
    st.markdown("**Estructura:**")
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
    
    emp_part = 0
    if not df_enoe_est.empty and tot_emp > 0:
        emp_part = (df_enoe_est['Sector Secundario'].values[0] / tot_emp * 100)

    st.markdown(f"""
    <div style="border-left: 4px solid #007bff; padding-left: 12px; margin-bottom: 15px;">
        <div style="font-weight:700; color:#555;">SECTOR SECUNDARIO</div>
        <div style="font-size:1.4rem; font-weight:800;">{format_mm_pesos(val_est)}</div>
        <div style="font-size:0.85rem;">📊 Part. Nacional: <b>{part_nac:.2f}%</b></div>
        <div style="font-size:0.85rem;">👷 <b>{emp_part:.2f}%</b> del Empleo Estatal</div>
    </div>
    """, unsafe_allow_html=True)

    sub_df = get_ranked_list(meta["Subsectores"], val_est, top_n=3)
    st.markdown("**Principales Subsectores (Top 3):**")
    for _, r in sub_df.iterrows():
        is_manuf = "manufactureras" in r['Nombre'].lower()
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <div style="font-weight:600; font-size:0.95rem;">• {r['Nombre']}</div>
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
    
    emp_part = 0
    if not df_enoe_est.empty and tot_emp > 0:
        emp_part = (df_enoe_est['Sector Terciario'].values[0] / tot_emp * 100)

    st.markdown(f"""
    <div style="border-left: 4px solid #fd7e14; padding-left: 12px; margin-bottom: 15px;">
        <div style="font-weight:700; color:#555;">SECTOR TERCIARIO</div>
        <div style="font-size:1.4rem; font-weight:800;">{format_mm_pesos(val_est)}</div>
        <div style="font-size:0.85rem;">📊 Part. Nacional: <b>{part_nac:.2f}%</b></div>
        <div style="font-size:0.85rem;">👷 <b>{emp_part:.2f}%</b> del Empleo Estatal</div>
    </div>
    """, unsafe_allow_html=True)

    sub_df = get_ranked_list(meta["Subsectores"], val_est, top_n=3)
    st.markdown("**Principales Subsectores (Top 3):**")
    for _, r in sub_df.iterrows():
        display_name = r['Nombre'][:37] + "..." if len(r['Nombre']) > 40 else r['Nombre']
        st.markdown(f"""
        <div style="margin-bottom:8px;">
            <div style="font-weight:600; font-size:0.95rem;">• {display_name}</div>
            <div style="color:#666; font-size:0.85rem; margin-left:15px;">${r['Valor']/1000:,.2f} MM ({r['Share']:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# SECCIÓN 3: POBLACIÓN
# ==========================================
st.markdown("---")
st.header("3. Demografía y Mercado Laboral")

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
    
    # Tasas Nacionales (Calculadas con los datos del registro Nacional)
    t_des_nac = (nac_des / nac_pea * 100) if nac_pea > 0 else 0
    t_inf_nac = rec_nac['Informalidad TIL1'] # Dato directo
    edad_prom_nac = rec_nac.get('Edad Promedio PEA', 0) # Dato directo

    # --- LÓGICA DE COLORES ---
    # Rojo (#dc3545) si es mayor al nacional, Verde (#28a745) si es menor.
    color_des = "#dc3545" if t_des_est > t_des_nac else "#28a745"
    color_inf = "#dc3545" if t_inf_est > t_inf_nac else "#28a745"

    # --- RENDERIZADO DE MÉTRICAS (6 Cuadros) ---
    with col_metrics:
        # Fila 1: Población y PEA (Neutros)
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
        
        # Fila 3: Desempleo Superior y Edad Promedio (Neutros)
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            render_custom_metric(
                "Desempleo Nivel Sup.", 
                f"{t_des_sup:.1f}%", 
                f"{des_sup_abs:,.0f} Personas"
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
            marker_color='#1f77b4',
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
            marker_color='#e377c2',
            text=df_m['Label_Text'],      # Texto visible
            textposition='inside',        # Posición dentro de la barra
            insidetextanchor='middle',
            customdata=df_m[['Valor', 'Porcentaje_Real']],
            hovertemplate="<b>Mujeres</b><br>Población: %{customdata[0]:,.0f}<br>Share: %{customdata[1]:.2f}%<extra></extra>"
        ))
        
        fig.update_layout(
            title="Pirámide Poblacional", 
            barmode='overlay', 
            bargap=0.1, 
            # Reemplazamos la lista estática por la lista ordenada de forma estricta
            yaxis={'categoryorder':'array', 'categoryarray': category_order}, 
            xaxis={'showticklabels':False, 'title': '% respecto al total poblacional'},
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            uniformtext_minsize=8, 
            uniformtext_mode='hide'
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# SECCIÓN 4: EDUCACIÓN
# ==========================================
st.markdown("---")
st.header("4. Educación Superior")

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

    state_target = state_norm.upper()

    df_tot_est = df_tot[df_tot['ENTIDAD'].str.upper() == state_target]
    df_top_mat = df_mat[df_mat['ENTIDAD'].str.upper() == state_target]
    df_top_egr = df_egr[df_egr['ENTIDAD'].str.upper() == state_target]

    if not df_tot_est.empty:
        total_alum = df_tot_est['Matrícula Total'].sum()
        total_egresados = df_tot_est['Egresados Total'].sum()

        def get_nivel_val(df, nivel, col):
            val = df[df['Nivel_Agrupado'] == nivel][col]
            return val.values[0] if not val.empty else 0

        mat_lic = get_nivel_val(df_tot_est, 'Licenciatura', 'Matrícula Total')
        mat_tsu = get_nivel_val(df_tot_est, 'Técnico Superior', 'Matrícula Total')
        mat_mae = get_nivel_val(df_tot_est, 'Maestría', 'Matrícula Total')
        mat_doc = get_nivel_val(df_tot_est, 'Doctorado', 'Matrícula Total')

        egr_lic = get_nivel_val(df_tot_est, 'Licenciatura', 'Egresados Total')
        egr_tsu = get_nivel_val(df_tot_est, 'Técnico Superior', 'Egresados Total')
        egr_mae = get_nivel_val(df_tot_est, 'Maestría', 'Egresados Total')
        egr_doc = get_nivel_val(df_tot_est, 'Doctorado', 'Egresados Total')

        # Se eliminaron los saltos de línea y la sangría para evitar que Markdown lo lea como bloque de código
        html_general = f"""<div style="border-left: 5px solid #17a2b8; padding-left: 20px; margin-bottom: 30px; background-color: #f8f9fa; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
<h3 style="color:#0056b3; margin-top:0;">🎓 Indicadores Generales</h3>
<div style="display: flex; flex-direction: column; gap: 20px;">
<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 20px; border-bottom: 1px solid #dee2e6; padding-bottom: 15px;">
<div style="min-width: 200px;">
<div style="font-size:2rem; font-weight:800; color:#212529;">{total_alum:,.0f}</div>
<div style="font-size:0.9rem; color:#666; text-transform: uppercase; font-weight:600;">Matrícula Total</div>
</div>
<div style="display: flex; gap: 10px; flex-wrap: wrap;">
<div style="background: white; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6;">
<div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase;">Licenciatura</div>
<div style="font-weight: 700; color: #17a2b8; font-size: 1.1rem;">{mat_lic:,.0f}</div>
</div>
<div style="background: white; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6;">
<div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase;">Técnico Sup.</div>
<div style="font-weight: 700; color: #17a2b8; font-size: 1.1rem;">{mat_tsu:,.0f}</div>
</div>
<div style="background: white; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6;">
<div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase;">Maestría</div>
<div style="font-weight: 700; color: #17a2b8; font-size: 1.1rem;">{mat_mae:,.0f}</div>
</div>
<div style="background: white; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6;">
<div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase;">Doctorado</div>
<div style="font-weight: 700; color: #17a2b8; font-size: 1.1rem;">{mat_doc:,.0f}</div>
</div>
</div>
</div>
<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 20px;">
<div style="min-width: 200px;">
<div style="font-size:2rem; font-weight:800; color:#28a745;">{total_egresados:,.0f}</div>
<div style="font-size:0.9rem; color:#666; text-transform: uppercase; font-weight:600;">Egresados (Anual)</div>
</div>
<div style="display: flex; gap: 10px; flex-wrap: wrap;">
<div style="background: white; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6;">
<div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase;">Licenciatura</div>
<div style="font-weight: 700; color: #28a745; font-size: 1.1rem;">{egr_lic:,.0f}</div>
</div>
<div style="background: white; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6;">
<div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase;">Técnico Sup.</div>
<div style="font-weight: 700; color: #28a745; font-size: 1.1rem;">{egr_tsu:,.0f}</div>
</div>
<div style="background: white; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6;">
<div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase;">Maestría</div>
<div style="font-weight: 700; color: #28a745; font-size: 1.1rem;">{egr_mae:,.0f}</div>
</div>
<div style="background: white; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6;">
<div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase;">Doctorado</div>
<div style="font-weight: 700; color: #28a745; font-size: 1.1rem;">{egr_doc:,.0f}</div>
</div>
</div>
</div>
</div>
</div>"""

        st.markdown(html_general, unsafe_allow_html=True)

        st.markdown("#### Principal Campo de Formación por Nivel Educativo")

        col_mat, col_egr = st.columns(2)

        niveles_orden = ['Licenciatura', 'Técnico Superior', 'Maestría', 'Doctorado']

        def get_top1_by_level(df, nivel, val_col, share_col):
            subset = df[df['Nivel_Agrupado'] == nivel]
            if not subset.empty:
                row = subset.sort_values(val_col, ascending=False).iloc[0]
                return row['CAMPO AMPLIO'], row[val_col], row[share_col]
            return None, 0, 0

        with col_mat:
            st.markdown(f"<div style='margin-bottom:15px; font-weight:700; color:#0056b3; font-size:1.1rem;'>Por Matrícula</div>", unsafe_allow_html=True)
            for nivel in niveles_orden:
                campo, val, share = get_top1_by_level(df_top_mat, nivel, 'Matrícula Total', 'Participacion_Matricula')
                if campo:
                    html_mat = f"""<div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #17a2b8; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 10px;">
<div style="font-size:0.8rem; color:#666; font-weight:700; text-transform: uppercase; margin-bottom:4px;">{nivel}</div>
<div style="font-weight:600; font-size:0.95rem; color:#333; margin-bottom:6px;">{campo}</div>
<div style="display:flex; justify-content:space-between; align-items:flex-end;">
<span style="color:#17a2b8; font-weight:700; font-size:1.1rem;">{share:.1f}%</span>
<span style="color:#888; font-size:0.85rem;">{val:,.0f} alumnos</span>
</div>
</div>"""
                    st.markdown(html_mat, unsafe_allow_html=True)

        with col_egr:
            st.markdown(f"<div style='margin-bottom:15px; font-weight:700; color:#198754; font-size:1.1rem;'>Por Egresados</div>", unsafe_allow_html=True)
            for nivel in niveles_orden:
                campo, val, share = get_top1_by_level(df_top_egr, nivel, 'Egresados Total', 'Participacion_Egresados')
                if campo:
                    html_egr = f"""<div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #28a745; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 10px;">
<div style="font-size:0.8rem; color:#666; font-weight:700; text-transform: uppercase; margin-bottom:4px;">{nivel}</div>
<div style="font-weight:600; font-size:0.95rem; color:#333; margin-bottom:6px;">{campo}</div>
<div style="display:flex; justify-content:space-between; align-items:flex-end;">
<span style="color:#28a745; font-weight:700; font-size:1.1rem;">{share:.1f}%</span>
<span style="color:#888; font-size:0.85rem;">{val:,.0f} egresados</span>
</div>
</div>"""
                    st.markdown(html_egr, unsafe_allow_html=True)

    else:
        st.info(f"No se encontraron datos de Educación Superior para {state_norm}.")

except Exception as e:
    st.error(f"Error procesando módulo de educación: {str(e)}")

# ==========================================
# SECCIÓN 5: PRODUCTIVIDAD
# ==========================================
st.markdown("---")
st.header("5. Productividad Laboral")

df_saic = DATA['saic']
df_saic['Entidad_Norm'] = df_saic['Entidad'].str.strip().replace(NAME_NORMALIZER)
df_saic['Rank'] = df_saic['Indicador_Productividad'].rank(ascending=False)

row = df_saic[df_saic['Entidad_Norm'] == state_norm]

if not row.empty:
    val = row['Indicador_Productividad'].values[0]
    rk = int(row['Rank'].values[0])
    nombre_estado = row['Entidad'].values[0]
    
    top1 = df_saic.sort_values('Indicador_Productividad', ascending=False).iloc[0]
    avg = df_saic['Indicador_Productividad'].mean()
    
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
    c4.markdown(card_html.format(title=f"1er Lugar ({top1['Entidad']})", value=f"{top1['Indicador_Productividad']:.2f}"), unsafe_allow_html=True)
    
    df_sorted = df_saic.sort_values('Indicador_Productividad', ascending=False).reset_index(drop=True)
    colors = ['#d63384' if x == state_norm else '#e9ecef' for x in df_sorted['Entidad_Norm']]
    
    fig = px.bar(df_sorted, x='Entidad', y='Indicador_Productividad')
    fig.update_traces(marker_color=colors)
    
    fig.add_hline(y=avg, line_dash="dot", line_color="white", annotation_text="Promedio", annotation_font_color="white")
    
    fig.update_layout(
        yaxis_title="Productividad",
        xaxis_title="",
        xaxis_tickangle=-90,
        margin=dict(t=20, b=0, l=0, r=0),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# SECCIÓN 6: IMCO
# ==========================================
st.markdown("---")
st.header("6. Competitividad (IMCO)")

df_g = DATA['imco_g']
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
    colors = ['#fd7e14' if x == state_norm else '#e9ecef' for x in df_sorted['Entidad_Norm']]
    
    fig = px.bar(df_sorted, x='Entidad', y='Valor')
    fig.update_traces(marker_color=colors)
    
    fig.add_hline(y=avg, line_dash="dot", line_color="white", annotation_text="Promedio", annotation_font_color="white")
    
    fig.update_layout(
        yaxis_title="Competitividad",
        xaxis_title="",
        xaxis_tickangle=-90,
        margin=dict(t=20, b=0, l=0, r=0),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

df_d = DATA['imco_d']
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
        # Si está en la lista es Inverso (33-Rank), si no, es Directo (Rank)
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
        # Menor puntaje = Mejor Rank (1)
        for _, r in st_d.sort_values('Puntaje_Fortaleza').head(5).iterrows():
            ch = r['Cambio_Ajustado']
            ch_str = f"⬆️ {int(abs(ch))}" if ch > 0 else (f"⬇️ {int(abs(ch))}" if ch < 0 else "➖")
            st.markdown(f"- **#{int(r['Rank'])}** {r['Indicador']} ({ch_str})")
    with c2:
        st.markdown("**⚠️ Top 5 Áreas de oportunidad**")
        # Mayor puntaje = Peor Rank (32)
        for _, r in st_d.sort_values('Puntaje_Fortaleza', ascending=False).head(5).iterrows():
            ch = r['Cambio_Ajustado']
            ch_str = f"⬆️ {int(abs(ch))}" if ch > 0 else (f"⬇️ {int(abs(ch))}" if ch < 0 else "➖")
            st.markdown(f"- **#{int(r['Rank'])}** {r['Indicador']} ({ch_str})")

# ==========================================
# SECCIÓN 7: RATINGS
# ==========================================
if "Tlaxcala" not in selected_name:
    st.markdown("---")
    st.header("7. Calificación Crediticia")
    df_r = DATA['ratings']
    if not df_r.empty:
        col_ent = [c for c in df_r.columns if "Entidad" in c][0]
        match = df_r[df_r[col_ent].astype(str).apply(lambda x: NAME_NORMALIZER.get(x, x)) == state_norm].copy()
        
        if not match.empty:
            match = match.rename(columns={
                "Fecha Publicacion": "Fecha Publicación",
                "Calificacion": "Calificación"
            })
            
            columnas_deseadas = ["Calificadora", "Entidad", "Fecha Publicación", "Calificación", "Perspectiva"]
            columnas_finales = [c for c in columnas_deseadas if c in match.columns]
            
            st.dataframe(match[columnas_finales], hide_index=True)
        else: 
            st.info("Sin calificación.")
    else: 
        st.info("Archivo no disponible.")

# ==========================================
# SECCIÓN 8: TOP EXPORTACIONES
# ==========================================
st.markdown("---")
if "Tlaxcala" in selected_name:
    st.header("7. Top 10 Sectores Exportadores")
else:
    st.header("8. Top 10 Sectores Exportadores")

df_e = DATA['export']
df_e['Year'] = df_e['Periodo'].astype(str).str[:4]
max_y = df_e['Year'].max()

st_e = df_e[(df_e['Estado_ID'].astype(str).str.zfill(2) == state_id_str) & (df_e['Year'] == max_y) & (df_e['Sector'] != 'Total')]

if not st_e.empty:
    top10 = st_e.groupby('Sector')['Valor'].sum().reset_index().sort_values('Valor', ascending=False).head(10)
    tot = top10['Valor'].sum()
    top10['Part'] = (top10['Valor']/tot*100)
    
    nac_agg = df_e[(df_e['Year'] == max_y) & (df_e['Sector'] != 'Total')].groupby(['Sector', 'Estado_ID'])['Valor'].sum().reset_index()
    rks = []
    for s in top10['Sector']:
        d_s = nac_agg[nac_agg['Sector'] == s].copy()
        d_s['Rank'] = d_s['Valor'].rank(ascending=False)
        try: r = int(d_s[d_s['Estado_ID'].astype(str).str.zfill(2) == state_id_str]['Rank'].values[0])
        except: r = "-"
        rks.append(r)
    top10['Rank Nac'] = rks

    max_val = top10['Valor'].max()
    
    html_export = """<div style="background-color: transparent; width: 100%; margin-top: 10px; font-family: sans-serif; color: #ffffff;">
<div style="display: flex; width: 100%; margin-bottom: 20px; font-weight: bold; text-align: center; font-size: 0.95rem;">
    <div style="width: 35%; text-align: right; padding-right: 15px; color: #ffffff;">Principales sectores de exportación, millones USD</div>
    <div style="width: 35%;"></div>
    <div style="width: 15%; color: #ffffff;">% en el total<br>estatal</div>
    <div style="width: 15%; color: #ffffff;">Ranking<br>nacional</div>
</div>"""
    
    for _, r in top10.iterrows():
        pct = (r['Valor'] / max_val) * 100 if max_val > 0 else 0
        val_millions = r['Valor'] / 1000
        sector_wrapped = '<br>'.join(textwrap.wrap(r['Sector'], width=38))
        
        html_export += f"""
<div style="display: flex; width: 100%; align-items: stretch; margin-bottom: 12px;">
    <div style="width: 35%; text-align: right; padding-right: 15px; font-size: 0.85rem; display: flex; align-items: center; justify-content: flex-end;">
        <span style="display: inline-block; line-height: 1.2; color: #ffffff;">{sector_wrapped}</span>
    </div>
    <div style="width: 35%; border-left: 2px solid #e0e0e0; padding-left: 0; display: flex; align-items: center;">
        <div style="background-color: #007bff; width: {pct}%; height: 26px; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; color: white; font-weight: bold; font-size: 0.85rem; min-width: 50px; border-radius: 0 4px 4px 0; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
            {val_millions:,.0f}
        </div>
    </div>
    <div style="width: 15%; display: flex; justify-content: center; align-items: center;">
        <div style="border: 1px solid #dee2e6; background-color: #ffffff; border-radius: 6px; padding: 4px 0; width: 80%; font-weight: bold; font-size: 0.9rem; color: #212529; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            {r['Part']:.1f}%
        </div>
    </div>
    <div style="width: 15%; display: flex; justify-content: center; align-items: center;">
        <div style="border: 1px solid #dee2e6; background-color: #ffffff; border-radius: 6px; padding: 4px 0; width: 80%; font-weight: bold; font-size: 0.9rem; color: #212529; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            {r['Rank Nac']}°
        </div>
    </div>
</div>"""
        
    html_export += "\n</div>"
    
    st.markdown(html_export, unsafe_allow_html=True)