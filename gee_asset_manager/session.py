__copyright__ = """

    Copyright 2019 Lukasz Tracewski

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
__license__ = "Apache 2.0"


import time
import logging
import requests
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_google_session(url: str, account_name: str, password: str, browser: str, headless: bool) -> requests.session:
    """
    Get Google session object. The function will use Selenium and selected web driver to login to the
    account and create a session object.
    :param url: address to use
    :param account_name: name of the account (user name)
    :param password: password for the account
    :param browser: which browser to use
    :param headless: run as headless
    :return: session object
    """
    options = Options()
    if headless:
        options.add_argument('--headless')

    if browser == 'Chrome':
        driver = webdriver.Chrome(options=options)
    else:
        raise NotImplemented('{} browser is not implemented.'.format(browser))

    try:
        driver.get(url)
        driver.implicitly_wait(4)
        if headless:
            logging.info('Running browser in headless mode')
            username_el = driver.find_element_by_xpath('//*[@id="Email"]')
            username_el.send_keys(account_name)
            driver.find_element_by_id("next").click()
            driver.implicitly_wait(4)
            password_el = driver.find_element_by_xpath('//*[@id="Passwd"]')
            password_el.send_keys(password)
            driver.find_element_by_id("signIn").click()
        else:
            logging.info('Running the browser in normal mode')
            username_el = driver.find_element_by_xpath('//*[@id="identifierId"]')
            username_el.send_keys(account_name)
            driver.find_element_by_id("identifierNext").click()
            driver.implicitly_wait(4)
            password_el = driver.find_element_by_name("password")
            password_el.send_keys(password)
            time.sleep(1)
            next_el = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.ID, "passwordNext"))
            )
            next_el.click()

        gee_code = WebDriverWait(driver, 100).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="logo"]/img'))
        )

        session = _get_session(driver)
    finally:
        driver.close()
        logging.info('Browser closed.')
    return session


def _get_session(driver):
    cookies = driver.get_cookies()
    session = requests.session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    return session

