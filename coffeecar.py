import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# Configuración de Selenium con Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

# URL de la app
driver.get("https://coffee-cart.app/")

# Ruta para guardar screenshots

ruta_screenshots = os.path.join(os.getcwd(), "screenshots")
os.makedirs(ruta_screenshots, exist_ok=True)

# Ruta para guardar errores
ruta_errores = os.path.join(os.getcwd(), "errores_coffee")
os.makedirs(ruta_errores, exist_ok=True)

try:
    # Esperar a que carguen las tazas (aumenta el tiempo de espera)
    try:
        tazas = WebDriverWait(driver, 40).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "cup-body"))
        )
    except TimeoutException as e:
        print("❌ Timeout esperando las tazas. Guardando screenshot y HTML para depuración.")
        driver.save_screenshot(os.path.join(ruta_screenshots, "error_tazas.png"))
        with open(os.path.join(ruta_screenshots, "error_tazas.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        tazas = []

    # Iterar solo sobre las 3 primeras tazas (o menos si hay menos)
    for i in range(min(3, len(tazas))):
        try:
            # Click en la taza
            try:
                tazas[i].click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", tazas[i])

            # Esperar y hacer click en el botón "Yes" del modal
            btn_yes = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//dialog[@data-cy='add-to-cart-modal']//button[text()='Yes']"))
            )
            try:
                btn_yes.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", btn_yes)

            # Pausa corta para que actualice el carrito
            time.sleep(1)

            # Guardar screenshot
            driver.save_screenshot(os.path.join(ruta_screenshots, f"taza_{i+1}.png"))
            print(f"✅ Taza {i+1} agregada y captura guardada.")

            # Manejo del popup especial de oferta (Yes, of course!)
            try:
                btn_offer_yes = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Yes, of course!')]"))
                )
                try:
                    btn_offer_yes.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", btn_offer_yes)
                print("✅ Oferta especial aceptada.")
                driver.save_screenshot(os.path.join(ruta_screenshots, f"oferta_especial_{i+1}.png"))
                time.sleep(1)
                # Intentar click en la taza con descuento si aparece
                try:
                    taza_descuento = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-cy='(Discounted)-Mocha']"))
                    )
                    try:
                        taza_descuento.click()
                    except ElementClickInterceptedException:
                        driver.execute_script("arguments[0].click();", taza_descuento)
                    print("✅ Taza con descuento seleccionada.")
                    driver.save_screenshot(os.path.join(ruta_screenshots, f"taza_descuento_{i+1}.png"))
                    time.sleep(1)
                except TimeoutException:
                    print("No apareció la taza con descuento.")
            except TimeoutException:
                pass  # No apareció la oferta especial, continuar normalmente

        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            print(f"⚠️ No se pudo procesar la taza {i+1}: {e}")
            driver.save_screenshot(os.path.join(ruta_errores, f"error_taza_{i+1}.png"))
            with open(os.path.join(ruta_errores, f"error_taza_{i+1}.html"), "w", encoding="utf-8") as f:
                f.write(driver.page_source)

finally:
    print("Prueba finalizada. Cerrando navegador en 10 segundos...")
    time.sleep(10)
    driver.quit()
