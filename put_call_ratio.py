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

def fetch_total_put_call_ratio():
    """爬取 CBOE TOTAL PUT/CALL RATIO 數值"""
    TARGET_URL = "https://www.cboe.com/us/options/market_statistics/daily/"
    
    chrome_options = Options()
    # --- 關鍵修改：加入 Headless 設定 ---
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # ---------------------------------
    
    # 保留原本的偽裝設定
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    chrome_options.add_argument('--lang=zh-TW,zh;q=0.9,en;q=0.8')
    chrome_options.add_argument('--window-size=1920,1080') # 建議設大一點確保元素可見
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 防止被偵測的腳本
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })

    try:
        driver.get(TARGET_URL)
        time.sleep(random.uniform(2, 4)) # 等待載入
        
        wait = WebDriverWait(driver, 15)
        # 等待 TOTAL PUT/CALL RATIO 數值出現
        # 定位方式：找到文字為 "TOTAL PUT/CALL RATIO" 的 td，再找它下一個 td
        target_xpath = "//td[contains(text(), 'TOTAL PUT/CALL RATIO')]/following-sibling::td[1]"
        wait.until(EC.presence_of_element_located((By.XPATH, target_xpath)))
        
        ratio_elem = driver.find_element(By.XPATH, target_xpath)
        ratio_value = ratio_elem.text.strip()
        return ratio_value
    except Exception as e:
        return f"抓取過程中發生錯誤: {e}"
    finally:
        driver.quit()
