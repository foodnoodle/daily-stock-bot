# 引入必要的函式庫
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def fetch_above_200_days_average():
    """爬取高於200日線股票比例"""
    TARGET_URL = "https://en.macromicro.me/series/22718/sp-500-200ma-breadth"
    
    chrome_options = Options()
    # --- 關鍵修改：加入 Headless 設定 ---
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # ---------------------------------
    
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10)
        # 等待數值出現
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.val")))
        
        above_200_days_element = driver.find_element(By.CSS_SELECTOR, "span.val")
        above_200_days_value = above_200_days_element.text
        return above_200_days_value
    except Exception as e:
        return f"抓取過程中發生錯誤: {e}"
    finally:
        driver.quit()
