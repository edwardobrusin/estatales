from playwright.sync_api import sync_playwright
import time
import os
import zipfile

# Lista exacta de estados extraída de tu diccionario STATE_MAP
ESTADOS = [
    'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche',
    'Coahuila', 'Colima', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Durango',
    'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'México', 'Michoacán',
    'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro',
    'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco',
    'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'
]

def generar_fichas_masivas(url="http://localhost:8501", output_dir="fichas_pdf", zip_name="fichas_pdf.zip"):
    # 1. Crear el directorio si no existe
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Directorio destino preparado: {output_dir}/")

    with sync_playwright() as p:
        print("🤖 Iniciando navegador Chromium (Headless)...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1300, "height": 1080},
            device_scale_factor=1
        )
        page = context.new_page()

        # 2. Iterar sobre cada estado
        for idx, estado in enumerate(ESTADOS, 1):
            print(f"\n[{idx}/{len(ESTADOS)}] Procesando: {estado}...")
            
            # Navegamos a la app fresca en cada iteración para restaurar el menú lateral
            page.goto(url, wait_until="domcontentloaded")
            
            # Esperamos a que el menú lateral esté visible
            page.wait_for_selector('[data-testid="stSidebar"]', state="visible", timeout=60000)
            
            print(f"      Haciendo clic en el botón de {estado}...")
            # Buscamos específicamente el botón en el sidebar que tenga exactamente el texto del estado
            boton_estado = page.locator('[data-testid="stSidebar"] button').get_by_text(estado, exact=True)
            boton_estado.click()
            
            print("      Esperando procesamiento de datos y gráficas...")
            # TRUCO: Esperamos a que el título H1 cambie exactamente al estado seleccionado
            page.wait_for_selector(f'h1:has-text("Ficha Técnica Estatal: {estado}")', state="visible", timeout=60000)
            
            # Esperamos a que Plotly dibuje
            page.wait_for_selector('.js-plotly-plot', state="visible", timeout=60000)
            time.sleep(3) # Pausa para animaciones

            print("      Inyectando CSS de limpieza y liberando lienzo...")
            css_limpieza = """
                [data-testid="stSidebar"], header[data-testid="stHeader"], footer, .stAppDeployButton, #MainMenu,
                .floating-download-btn,
                .floating-warning {     
                    display: none !important; 
                }
                html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
                    height: auto !important; min-height: 100% !important; overflow: visible !important; position: static !important;
                }
                [data-testid="stAppViewBlockContainer"], .block-container, [data-testid="block-container"] {
                    max-width: 100% !important; padding: 2rem !important; margin: 0 !important;
                }
                .stApp { background-color: #F8FAFC !important; }
            """
            page.add_style_tag(content=css_limpieza)
            time.sleep(2) # Reflow del DOM

            # Calcular altura real
            altura_total = page.evaluate("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.body.offsetHeight)")
            ancho_fijo = 1300

            # 3. Generar y guardar el PDF
            output_path = os.path.join(output_dir, f"{estado}.pdf")
            page.pdf(
                path=output_path,
                print_background=True,
                width=f"{ancho_fijo}px",
                height=f"{altura_total + 50}px"
            )
            print(f"      ✅ Guardado: {output_path}")

        browser.close()
        
    # 4. Compresión automática del directorio en un archivo .zip
    # Código Modificado
    print(f"\n📦 Empaquetando y comprimiendo {output_dir}/ en {zip_name} al máximo nivel...")
    try:
        # Agregamos compresslevel=9 para exprimir cada byte
        with zipfile.ZipFile(zip_name, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        # arcname=file asegura que los PDFs queden en la raíz del ZIP (sin subcarpetas internas)
                        zipf.write(file_path, arcname=file)
        print(f"✅ ¡Éxito! Archivo ZIP generado con máxima compresión en: {zip_name}")
    except Exception as e:
        print(f"❌ Error al generar el archivo ZIP: {e}")

    print("\n🎉 ¡Proceso masivo completado de principio a fin!")

if __name__ == "__main__":
    generar_fichas_masivas(url="http://localhost:8501")