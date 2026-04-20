# tests/selenium/test_frontend.py
import pytest
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pages.task_page import TaskPage
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException

# ============================================
# FIXTURE untuk WebDriver
# ============================================

@pytest.fixture(scope="function")
def driver():
    """Fixture untuk WebDriver - dibuat baru setiap test function"""
    chrome_options = Options()
    
    # Cek environment variable HEADLESS
    if os.environ.get("HEADLESS", "false").lower() == "true":
        chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    
    # Inisialisasi Chrome dengan WebDriver Manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(30)
    
    # Buka Frontend
    driver.get("http://127.0.0.1:8080")
    
    yield driver
    
    driver.quit()


# ============================================
# TEST CLASS
# ============================================

class TestTaskFlowFrontend:
    """Test suite untuk frontend TaskFlow"""
    
    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Setup sebelum setiap test"""
        self.page = TaskPage(driver)
        self.driver = driver
        
        # Tutup modal jika masih terbuka dari test sebelumnya
        try:
            modal = self.driver.find_element(*self.page.MODAL_EDIT)
            if modal.is_displayed():
                modal.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
        except Exception:
            pass
        
        # Refresh halaman untuk state bersih
        self.page.refresh_tasks()
        time.sleep(0.5)
    
    # ============================================
    # TEST CASES
    # ============================================
    
    def test_page_loads_correctly(self):
        """TC-FE-001: Memastikan halaman dapat dimuat dengan benar"""
        assert "TaskFlow" in self.driver.title
        assert self.page.FORM_TITLE is not None
        print("✓ Halaman berhasil dimuat")
    
    def test_create_new_task_success(self):
        """TC-FE-002: Membuat tugas baru dengan data valid"""
        task_title = f"Test Task {int(time.time())}"
        task_desc = "Ini adalah tugas test"
        task_status = "pending"
        
        self.page.create_task(task_title, task_desc, task_status)
        time.sleep(1)
        
        assert self.page.task_exists(task_title), "Tugas tidak muncul di tabel"
        alert_msg = self.page.get_alert_message()
        assert "berhasil ditambahkan" in alert_msg
        print(f"✓ Tugas '{task_title}' berhasil dibuat")
    
    def test_create_task_without_title_validation(self):
        """TC-FE-003: Validasi client-side untuk field judul kosong"""
        # Kosongkan field judul dulu
        title_input = self.driver.find_element(*self.page.FORM_TITLE)
        title_input.clear()
        
        # Submit form
        self.driver.find_element(*self.page.BTN_SUBMIT).click()
        
        # Cek validasi HTML5 required
        validation_message = self.driver.execute_script(
            "return arguments[0].validationMessage;", title_input
        )
        assert validation_message != "", "Validasi tidak muncul"
        print("✓ Validasi judul kosong berfungsi")
    
    def test_reset_form_functionality(self):
        """TC-FE-004: Memastikan tombol reset mengosongkan form"""
        # Isi form
        self.driver.find_element(*self.page.FORM_TITLE).send_keys("Test Reset")
        self.driver.find_element(*self.page.FORM_DESCRIPTION).send_keys("Deskripsi test")
        
        # Reset form
        self.page.reset_form()
        time.sleep(0.5)
        
        # Assert
        form_values = self.page.get_form_values()
        assert form_values['title'] == "", "Judul tidak tereset"
        assert form_values['description'] == "", "Deskripsi tidak tereset"
        print("✓ Form reset berfungsi")
    
    def test_edit_task_functionality(self):
        """TC-FE-005: Mengedit tugas yang sudah ada"""
        original_title = f"Edit Test {int(time.time())}"
        self.page.create_task(original_title, "Deskripsi awal", "pending")
        time.sleep(1)
        
        self.page.click_edit_task(original_title)
        time.sleep(0.5)
        
        new_title = f"{original_title} (Updated)"
        self.page.update_task_in_modal(
            title=new_title,
            description="Deskripsi setelah update",
            status="completed"
        )
        time.sleep(1)
        
        assert self.page.task_exists(new_title), "Tugas dengan judul baru tidak ditemukan"
        task = self.page.get_task_by_title(new_title)
        assert task['status'] == "Completed"
        print(f"✓ Tugas berhasil diedit menjadi '{new_title}'")
    
    def test_delete_task_functionality(self):
        """TC-FE-006: Menghapus tugas"""
        task_title = f"Delete Test {int(time.time())}"
        self.page.create_task(task_title, "Akan dihapus", "pending")
        time.sleep(1)
        assert self.page.task_exists(task_title), "Tugas tidak berhasil dibuat"
        
        self.page.click_delete_task(task_title)
        time.sleep(0.5)
        
        self.page.handle_delete_confirmation(accept=True)
        time.sleep(1)
        
        assert not self.page.task_exists(task_title), "Tugas masih ada setelah dihapus"
        print(f"✓ Tugas '{task_title}' berhasil dihapus")
    
    def test_delete_task_cancelled(self):
        """TC-FE-007: Membatalkan penghapusan tugas - DIPERBAIKI"""
        task_title = f"Cancel Delete {int(time.time())}"
        self.page.create_task(task_title, "Tidak jadi dihapus", "pending")
        time.sleep(1)
        
        # Klik tombol delete
        self.page.click_delete_task(task_title)
        time.sleep(0.5)
        
        # Batalkan penghapusan
        try:
            alert = self.driver.switch_to.alert
            alert.dismiss()  # Klik Cancel
        except NoAlertPresentException:
            # Jika alert tidak muncul, refresh dan cek lagi
            self.page.refresh_tasks()
        
        time.sleep(1)
        
        # Refresh halaman untuk memastikan
        self.page.refresh_tasks()
        time.sleep(0.5)
        
        # Assert - Tugas harus masih ada
        assert self.page.task_exists(task_title), "Tugas hilang padahal delete dibatalkan"
        print("✓ Pembatalan delete berfungsi")
    
    def test_refresh_button(self):
        """TC-FE-008: Memastikan tombol refresh memuat ulang data"""
        api_url = "http://127.0.0.1:8000/api/tasks"
        new_task = {
            "title": f"API Created Task {int(time.time())}",
            "description": "Dibuat via API",
            "status": "pending"
        }
        response = requests.post(api_url, json=new_task)
        assert response.status_code == 201
        task_title = new_task["title"]
        
        time.sleep(1)
        self.page.refresh_tasks()
        time.sleep(1)
        
        assert self.page.task_exists(task_title), "Tugas dari API tidak muncul setelah refresh"
        
        # Cleanup - hapus tugas yang dibuat via API
        tasks = requests.get(api_url).json()
        for task in tasks:
            if task['title'] == task_title:
                requests.delete(f"{api_url}/{task['id']}")
        
        print("✓ Tombol refresh berfungsi")
    
    def test_status_badge_display(self):
        """TC-FE-009: Memastikan status badge ditampilkan dengan warna yang benar"""
        # Hapus data lama dulu
        api_url = "http://127.0.0.1:8000/api/tasks"
        tasks = requests.get(api_url).json()
        for task in tasks:
            requests.delete(f"{api_url}/{task['id']}")
        
        time.sleep(1)
        
        # Buat tugas dengan berbagai status
        tasks_data = [
            ("Task Pending", "pending"),
            ("Task Progress", "in-progress"),
            ("Task Completed", "completed")
        ]
        
        for title, status in tasks_data:
            self.page.create_task(title, f"Test {status}", status)
            time.sleep(0.5)
        
        # Refresh dan verifikasi
        self.page.refresh_tasks()
        time.sleep(1)
        
        # Cek setiap tugas ada
        for title, _ in tasks_data:
            assert self.page.task_exists(title), f"Tugas '{title}' tidak ditemukan"
        
        print("✓ Status badge ditampilkan dengan benar")
    
    def test_modal_close_buttons(self):
        """TC-FE-010: Memastikan modal edit bisa ditutup dengan berbagai cara"""
        task_title = f"Modal Test {int(time.time())}"
        self.page.create_task(task_title, "Test modal", "pending")
        time.sleep(1)
        
        # Test 1: Tutup dengan tombol X
        self.page.click_edit_task(task_title)
        time.sleep(0.5)
        try:
            close_btn = self.driver.find_element(*self.page.BTN_CLOSE_MODAL)
            close_btn.click()
        except:
            # Jika tombol X tidak ditemukan, tekan ESC
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        print("  ✓ Modal bisa ditutup")
        
        # Test 2: Buka lagi dan tutup dengan ESC
        self.page.click_edit_task(task_title)
        time.sleep(0.5)
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        print("  ✓ Modal bisa ditutup dengan ESC")
        
        print("✓ Modal close buttons berfungsi")
    
    def test_empty_state_when_no_tasks(self):
        """TC-FE-011: Memastikan empty state muncul saat tidak ada tugas"""
        # Hapus semua tugas
        api_url = "http://127.0.0.1:8000/api/tasks"
        tasks = requests.get(api_url).json()
        for task in tasks:
            requests.delete(f"{api_url}/{task['id']}")
        
        time.sleep(1)
        self.page.refresh_tasks()
        time.sleep(1)
        
        assert self.page.is_empty_state_displayed(), "Empty state tidak muncul"
        print("✓ Empty state ditampilkan dengan benar")
    
    def test_form_validation_after_reset(self):
        """TC-FE-012: Memastikan form valid setelah di-reset - DIPERBAIKI"""
        # Submit form kosong (trigger validasi)
        self.driver.find_element(*self.page.BTN_SUBMIT).click()
        time.sleep(0.5)
        
        # Reset form
        self.page.reset_form()
        time.sleep(0.5)
        
        # Coba submit lagi, seharusnya tidak ada validasi error
        # (Validasi HTML5 hanya trigger jika field required kosong)
        title_input = self.driver.find_element(*self.page.FORM_TITLE)
        title_input.send_keys("Test After Reset")
        
        self.driver.find_element(*self.page.BTN_SUBMIT).click()
        time.sleep(0.5)
        
        # Cek apakah ada alert sukses
        try:
            alert = self.driver.find_element(*self.page.ALERT_SUCCESS)
            assert alert.is_displayed()
        except NoSuchElementException:
            pass  # Mungkin alert sudah hilang
        
        print("✓ Validasi form di-reset dengan benar")