# 紫微斗數 AI 排盤（Streamlit 網頁版）

輸入陽曆生辰，自動排出完整紫微斗數十二宮命盤（十四主星、十四輔星、五行局、命身宮、
大限、生年四化、宮干飛星四化），支援指定西元年查詢該年**大限流年三層四化疊宮應事分析**
（本命／大限／流年四化同宮疊加提示，附白話論斷句），並提供可直接複製給 AI 分析的文字內容。

## 檔案結構

```
.
├── app.py            # Streamlit 網頁介面（入口檔）
├── ziwei.py           # 排盤核心邏輯（可獨立當 CLI 使用，已對照真實命盤驗證）
├── requirements.txt   # 部署所需套件
└── .gitignore
```

`ziwei.py` 也可以直接在終端機用：

```bash
python ziwei.py 1990-08-23 14:20 F 姓名
```

## 部署到 Streamlit Community Cloud（永久免費網址）

1. **建立 GitHub repository**，名稱建議直接用 `ziwei-ai-tw`（公開或私人皆可，
   Streamlit Cloud 免費方案兩者都支援）：
   ```bash
   git init
   git add app.py ziwei.py requirements.txt .gitignore README.md
   git commit -m "紫微斗數 AI 排盤"
   git branch -M main
   git remote add origin https://github.com/<你的帳號>/ziwei-ai-tw.git
   git push -u origin main
   ```
   > ⚠️ 資料夾裡的兩張 `.jpg` 截圖含有真實姓名與生辰，已在 `.gitignore` 中排除，
   > 不會被推上 GitHub；若不放心可先手動確認 `git status` 沒有列出它們。

2. 前往 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 帳號登入。

3. 點選 **"New app"** → 選擇你剛剛建立的 repository（`ziwei-ai-tw`）、分支 `main`、
   Main file path 填 `app.py`。展開 **"Advanced settings"** 或在網址欄位中，把
   **App URL** 填成 `ziwei-ai-tw` → 按 **Deploy**。

4. 約 1~2 分鐘後即可取得永久網址：
   **`https://ziwei-ai-tw.streamlit.app`**，可自由分享。
   （若該代稱已被別人註冊，Streamlit 會提示你更換，例如 `ziwei-ai-tw-2`。）

5. 之後只要 `git push` 更新程式碼，Streamlit Cloud 會自動重新部署。

## 本機測試

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 排盤邏輯依據

命宮／身宮定位、五虎遁年上起月、定紫微星訣、紫微／天府雙星系順逆位移表、
文昌文曲左輔右弼天魁天鉞祿存天馬擎羊陀羅火鈴空劫安星訣、十干四化表、
大限順逆行規則——皆為傳統紫微斗數安星訣公式，已用已知命盤逐項核對，
十四主星、十四輔星、生年四化、宮干飛星、大限歲數等全部欄位一致。

若出生時辰不確定或跨農曆閏月，排盤結果可能需要人工複核。本工具僅供命理
研究與參考，不構成任何人生決策建議。
