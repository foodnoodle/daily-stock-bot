# 引入必要的函式庫
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def fetch_aaii_bull_bear_diff():
    """爬取 AAII 最新一筆看多與看空百分比，並計算差值"""
    TARGET_URL = "https://www.stockq.org/economy/aaiisurvey.php"
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 關鍵：無頭模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")    
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10)
        # 等待表格出現
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.economytable tr.row2")))
        # 取得最新一筆 row2 的所有欄位
        first_row = driver.find_element(By.CSS_SELECTOR, "table.economytable tr.row2")
        tds = first_row.find_elements(By.TAG_NAME, "td")
        # tds[1] = 看多, tds[3] = 看空
        bull = tds[1].text.strip().replace('%','')
        bear = tds[3].text.strip().replace('%','')
        bull = float(bull)
        bear = float(bear)
        diff = bull - bear
        return bull, bear, diff
    except Exception as e:
        return None, None, f"抓取過程中發生錯誤: {e}"
    finally:
        driver.quit()


