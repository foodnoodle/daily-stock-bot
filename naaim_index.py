# 引入必要的函式庫
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def fetch_naaim_exposure_index():
    """爬取 NAAIM 曝險指數"""
    TARGET_URL = "https://naaim.org/programs/naaim-exposure-index/"
    
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
        # 等待元素出現
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#brxe-ymwzia.brxe-shortcode")))
        
        naaim_element = driver.find_element(By.CSS_SELECTOR, "div#brxe-ymwzia.brxe-shortcode")
        naaim_value = naaim_element.text
        return naaim_value
    except Exception as e:
        return f"抓取過程中發生錯誤: {e}"
    finally:
        driver.quit()
