# tests/selenium/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

# Konfigurasi URL Frontend
FRONTEND_URL = "http://127.0.0.1:8080"

@pytest.fixture(scope="function")
def driver():
    """Fixture untuk WebDriver - akan dibuat baru setiap test function"""
    
    # Chrome Options
    chrome_options = Options()
    
    # Headless mode untuk CI/CD (tidak membuka browser GUI)
    if os.environ.get("HEADLESS", "false").lower() == "true":
        chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Inisialisasi driver dengan WebDriver Manager (auto download chromedriver)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Implicit wait - menunggu maksimal 10 detik untuk setiap find_element
    driver.implicitly_wait(10)
    
    # Buka halaman utama
    driver.get(FRONTEND_URL)
    
    yield driver
    
    # Cleanup - tutup browser setelah test selesai
    driver.quit()

@pytest.fixture
def frontend_url():
    return FRONTEND_URL

# Hook untuk screenshot saat test gagal
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        if "driver" in item.fixturenames:
            web_driver = item.funcargs["driver"]
            screenshot_dir = "reports/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            
            screenshot_path = f"{screenshot_dir}/{item.name}.png"
            web_driver.save_screenshot(screenshot_path)
            print(f"\nScreenshot saved: {screenshot_path}")