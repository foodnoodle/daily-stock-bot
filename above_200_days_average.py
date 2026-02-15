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
    """爬取高於200日線股票比例 (v4.0: 終極穩定版 - Eager Load + Debug Port)"""
    TARGET_URL = "https://en.macromicro.me/series/22718/sp-500-200ma-breadth"
    
    chrome_options = Options()
    
    # --- 1. 載入策略優化 (關鍵！) ---
    # 設定為 'eager'：只要 DOM 載入完成就開始動作，不等待圖片或重型 JS 跑完
    # 這能大幅降低在複雜網頁崩潰的機率
    chrome_options.page_load_strategy = 'eager'
    
    # --- 2. 基礎 Headless 設定 ---
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # --- 3. Linux CI 環境防崩潰大全 (解決 0x56 錯誤) ---
    chrome_options.add_argument("--remote-debugging-port=9222") # [重要] 解決 CI 環境通訊崩潰
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor") # [重要] 停用合成器以防渲染崩潰
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false") # 不載入圖片

    # --- 4. 偽裝機制 ---
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
        # 因為用了 eager 模式，get 會很快返回
        driver.get(TARGET_URL)
        
        # 稍微等待一下讓動態內容生成
        time.sleep(random.uniform(3, 5))

        wait = WebDriverWait(driver, 20)
        # 只要看到這個數值元素出現，就立刻抓取並撤退
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.val")))
        
        above_200_days_element = driver.find_element(By.CSS_SELECTOR, "span.val")
        above_200_days_value = above_200_days_element.text
        return above_200_days_value
    except Exception as e:
        return f"抓取錯誤: {str(e)[:50]}"
    finally:
        driver.quit()
