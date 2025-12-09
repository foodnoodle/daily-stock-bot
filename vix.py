# 引入必要的函式庫
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def fetch_vix_index():
    import time, random
    """爬取 Google 財經 VIX 指數最新數值"""
    TARGET_URL = "https://www.google.com/finance/quote/VIX:INDEXCBOE?sa=X&ved=2ahUKEwiDl7b9ut-OAxVCn68BHQwuHKEQ3ecFegQIKBAb"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 偽裝常見瀏覽器資訊
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    chrome_options.add_argument('--lang=zh-TW,zh;q=0.9,en;q=0.8')
    chrome_options.add_argument('--window-size=1200,900')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # 禁用自動化標記
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # 移除 webdriver 屬性
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    try:
        driver.get(TARGET_URL)
        # 模擬真人瀏覽延遲
        time.sleep(random.uniform(2, 4))
        wait = WebDriverWait(driver, 15)
        # 等待 VIX 數值元素出現，且數值不是0
        def vix_value_loaded(driver):
            elem = driver.find_element(By.CSS_SELECTOR, "div.YMlKec.fxKbKc")
            val = elem.text.strip()
            return val not in ("0", "0.0", "")
        wait.until(vix_value_loaded)
        # 再隨機延遲
        time.sleep(random.uniform(1, 2))
        vix_elem = driver.find_element(By.CSS_SELECTOR, "div.YMlKec.fxKbKc")
        vix_value = vix_elem.text.strip()
        return vix_value
    except Exception as e:
        return f"抓取過程中發生錯誤: {e}"
    finally:
        driver.quit()

