import os
import shutil
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


BOOKING_URL = (
    "https://cityofhamilton.perfectmind.com/39117/Clients/BookMe4BookingPages/Classes?"
    "widgetId=d63d746c-8862-4ca9-8b3c-5f79e841bba7&"
    "calendarId=baecc0a4-1ba9-4151-9e2c-45f21f60bbb6&"
    "singleCalendarWidget=False"
)


def book_court(day: str, court_name: str, time_str: str, email: str, password: str, *, headless: bool = False) -> str:
    """Book a pickleball court using Selenium and return a status message.

    Args:
        day: Weekday name exactly as shown on site, e.g., "Wednesday".
        court_name: Court label as shown on site, e.g., "Pickleball Court 9".
        time_str: Time string as shown on site, e.g., "07:30 pm".
        email: Login email.
        password: Login password.
        headless: If True, runs Chrome in headless mode.

    Returns:
        A human-readable status string indicating success or failure.
    """
    driver: Optional[webdriver.Chrome] = None
    try:
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1280,800")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-setuid-sandbox")

        chrome_binary = os.environ.get("CHROME_BIN")
        if chrome_binary:
            chrome_options.binary_location = chrome_binary

        chromedriver_path = (
            os.environ.get("CHROMEDRIVER")
            or shutil.which("chromedriver")
            or ChromeDriverManager().install()
        )
        service = ChromeService(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 20)

        driver.get(BOOKING_URL)

        # Login
        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pm-button.pm-login-button"))
        )
        login_button.click()

        email_box_input = wait.until(
            EC.presence_of_element_located((By.ID, "textBoxUsername"))
        )
        email_box_input.clear()
        email_box_input.send_keys(email)

        password_box_input = driver.find_element(By.ID, "textBoxPassword")
        password_box_input.clear()
        password_box_input.send_keys(password)

        submit_button = driver.find_element(By.ID, "buttonLogin")
        submit_button.click()

        # Wait for filters to load and overlay to disappear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.weekdays-filter")))
        wait.until(EC.invisibility_of_element_located((By.ID, "bm-overlay")))

        # Select weekday
        checkbox = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f'input.pm-weekdays-checkbox[data-value="{day}"]')
            )
        )
        driver.execute_script("arguments[0].click();", checkbox)

        # Locate court container
        court_div = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//div[h3/span[contains(text(), '{court_name}')]]")
            )
        )

        # Find requested time under that court and its corresponding Book button
        time_span = court_div.find_element(By.XPATH, f"following::span[contains(text(), '{time_str}')]")
        book_button = time_span.find_element(
            By.XPATH, "following::input[@type='button' and @value='Book'][1]"
        )
        book_button.click()

        # Book event flow
        book_court_btn = wait.until(EC.element_to_be_clickable((By.ID, "bookEventButton")))
        book_court_btn.click()

        # Select up to first 6 participant checkboxes if present
        try:
            checkboxes = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "input[role='checkbox'][name*='IsParticipating']")
                )
            )
            for checkbox in checkboxes[:6]:
                if not checkbox.is_selected():
                    checkbox.click()
                    time.sleep(0.2)
        except TimeoutException:
            # Some flows may skip participants selection
            pass

        # Next → Next → Add to Cart
        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[title='Next']")))
        next_btn.click()

        next_btn2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[title='Next']")))
        next_btn2.click()

        add_to_cart = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[title='Add to Cart']"))
        )
        add_to_cart.click()

        # Switch to checkout iframe and place order
        iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.online-store"))
        )
        driver.switch_to.frame(iframe)

        container = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.process-actions"))
        )
        place_order = container.find_element(By.CSS_SELECTOR, "[id^='process-now']")
        driver.execute_script(
            "arguments[0].scrollIntoView(true); arguments[0].click();", place_order
        )

        # Small settle wait
        time.sleep(2)
        return "Success: Court booking flow completed. Please verify your account for confirmation."

    except (TimeoutException, NoSuchElementException) as e:
        return f"Failed during booking flow: {str(e)}"
    except WebDriverException as e:
        return f"WebDriver error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass 
