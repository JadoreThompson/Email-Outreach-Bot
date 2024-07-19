from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time


def client_scraper():
    driver = webdriver.Chrome()
    base_url = "https://www.google.com/maps/search/business+near+me"


    industries = ['restaurants', 'dental+practices']
    wait = WebDriverWait(driver, timeout=10)
    for industry in industries:
        driver.get(base_url.replace('business', industry))

        try:
            accept_btn = wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button")))
            accept_btn.click()
        except:
            pass

        time.sleep(9999999)

    driver.quit()