# 每日微光 Daily Glow（GitHub Pages + 每日內容更新版）

這是獨立、手機優先的繁體中文 PWA 網站。可以先用內建內容輪替；設定 OpenAI API Key 後，GitHub Actions 會每天（台灣時間約 00:10）搜尋來源、生成新的 5 則內容與 2 則世界知識，將 JSON 更新並部署到 GitHub Pages。

## 功能
- 每日五則：原創佳句、心理學、科學常識、哲學思考、今日微行動。
- 每日兩則世界之最／自然與地理冷知識，附來源連結。
- 簽到、連續天數、累積天數、週進度、月曆、心情、日記、收藏、已讀紀錄。
- 本機資料使用瀏覽器 localStorage；可匯出／匯入 JSON 備份。
- PWA manifest、iPhone 主畫面圖示、基本離線快取。
- GitHub Actions 定時生成內容與部署網站；API Key 只存在 GitHub Secrets，不放進前端。

## 重要限制
- **ChatGPT Plus 訂閱不等於 OpenAI API 額度。** 若要每天用 AI 搜尋並生成全新內容，需要另行建立 OpenAI API Key 並在 API 平台設定計費；實際費用依使用量而定。
- 未設定 `OPENAI_API_KEY` 時，網站仍能部署並以內建的 15 組內容依日期輪替，但這不等於每天都產生全新內容。排程會顯示提醒，不會把 API Key 放到瀏覽器。
- AI 生成內容仍可能出錯。程式會要求使用網路搜尋、要求來源 URL，並檢查來源是否出現在 API 回傳的搜尋來源清單；如果來源驗證或格式檢查失敗，當天更新會停止，避免覆蓋既有內容。正式公開前仍建議人工抽查。
- 簽到、日記、心情與收藏存在**目前這台裝置／這個瀏覽器**，不會自動同步其他裝置。清除 Safari 網站資料可能造成資料遺失，請定期匯出備份。
- 本網站是一般教育與自我覺察工具，不取代心理師、醫師或緊急服務。

## 部署到 GitHub Pages

### A. 建立 Repository
1. 登入 GitHub，建立一個新的 repository，名稱可用 `daily-glow`。
2. 初次操作最簡單的方式是設為 **Public**，並選擇不要自動加入 README（本專案已有 README）。
3. 將 ZIP 解壓縮，把解壓後的**所有檔案與資料夾內容**上傳到 repository 根目錄；不要只上傳 ZIP 檔。必須保留 `.github/workflows/site.yml`、`scripts/`、`content/` 等結構。
4. Commit 到 `main` 分支。

> 若使用 GitHub 網頁上傳檔案，請確認隱藏的 `.github` 資料夾也確實被上傳。使用電腦的 GitHub Desktop 或 Git 命令通常較容易保留完整資料夾結構。

### B. 開啟 Pages
1. 進入 repository 的 **Settings → Pages**。
2. 在 **Build and deployment → Source** 選擇 **GitHub Actions**。
3. 回到 **Actions**，確認 `Daily Glow - Update content and deploy` workflow 執行成功。
4. 成功後，到 Settings → Pages 查看網站網址，通常是 `https://你的帳號.github.io/daily-glow/`。

### C. 開啟真正的每日 AI 更新（可先跳過）
1. 到 OpenAI API 平台建立 API Key，並確認 API 專案已設定付款方式／額度。不要把 Key 貼到聊天、HTML 或 GitHub 程式碼中。
2. 在 GitHub repository 進入 **Settings → Secrets and variables → Actions → New repository secret**。
3. Name 填 `OPENAI_API_KEY`，Secret 填 API Key，儲存。
4. 到 **Actions → Daily Glow - Update content and deploy → Run workflow**，勾選 `Generate new sourced content now` 後執行一次測試。
5. 測試成功後，排程會在每天台灣時間約 00:10 執行；GitHub Actions 可能有少量排程延遲。

## 在 iPhone 加到主畫面
1. 用 iPhone 的 **Safari** 開啟部署後的 HTTPS 網站。
2. 點 Safari 的「分享」按鈕。
3. 選「加入主畫面」；若看不到，往下找「編輯動作」再加入。
4. 建議啟用「以網頁 App 方式打開」（若畫面有此選項），再點「加入」。
5. 之後從主畫面「每日微光」圖示開啟即可。

## 每日內容流程
- 排程：GitHub Actions 台灣時間每天約 00:10。
- 模型：`gpt-4.1-mini`（可在 workflow 的 `OPENAI_MODEL` 修改）。
- 搜尋範圍：優先可信機構與學術百科。
- 輸出：`content/today.json`，最近 30 天的主題與標題存於 `content/archive.json`，用於降低重複。
- 如果 API、來源檢查或格式驗證失敗，更新步驟會失敗並保留上一版內容；網站本身會退回內建日期輪替。

## 本機測試
在此資料夾執行：

```bash
python -m http.server 8000
```

再用瀏覽器開啟 `http://localhost:8000/`。PWA／Service Worker 測試需使用 localhost 或 HTTPS。

## 專案結構
- `index.html`：網站與互動功能。
- `manifest.json`：PWA 設定。
- `sw.js`：靜態檔快取與每日 JSON 的 network-first 更新策略。
- `icon.svg`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`：圖示。
- `content/today.json`：當日生成內容。
- `content/archive.json`：最近內容標題，用來降低重複。
- `scripts/generate_daily.py`：呼叫 Responses API 網路搜尋並驗證來源。
- `.github/workflows/site.yml`：GitHub Pages 部署與每日更新排程。


## 重要：上傳檔案時

請解壓縮 ZIP，進入 `daily-glow` 資料夾後，將**資料夾內的所有檔案與子資料夾**上傳到 Repository 根目錄；不要把外層 `daily-glow` 資料夾再包一層，也不要只上傳 ZIP。必須保留隱藏的 `.github/workflows/site.yml`。
