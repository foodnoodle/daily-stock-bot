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

def fetch_aaii_bull_bear_diff():
    """爬取 AAII 最新一筆看多與看空百分比，並計算差值 (v2.0: 修復崩潰)"""
    TARGET_URL = "https://www.stockq.org/economy/aaiisurvey.php"
    
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
        # 等待表格出現
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.economytable tr.row2")))
        # 取得最新一筆 row2 的所有欄位
        first_row = driver.find_element(By.CSS_SELECTOR, "table.economytable tr.row2")
        tds = first_row.find_elements(By.TAG_NAME, "td")
        # tds[1] = 看多, tds[3] = 看空
        bull = float(tds[1].text.strip().replace('%',''))
        bear = float(tds[3].text.strip().replace('%',''))
        diff = bull - bear
        return bull, bear, diff
    except Exception as e:
        return None, None, f"抓取錯誤: {str(e)[:100]}"
    finally:
        driver.quit()
