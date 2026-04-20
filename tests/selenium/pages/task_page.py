# tests/selenium/pages/task_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class TaskPage:
    """Page Object untuk halaman TaskFlow"""
    
    # ========== Locators ==========
    # Form tambah tugas
    FORM_TITLE = (By.ID, "title")
    FORM_DESCRIPTION = (By.ID, "description")
    FORM_STATUS = (By.ID, "status")
    BTN_SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")
    BTN_RESET = (By.ID, "resetForm")
    
    # Tabel tugas
    TASKS_TABLE = (By.CSS_SELECTOR, ".table")
    TASKS_TABLE_BODY = (By.CSS_SELECTOR, ".table tbody")
    TASKS_TABLE_ROWS = (By.CSS_SELECTOR, ".table tbody tr")
    BTN_REFRESH = (By.ID, "refreshBtn")
    
    # Modal edit
    MODAL_EDIT = (By.ID, "editTaskModal")
    MODAL_TITLE = (By.ID, "editTitle")
    MODAL_DESCRIPTION = (By.ID, "editDescription")
    MODAL_STATUS = (By.ID, "editStatus")
    BTN_SAVE_EDIT = (By.ID, "saveEditBtn")
    BTN_CANCEL_EDIT = (By.CSS_SELECTOR, "#editTaskModal .btn-secondary")
    BTN_CLOSE_MODAL = (By.CSS_SELECTOR, "#editTaskModal .btn-close")
    
    # Alert container
    ALERT_CONTAINER = (By.ID, "alertContainer")
    ALERT_SUCCESS = (By.CSS_SELECTOR, ".alert-success")
    ALERT_DANGER = (By.CSS_SELECTOR, ".alert-danger")
    
    # Empty state
    EMPTY_STATE = (By.CSS_SELECTOR, ".text-center.text-muted")
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    # ========== Actions ==========
    
    def create_task(self, title, description="", status="pending"):
        """Membuat tugas baru melalui form"""
        self.wait.until(EC.presence_of_element_located(self.FORM_TITLE))
        
        # Isi form
        self.driver.find_element(*self.FORM_TITLE).send_keys(title)
        if description:
            self.driver.find_element(*self.FORM_DESCRIPTION).send_keys(description)
        
        # Pilih status menggunakan dropdown
        from selenium.webdriver.support.ui import Select
        select = Select(self.driver.find_element(*self.FORM_STATUS))
        select.select_by_value(status)
        
        # Submit form
        self.driver.find_element(*self.BTN_SUBMIT).click()
        
        # Tunggu alert muncul (indikasi sukses)
        self.wait.until(EC.presence_of_element_located(self.ALERT_SUCCESS))
    
    def reset_form(self):
        """Reset form ke keadaan awal"""
        self.driver.find_element(*self.BTN_RESET).click()
    
    def get_form_values(self):
        """Mendapatkan nilai current dari form"""
        return {
            'title': self.driver.find_element(*self.FORM_TITLE).get_attribute('value'),
            'description': self.driver.find_element(*self.FORM_DESCRIPTION).get_attribute('value')
        }
    
    def refresh_tasks(self):
        """Klik tombol refresh"""
        self.driver.find_element(*self.BTN_REFRESH).click()
        time.sleep(0.5)  # Tunggu sebentar untuk loading
    
    def get_all_tasks(self):
        """Mengembalikan list semua tugas yang ditampilkan di tabel"""
        rows = self.driver.find_elements(*self.TASKS_TABLE_ROWS)
        tasks = []
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 5:
                task = {
                    'id': cells[0].text.strip(),
                    'title': cells[1].text.strip(),
                    'description': cells[2].text.strip(),
                    'status': cells[3].find_element(By.TAG_NAME, "span").text.strip(),
                    'actions': {
                        'edit': cells[4].find_element(By.CSS_SELECTOR, ".btn-warning"),
                        'delete': cells[4].find_element(By.CSS_SELECTOR, ".btn-danger")
                    }
                }
                tasks.append(task)
        
        return tasks
    
    def task_exists(self, title):
        """Memeriksa apakah tugas dengan judul tertentu ada di tabel"""
        tasks = self.get_all_tasks()
        return any(task['title'] == title for task in tasks)
    
    def get_task_by_title(self, title):
        """Mendapatkan data tugas berdasarkan judul"""
        tasks = self.get_all_tasks()
        for task in tasks:
            if task['title'] == title:
                return task
        return None
    
    def click_edit_task(self, title):
        """Klik tombol edit untuk tugas dengan judul tertentu"""
        task = self.get_task_by_title(title)
        if task:
            task['actions']['edit'].click()
            # Tunggu modal muncul
            self.wait.until(EC.visibility_of_element_located(self.MODAL_EDIT))
        else:
            raise Exception(f"Task with title '{title}' not found")
    
    def click_delete_task(self, title):
        """Klik tombol delete untuk tugas dengan judul tertentu"""
        task = self.get_task_by_title(title)
        if task:
            task['actions']['delete'].click()
    
    def update_task_in_modal(self, title=None, description=None, status=None):
        """Update tugas melalui modal edit"""
        if title is not None:
            title_input = self.driver.find_element(*self.MODAL_TITLE)
            title_input.clear()
            title_input.send_keys(title)
        
        if description is not None:
            desc_input = self.driver.find_element(*self.MODAL_DESCRIPTION)
            desc_input.clear()
            desc_input.send_keys(description)
        
        if status is not None:
            from selenium.webdriver.support.ui import Select
            select = Select(self.driver.find_element(*self.MODAL_STATUS))
            select.select_by_value(status)
        
        self.driver.find_element(*self.BTN_SAVE_EDIT).click()
        
        # Tunggu modal tertutup dan alert muncul
        self.wait.until(EC.invisibility_of_element_located(self.MODAL_EDIT))
        self.wait.until(EC.presence_of_element_located(self.ALERT_SUCCESS))
    
    def get_alert_message(self):
        """Mendapatkan teks dari alert yang muncul"""
        alert = self.wait.until(EC.presence_of_element_located(self.ALERT_CONTAINER))
        return alert.text
    
    def is_empty_state_displayed(self):
        """Memeriksa apakah empty state ditampilkan"""
        try:
            self.driver.find_element(*self.EMPTY_STATE)
            return True
        except:
            return False
    
    def wait_for_alert_to_disappear(self):
        """Menunggu alert menghilang"""
        self.wait.until(EC.invisibility_of_element_located(self.ALERT_CONTAINER))
    
    def handle_delete_confirmation(self, accept=True):
        """Menangani dialog konfirmasi delete"""
        alert = self.wait.until(EC.alert_is_present())
        if accept:
            alert.accept()
        else:
            alert.dismiss()