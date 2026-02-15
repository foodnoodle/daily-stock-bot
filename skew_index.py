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

def fetch_skew_index():
    """爬取 SKEW 黑天鵝指標 (v2.0: 修復崩潰 + Google 防擋)"""
    # 注意：Google Finance 的網址
    TARGET_URL = "https://www.google.com/finance/quote/SKEW:INDEXCBOE"
    
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
        # 模擬人類行為：Google 比較敏感，多等一下
        time.sleep(random.uniform(3, 5))
        
        wait = WebDriverWait(driver, 15)
        # 等待數值出現
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.YMlKec.fxKbKc")))
        
        skew_element = driver.find_element(By.CSS_SELECTOR, "div.YMlKec.fxKbKc")
        skew_value = skew_element.text.strip()
        return skew_value
    except Exception as e:
        return f"抓取錯誤: {str(e)[:100]}"
    finally:
        driver.quit()
