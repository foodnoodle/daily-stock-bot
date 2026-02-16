# --- treasury_yield.py ---
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

def fetch_10y_treasury_yield():
    """
    爬取 Google Finance 的 10年期公債殖利率 (TNX)
    替代不穩定的 Yahoo Finance ^TNX
    """
    # Google Finance 的 TNX 代號頁面
    TARGET_URL = "https://www.google.com/finance/quote/TNX:INDEXCBOE"
    
    chrome_options = Options()
    # 使用新版 Headless 模式
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 偽裝機制
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
        # 隨機等待，模擬人類
        time.sleep(random.uniform(2, 4))
        
        wait = WebDriverWait(driver, 15)
        # Google Finance 統一的價格 CSS Selector (與 SKEW 相同)
        # class="YMlKec fxKbKc" 是大字體價格
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.YMlKec.fxKbKc")))
        
        price_element = driver.find_element(By.CSS_SELECTOR, "div.YMlKec.fxKbKc")
        raw_value = price_element.text.strip()
        
        # 處理數值: Google Finance 顯示如 "42.50"，需除以 10 轉換為 "4.25"
        clean_val = raw_value.replace(',', '')
        final_yield = float(clean_val) / 10.0
        
        return f"{final_yield:.2f}"

    except Exception as e:
        return f"錯誤: {str(e)[:50]}"
    finally:
        driver.quit()
