# 引入必要的函式庫
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import random

def fetch_fear_greed_meter():
    """爬取 FearGreedMeter 貪婪恐懼指標 (v2.0: 修復崩潰)"""
    TARGET_URL = "https://feargreedmeter.com/"
    
    chrome_options = Options()
    # --- 關鍵修正：使用新版 Headless 模式 ---
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # --- 關鍵修正：加入偽裝機制 ---
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 移除 webdriver 標記
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })

    try:
        driver.get(TARGET_URL)
        time.sleep(random.uniform(2, 4)) # 隨機等待
        wait = WebDriverWait(driver, 15)
        
        # 嘗試尋找數值
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-center.text-4xl.font-semibold.mb-1.text-white")))
        fear_greed_element = driver.find_element(By.CSS_SELECTOR, "div.text-center.text-4xl.font-semibold.mb-1.text-white")
        return fear_greed_element.text
    except Exception as e:
        return f"抓取錯誤: {str(e)[:100]}"
    finally:
        driver.quit()
