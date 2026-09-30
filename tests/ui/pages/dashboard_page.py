"""
Page Object for the dashboard.

Locators and page actions live here. Tests only call methods like
page.measure(2400) - if the HTML changes, we fix it in ONE place.
"""
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class DashboardPage:
    IDN = (By.ID, "idn")
    FREQ_INPUT = (By.ID, "freq-input")
    MEASURE_BTN = (By.ID, "measure-btn")
    ERROR_MSG = (By.ID, "error-msg")
    ROWS = (By.CSS_SELECTOR, "#results-table .result-row")
    FIRST_STATUS = (By.CSS_SELECTOR, "#results-table .result-row .status")
    FIRST_POWER = (By.CSS_SELECTOR, "#results-table .result-row .power")

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def open(self):
        self.driver.get(self.base_url)
        self.wait.until(EC.visibility_of_element_located(self.IDN))
        return self

    def instrument_id(self):
        return self.driver.find_element(*self.IDN).text

    def measure(self, freq_mhz):
        field = self.wait.until(EC.element_to_be_clickable(self.FREQ_INPUT))
        field.clear()
        field.send_keys(str(freq_mhz))
        # Mark the current page. After the form submits, the browser loads a
        # new document without this mark - that's how we know the reload
        # finished. Without this, the wait below could be satisfied by the
        # OLD page (which already has result rows) = flaky test.
        self.driver.execute_script("document.body.dataset.oldPage = 'yes'")
        self.driver.find_element(*self.MEASURE_BTN).click()
        WebDriverWait(self.driver, 10, ignored_exceptions=[WebDriverException]).until(
            lambda d: d.execute_script(
                "return document.readyState === 'complete' && "
                "!document.body.dataset.oldPage")
        )
        # Now wait for the NEW page to show a result or an error
        self.wait.until(
            EC.any_of(
                EC.presence_of_element_located(self.FIRST_STATUS),
                EC.presence_of_element_located(self.ERROR_MSG),
            )
        )
        return self

    def last_status(self):
        return self.driver.find_element(*self.FIRST_STATUS).text

    def last_power(self):
        return float(self.driver.find_element(*self.FIRST_POWER).text)

    def error_message(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.ERROR_MSG)).text
