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

def fetch_above_200_days_average():
    """
    爬取高於200日線股票比例 (v5.0: 切換資料源至 Barchart)
    
    舊來源: MacroMicro (因 GitHub CI 環境顯卡相容性問題與反爬蟲導致持續崩潰)
    新來源: Barchart ($S5TH - S&P 500 Stocks Above 200-Day Average)
    """
    # Barchart 的 S&P 500 > 200DMA 指數代號是 $S5TH
    TARGET_URL = "https://www.barchart.com/stocks/quotes/$S5TH"
    
    chrome_options = Options()
    
    # --- 1. 載入策略 ---
    chrome_options.page_load_strategy = 'eager' # 不用等廣告載入完
    
    # --- 2. Headless 設定 ---
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # --- 3. 防崩潰參數 (保留以策安全) ---
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false") # 不載圖
    
    # --- 4. 偽裝機制 (Barchart 對 User-Agent 檢查較嚴格) ---
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
        
        # Barchart 有時會有 Cloudflare 驗證，稍微等待
        time.sleep(random.uniform(3, 6))

        wait = WebDriverWait(driver, 20)
        
        # Barchart 的價格通常顯示在 span 內，class 包含 status_last 或 last-change
        # 我們嘗試捕捉主要的價格區塊
        # CSS Selector: 尋找含有 'last-change' 的 span (這是 Barchart 慣用的價格 class)
        selector = "span.last-change"
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        
        price_element = driver.find_element(By.CSS_SELECTOR, selector)
        value = price_element.text.strip().replace('%', '') # 移除可能出現的 % 符號
        
        # 簡單驗證抓到的是不是數字
        try:
            float(value)
            return value
        except ValueError:
            return f"抓取內容非數值: {value}"

    except Exception as e:
        return f"Barchart 抓取錯誤: {str(e)[:100]}"
    finally:
        driver.quit()
