# 引入必要的函式庫
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


def fetch_fear_greed_meter():
    """爬取 FearGreedMeter 貪婪恐懼指標數值"""
    TARGET_URL = "https://feargreedmeter.com/"
    chrome_options = Options()
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-center.text-4xl.font-semibold.mb-1.text-white")))
        fear_greed_element = driver.find_element(By.CSS_SELECTOR, "div.text-center.text-4xl.font-semibold.mb-1.text-white")
        fear_greed_value = fear_greed_element.text
        return fear_greed_value
    except Exception as e:
        return f"抓取過程中發生錯誤: {e}"
    finally:
        driver.quit()
