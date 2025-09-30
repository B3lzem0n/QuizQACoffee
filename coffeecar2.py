import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# --- 1. Constantes de Configuración ---
URL_APP = "https://coffee-cart.app/"
TIMEOUT_GENERAL = 20  # Tiempo de espera para la mayoría de los elementos
TIMEOUT_INICIAL = 40  # Tiempo de espera para la carga inicial de productos
TIMEOUT_OFERTA = 5    # Tiempo corto de espera para pop-ups opcionales

# --- 2. Selectores Centralizados (Recomendados por estabilidad) ---
# Selector para los ítems de café (más estable que solo 'cup-body')
SELECTOR_COFFEE_ITEM = (By.CSS_SELECTOR, "ul[data-cy='coffee-list'] .coffee-item")

# Botón 'Yes' en el modal de confirmación (usando el data-cy si está disponible)
SELECTOR_BTN_YES = (By.XPATH, "//dialog[@data-cy='add-to-cart-modal']//button[text()='Yes']")

# Botón 'Yes, of course!' para la oferta especial
SELECTOR_BTN_OFFER = (By.XPATH, "//button[contains(text(),'Yes, of course!')]")

# Taza de descuento que puede aparecer tras aceptar la oferta
SELECTOR_TAZA_DESCUENTO = (By.XPATH, "//div[@data-cy='(Discounted)-Mocha']")


# --- 3. Inicialización del Driver y Directorios ---
# Configuración de Selenium con Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_experimental_option('excludeSwitches', ['enable-logging']) # Limpia la consola

try:
    print("⚙️ Configurando y conectando el driver de Chrome...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait_general = WebDriverWait(driver, TIMEOUT_GENERAL)
    wait_oferta = WebDriverWait(driver, TIMEOUT_OFERTA)

    # Ruta unificada para resultados (screenshots y archivos de error)
    ruta_resultados = os.path.join(os.getcwd(), "test_results_coffee_cart")
    os.makedirs(ruta_resultados, exist_ok=True)
    print(f"✅ Driver iniciado. Resultados se guardarán en: {ruta_resultados}")
    
except Exception as e:
    print(f"❌ Error crítico al iniciar el driver: {e}")
    exit(1)


# --- 4. Función Auxiliar para Clicks Robusto ---
def click_robusto(element, element_name):
    """Intenta hacer click de forma normal, si falla, usa JavaScript."""
    try:
        element.click()
        print(f"  ➡️ Click normal en '{element_name}'.")
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)
        print(f"  ➡️ Click por JavaScript en '{element_name}' (interceptado).")


# --- 5. Lógica Principal de la Prueba ---
try:
    driver.get(URL_APP)
    print(f"🌐 Navegando a: {URL_APP}")

    # Esperar a que carguen las tazas
    try:
        print(f"⏳ Esperando la lista de productos (máx {TIMEOUT_INICIAL}s)...")
        tazas = WebDriverWait(driver, TIMEOUT_INICIAL).until(
            EC.presence_of_all_elements_located(SELECTOR_COFFEE_ITEM)
        )
        print(f"✅ {len(tazas)} productos encontrados.")

    except TimeoutException:
        print("❌ Timeout: No se pudo cargar la lista de productos a tiempo.")
        driver.save_screenshot(os.path.join(ruta_resultados, "error_carga_productos.png"))
        tazas = []
    
    # Iterar solo sobre las 3 primeras tazas
    num_tazas_a_probar = min(3, len(tazas))
    print(f"🛒 Iniciando prueba de agregar {num_tazas_a_probar} ítem(s) al carrito.")

    for i in range(num_tazas_a_probar):
        try:
            print(f"\n--- Procesando Producto {i+1} ---")

            # 1. Click en el producto
            click_robusto(tazas[i], f"Producto {i+1}")

            # 2. Esperar y hacer click en el botón "Yes" del modal
            btn_yes = wait_general.until(
                EC.element_to_be_clickable(SELECTOR_BTN_YES)
            )
            click_robusto(btn_yes, "Botón 'Yes' del modal")

            # Pausa corta para que el carrito de la UI se actualice
            time.sleep(1)

            # Guardar screenshot del carrito con el ítem agregado
            driver.save_screenshot(os.path.join(ruta_resultados, f"taza_{i+1}_agregada.png"))
            print(f"  ✅ Producto {i+1} agregado. Captura guardada.")

            # --- Manejo del popup especial de oferta ---
            try:
                print("  ⏳ Buscando oferta especial...")
                # Esperamos poco tiempo ya que es un pop-up que aparece inmediatamente o no aparece
                btn_offer_yes = wait_oferta.until(
                    EC.element_to_be_clickable(SELECTOR_BTN_OFFER)
                )
                
                click_robusto(btn_offer_yes, "Botón 'Yes, of course!' (Oferta)")
                print("  ✅ Oferta especial aceptada.")
                driver.save_screenshot(os.path.join(ruta_resultados, f"oferta_especial_{i+1}_aceptada.png"))
                time.sleep(1) 

                # Intentar click en la taza con descuento si aparece (después de aceptar la oferta)
                try:
                    taza_descuento = wait_oferta.until(
                        EC.element_to_be_clickable(SELECTOR_TAZA_DESCUENTO)
                    )
                    click_robusto(taza_descuento, "Taza con descuento")
                    print("  ✅ Taza con descuento seleccionada.")
                    driver.save_screenshot(os.path.join(ruta_resultados, f"taza_descuento_{i+1}_agregada.png"))
                    time.sleep(1)
                except TimeoutException:
                    print("  ⚠️ Taza con descuento no apareció o no se pudo hacer click.")
                
            except TimeoutException:
                print("  ➡️ No apareció la oferta especial, continuando...")
                pass # No apareció la oferta especial, continuar normalmente

        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            error_type = type(e).__name__
            print(f"⚠️ ERROR FATAL al procesar Taza {i+1} ({error_type}): {e}")
            # Guardar evidencias en el mismo directorio de resultados
            driver.save_screenshot(os.path.join(ruta_resultados, f"error_taza_{i+1}_{error_type}.png"))
            with open(os.path.join(ruta_resultados, f"error_taza_{i+1}.html"), "w", encoding="utf-8") as f:
                f.write(driver.page_source)

finally:
    # --- 6. Cierre del Driver ---
    print("\n--- Finalizando Prueba ---")
    print("Prueba completada. Cerrando navegador en 5 segundos...")
    time.sleep(5)
    driver.quit()
    print("Navegador cerrado.")
