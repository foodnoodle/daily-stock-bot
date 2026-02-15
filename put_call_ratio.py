# --- put_call_ratio.py (v6.1: Selenium Headless New + Anti-bot) ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import datetime
import time
import random

def fetch_put_call_ratio():
    """
    [終極版] 抓取 CBOE Put/Call Ratio
    策略：使用 Selenium 開啟帶有日期參數的網址 (?dt=YYYY-MM-DD)
    解決了 requests 被擋的問題，同時保留了自動往回找日期的功能。
    """
    base_url = "https://www.cboe.com/us/options/market_statistics/daily/"
    
    chrome_options = Options()
    # --- 關鍵修正：使用新版 Headless 模式 ---
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # --- 關鍵修正：加入偽裝機制 ---
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 啟動瀏覽器
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 移除 webdriver 標記
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
    except Exception as e:
        return f"驅動啟動失敗: {e}"

    try:
        # 2. 自動回溯機制 (最多找 5 天)
        for i in range(5):
            try:
                # 計算日期 (今天, 昨天, 前天...)
                target_date = datetime.date.today() - datetime.timedelta(days=i)
                date_str = target_date.strftime("%Y-%m-%d")
                
                # 組裝網址，讓 Selenium 前往指定日期
                target_url = f"{base_url}?dt={date_str}"
                
                driver.get(target_url)
                
                # 模擬人類行為：稍微隨機等待一下
                time.sleep(random.uniform(1.5, 3))
                
                # 等待網頁載入 (最多 5 秒)
                wait = WebDriverWait(driver, 5)
                
                # 3. 檢查是否有資料
                # XPath: 尋找文字包含 "TOTAL PUT/CALL RATIO" 的欄位，並抓它隔壁的數值
                xpath = "//td[contains(text(), 'TOTAL PUT/CALL RATIO')]/following-sibling::td[1]"
                
                try:
                    # 等待元素出現
                    wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    element = driver.find_element(By.XPATH, xpath)
                    val = element.text.strip()
                    
                    if val:
                        return val  # 成功抓到！回傳並結束
                except:
                    # 如果找不到元素 (Timeout)，代表這一天沒資料，繼續迴圈跑下一天
                    continue
                    
            except Exception:
                continue
        
        return "抓取失敗 (多日無資料)"

    except Exception as e:
        return f"執行錯誤: {str(e)[:100]}"
        
    finally:
        # 釋放記憶體
        if 'driver' in locals():
            driver.quit()
