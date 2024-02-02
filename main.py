import time

from selenium.common import WebDriverException

from config import *
from models import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from chromedriver_py import binary_path


def launch_paylocity(service: webdriver.ChromeService):
    """
    Start a new Chrome session and login to Paylocity
    :param service: The Selenium Chrome service to get the ChromeDriver
    :return: A new Chrome session with Paylocity logged in
    """

    driver = webdriver.Chrome(service=service)
    driver.get(PAYLOCITY_LOGIN_URL)
    driver.implicitly_wait(10)

    # Login
    company_id = driver.find_element(By.ID, "CompanyId")
    company_id.send_keys(PAYLOCITY_COMPANY_ID)
    username = driver.find_element(By.ID, "Username")
    username.send_keys(PAYLOCITY_USERNAME)
    password = driver.find_element(By.ID, "Password")
    password.send_keys(PAYLOCITY_PASSWORD)
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()

    # Security question
    question = driver.find_element(By.CSS_SELECTOR, "label[for='ChallengeAnswer']")
    question_text = question.text.lower()

    for security_question in PAYLOCITY_SECURITY_QUESTIONS:
        if security_question["question"].lower() in question_text:
            answer = driver.find_element(By.ID, "ChallengeAnswer")
            answer.send_keys(security_question["answer"])
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            break

    return driver


def get_clock_status(driver: webdriver.Chrome) -> ClockStatus:
    """
    Get the current clock status from Paylocity. The driver should be logged in to Paylocity.
    :param driver: A logged in Chrome session
    :return: The current clock status
    """

    driver.get(PAYLOCITY_WEBTIME_URL)
    time.sleep(2)

    try:
        # We use the background color to determine if the button is highlighted

        clock_in_button = driver.find_element(By.CSS_SELECTOR, "button[data-automation-id='punch-button-ClockIn']")
        is_selected = "0, 0, 0" not in driver.execute_script("return window.getComputedStyle(arguments[0], null)['background-color'];", clock_in_button)
        if is_selected:
            return ClockStatus.In

        clock_out_button = driver.find_element(By.CSS_SELECTOR, "button[data-automation-id='punch-button-ClockOut']")
        is_selected = "0, 0, 0" not in driver.execute_script("return window.getComputedStyle(arguments[0], null)['background-color'];", clock_out_button)
        if is_selected:
            return ClockStatus.Out

        return ClockStatus.Unknown
    except WebDriverException as ex:
        print("Failed to get clock status: ", ex)
        return ClockStatus.Unknown


def handle_clock_in_out(driver: webdriver.Chrome, action: ClockAction):
    """
    Clock in or out, depending on the action. The driver should be logged in to Paylocity.
    :param driver: A logged in Chrome session
    :param action: The action to perform
    """

    driver.get("https://webtime2.paylocity.com/WebTime/v3/Employee")

    if action == ClockAction.In:
        clock_in = driver.find_element(By.CSS_SELECTOR, "button[data-automation-id='punch-button-ClockIn']")
        clock_in.click()
    elif action == ClockAction.Out:
        clock_out = driver.find_element(By.CSS_SELECTOR, "button[data-automation-id='punch-button-ClockOut']")
        clock_out.click()


def shutdown(driver: webdriver.Chrome):
    """
    Close the Chrome session
    :param driver: The Chrome session to close
    """
    driver.get(PAYLOCITY_WEBTIME_LOGOUT_URL)
    time.sleep(2)
    driver.quit()


def startup():
    service = webdriver.ChromeService(executable_path=binary_path)
    driver = launch_paylocity(service)
    status = get_clock_status(driver)
    if status == ClockStatus.In:
        handle_clock_in_out(driver, ClockAction.Out)
    elif status == ClockStatus.Out:
        handle_clock_in_out(driver, ClockAction.In)
    else:
        print("Unknown clock status")
    shutdown(driver)
    service.stop()


if __name__ == "__main__":
    startup()
