# Selenium Browser
from types import coroutine
from typing import Mapping
from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome import options  # type: ignore
from selenium.webdriver.common import by  # type: ignore
from selenium.webdriver.common.keys import Keys  # type: ignore
from selenium.webdriver.common.action_chains import ActionChains  # type: ignore
from selenium.webdriver.support.select import Select  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager
# Selenium Wait
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
# Selenium Exceptions
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.common.exceptions import TimeoutException  # type: ignore
from selenium.common.exceptions import ElementClickInterceptedException  # type: ignore
from selenium.common.exceptions import StaleElementReferenceException  # type: ignore
from selenium.common.exceptions import WebDriverException  # type: ignore
# Utilities
import time
import string
import random
import os
import base64
from sys import argv
import argparse
from rich.console import Console  # type: ignore

console = Console()

"""Default Parameters"""
MAX_WAIT = 600
DRIVER = None
URL = 'https://request-test.fpm.pdx.edu/ready'
WORKING_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
UTILS_FOLDER = os.path.join(WORKING_DIRECTORY, 'utils/')


def initializeDriver():
    """
    Initialize Chrome webdriver
    Params:
        None
    Returns:
        driver <webdriver> : Chrome webdriver with specified options
    """
    # Chrome Driver Options
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-extensions')
    options.add_argument('--kiosk-printing')
    options.add_argument('--test-type')
    options.add_argument('--disable-gpu')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # Create a new driver
    chromedriver = os.path.join(UTILS_FOLDER, 'chromedriver')
    services = Service(chromedriver)
    driver = webdriver.Chrome(service=services, options=options)
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.set_page_load_timeout(MAX_WAIT)
    driver.set_script_timeout(MAX_WAIT)

    return driver


def decodePassword(passFile):
    """
    Decodes the base64 password so we can use it to login
    Params:
        passFile <string> : name of file containing username
                            and base64 encrypted password
    Returns:
        login <obj>: unencrypted username and password
    """
    class credentials:
        def __init__(self) -> None:
            self.usr = ''
            self.pwd = ''

        def __str__(self) -> str:
            return """Username: %s \nPassword: %s""" % (self.usr, self.pwd)
    # Open file and read in the encrypted password
    f = open(passFile, 'r')
    data = f.read().splitlines()
    f.close()
    username = data[0]
    encryption = data[1]
    # Decode the password and return the plaintext to caller
    encoded = encryption.encode('ascii')
    decoded = base64.b64decode(encoded)
    password = decoded.decode('ascii')
    login = credentials()
    login.usr = username
    login.pwd = password
    return login


def stressTest(credentials, iterations):
    """
    This function logs into ReadyRequest and attempts to submit multiple requests in order to test stability.
    Params:
        credentials <obj>   : SSO login credentials
        iterations  <int>   : number of requests to send
    Returns:
        None
    """
    class LabelMap:
        def __init__(self) -> None:
            self.text = ''
            self.btn_id = ''

        def __str__(self) -> str:
            return "Label: %s \nButton ID: %s" % (self.text, self.btn_id)

    def ssoLogin(credentials):
        """
        Logs into SSO using the provided credentials. Works consistently when 2fa is off or when device is trusted.
        Params:
            credentials <obj>   : SSO login credentials
        Returns:
            None
        """
        # Identify login form elements
        email = driver.find_element(by='id', value='email')
        continue_btn = driver.find_element(by='id', value='continueButton')
        # Enter login credentials and click sign in button
        email.send_keys('phan5@pdx.edu')
        continue_btn.click()
        time.sleep(2)
        password = driver.find_element(by='id', value='password')
        sign_in_btn = driver.find_element(by='id', value='signIn')
        password.send_keys(credentials.pwd)
        sign_in_btn.click()
        time.sleep(2)
        return

    console.log('Creating web driver...', style='bold')
    driver = initializeDriver()
    console.log('Navigating to ReadyRequest...', style='bold')
    driver.get(URL)
    # Pause for redirect
    time.sleep(2)
    # Check if we need to sign into SSO
    ssoLogin(credentials)
    try:
        for iteration in range(iterations):
            console.log("Request portal loaded...", style='bold')
            console.log('Grabbing tile...', style='bold')
            tileID = ''
            tile = ''
            for label in driver.find_elements(By.TAG_NAME, 'label'):
                if label.get_attribute('innerHTML') == 'Building Maintenance_IMPORT':
                    tileID = label.get_attribute('for')
            tile = driver.find_element(By.ID, tileID)
            tile.click()
            time.sleep(2)

            console.log('Filling out form...', style='bold')
            contactY = driver.find_element(By.NAME, 'primaryContactYN')
            contactY.click()
            bldgSpan = driver.find_element(
                By.CLASS_NAME, 'select2-selection--single')
            bldgSpan.click()
            time.sleep(1)
            bldg = ''
            for l in driver.find_elements(By.CLASS_NAME, 'select2-results__option'):
                if l.get_attribute('innerHTML') == 'USB - University Services Building':
                    bldg = l
            bldg.click()
            time.sleep(2)
            floorGroup = driver.find_element(By.ID, 'location|Floor|flrId-id')
            flrSpan = floorGroup.find_element(
                By.CLASS_NAME, 'select2-selection--single')
            flrSpan.click()
            time.sleep(1)
            floor = ''
            for l in driver.find_elements(By.CLASS_NAME, 'select2-results__option'):
                if l.get_attribute('innerHTML') == '(2) SECOND FLOOR':
                    floor = l
            floor.click()
            locDesc = driver.find_element(By.ID, 'locationDescription')
            locDesc.send_keys(f'TEST {iteration}')
            time.sleep(1)
            nextBtn = driver.find_element(
                By.XPATH, '//*[@id="requestScreenNext"]')
            nextBtn.click()
            time.sleep(2)

            # Select issue from radio buttons
            issue = ''
            for radio in driver.find_elements(By.TAG_NAME, 'input'):
                if radio.get_attribute('value') == 'Damaged Window':
                    issue = radio
            issue.click()
            moreInfo = driver.find_element(By.ID, 'addInfo')
            moreInfo.send_keys(f'This is stress test request #{iteration}')
            time.sleep(1)
            nextBtn = driver.find_element(
                By.XPATH, '//*[@id="requestScreenNext"]')
            nextBtn.click()
            time.sleep(2)
            reviewBtn = driver.find_element(By.ID, 'requestScreenReview')
            reviewBtn.click()
            time.sleep(2)
            submitBtn = driver.find_element(By.ID, 'requestScreenInsert')
            submitBtn.click()
            time.sleep(2)
    except NoSuchElementException:
        console.print('Error: No element found.', style='bold red')
    except TimeoutException:
        console.print('Error: Page took too long to load.', style='bold red')
    except ElementClickInterceptedException:
        console.print('Error: Failed to click the element.', style='bold red')
    except StaleElementReferenceException:
        console.print('Error: Stale reference.', style='bold red')
    except WebDriverException:
        console.print('Error: Webdriver detached.', style='bold red')


def main():
    credentials = decodePassword(os.path.join(UTILS_FOLDER, 'login.txt'))
    stressTest(credentials, 10)


def cli():
    main()


if __name__ == "__main__":
    main()
