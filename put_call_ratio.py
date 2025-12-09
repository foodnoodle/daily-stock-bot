# 引入必要的函式庫
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def fetch_total_put_call_ratio():
    """爬取 CBOE TOTAL PUT/CALL RATIO 數值"""
    TARGET_URL = "https://www.cboe.com/us/options/market_statistics/daily/"
    chrome_options = Options()
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    chrome_options.add_argument('--lang=zh-TW,zh;q=0.9,en;q=0.8')
    chrome_options.add_argument('--window-size=1200,900')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    import time, random
    try:
        driver.get(TARGET_URL)
        time.sleep(random.uniform(2, 4))
        wait = WebDriverWait(driver, 15)
        # 等待 TOTAL PUT/CALL RATIO 數值出現
        wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'TOTAL PUT/CALL RATIO')]/following-sibling::td[1]")))
        ratio_elem = driver.find_element(By.XPATH, "//td[contains(text(), 'TOTAL PUT/CALL RATIO')]/following-sibling::td[1]")
        ratio_value = ratio_elem.text.strip()
        return ratio_value
    except Exception as e:
        return f"抓取過程中發生錯誤: {e}"
    finally:
        driver.quit()
