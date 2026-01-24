# 📈 Daily Stock Index Bot (美股全方位情緒機器人)

這是一個基於 Python 的自動化財經分析機器人，運行於 **GitHub Actions**。它每天自動抓取華爾街關注的關鍵指標（宏觀、技術、籌碼、情緒），進行多空判讀，並將精美的報告發送至 **Discord**，同時將數據永久保存為 CSV 以供未來回測或 AI 訓練使用。

<img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/207b6f20-a965-48e0-9aba-402d627165f7" />

## ✨ 主要功能 (Key Features)

* **全自動運行**：每天早上 08:00 (台灣時間) 自動執行，無需人工干預。
* **多維度分析**：
    * 🌊 **宏觀 (Macro)**：10年債殖利率、美元指數 (DXY)、比特幣 (BTC)、高收益債 (HYG)。
    * 🏗️ **結構 (Structure)**：羅素2000 (IWM)、半導體 (SOXX)、風險胃口 (XLY/XLP)。
    * 🌡️ **情緒 (Sentiment)**：VIX 波動率、CNN 恐懼貪婪、RSI 指標、200日線比例。
    * 🐳 **籌碼 (Smart Money)**：Put/Call Ratio、NAAIM 經理人持倉、SKEW 黑天鵝指數、AAII 散戶情緒。
* **智慧抓取技術**：
    * 混合架構：結合 `yfinance` (API) 與 `Selenium` (爬蟲)。
    * **自動回溯**：若 Put/Call Ratio 當日無資料，會自動往回尋找最近的交易日，確保數據不開天窗。
    * **模組化設計**：程式碼分離為 `fetchers`, `utils`, `config`，易於維護與擴充。
* **視覺化報告**：Discord 卡片具備動態顏色（綠/紅/灰）與動態縮圖，並有完美的版面間距。
* **數據累積**：自動將每日數據清洗並寫入 `data/history.csv`，並自動 Commit 回 GitHub 倉庫。

## 📂 專案結構

* `main.py`: 程式入口，負責排程與呼叫。
* `config.py`: **設定檔**。所有指標的開關、判斷門檻、顯示名稱、圖片素材都在這裡調整。
* `data_fetchers.py`: **抓取層**。負責與 Yahoo Finance 溝通及計算技術指標。
* `utils.py`: **工具層**。負責多空邏輯判斷、Discord 排版發送、CSV 格式化存檔。
* `put_call_ratio.py`: 獨立的 Selenium 爬蟲模組，含反爬蟲偽裝與日期回溯邏輯。
* `.github/workflows/daily_run.yml`: 自動化排程設定檔。

## 🚀 安裝與設定 (Setup)

1.  **Fork 此專案** 到您的 GitHub。
2.  **設定 Discord Webhook**：
    * 進入 Repo 的 `Settings` -> `Secrets and variables` -> `Actions`。
    * 新增 Repository secret：`DISCORD_WEBHOOK_URL`，填入您的 Discord Webhook 網址。
3.  **開啟寫入權限** (重要！否則無法存檔 CSV)：
    * 進入 `Settings` -> `Actions` -> `General`。
    * 在 `Workflow permissions` 勾選 **Read and write permissions**。
4.  **手動測試**：
    * 到 `Actions` 分頁，選擇 `Daily Stock Index Fetcher`，點擊 `Run workflow`。

## 📊 數據欄位說明 (CSV)

| 欄位 | 說明 |
| :--- | :--- |
| **SPX_Price** | S&P 500 收盤價 |
| **Risk_Ratio** | 風險胃口 (XLY / XLP) |
| **10Y_Yield** | 美國 10 年期公債殖利率 |
| **AAII_Diff** | 散戶情緒差值 (看多% - 看空%) |
| ... | (包含所有 config 中定義的指標) |

## 🛠️ 技術堆疊

* Python 3.11
* Libraries: `yfinance`, `pandas`, `selenium`, `requests`
* CI/CD: GitHub Actions
  
---
## Discord 訊息截圖
<table>
  <tr>
    <td><img width="348" height="595" alt="image" src="https://github.com/user-attachments/assets/e6237e1b-a263-4c0d-9424-eedbee20fe9f" /></td>
    <td><img width="351" height="604" alt="image" src="https://github.com/user-attachments/assets/858f2f50-256c-41ac-b48e-2d6adb743d3b" /></td>
    <td><img width="354" height="602" alt="image" src="https://github.com/user-attachments/assets/a80abd51-0597-47c3-bffc-f3d58d27b8e8" /></td>
  </tr>
</table>

---
*Created by Github Actions Auto Bot*
