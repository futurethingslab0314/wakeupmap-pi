# API 金鑰統一管理說明

## 🔑 統一管理原則

現在所有 API 金鑰都統一在 `.env` 檔案中管理，避免多處設定的混亂。

## 📁 設定位置

### 主要設定：`.env` 檔案
```bash
# OpenAI API 金鑰
OPENAI_API_KEY=sk-your-openai-api-key-here

# Firebase 設定
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY=/path/to/private_key.pem

# 使用者設定
USER_NAME=your-username
```

### 自動讀取：`config.py`
```python
# 自動從環境變數讀取，無需手動設定
TTS_CONFIG = {
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),  # 從 .env 讀取
    'openai_model': 'tts-1-hd',
    'openai_voice': 'nova',
    # ...
}
```

## 🔄 設定流程

### 方法 1：手動編輯 .env
```bash
# 編輯 .env 檔案
nano .env

# 添加或修改
OPENAI_API_KEY=sk-your-actual-api-key-here

# 重新載入環境變數
source .env
```

### 方法 2：使用設定腳本
```bash
# 執行自動設定腳本
cd raspberrypi-dsi
python3 setup_openai_tts.py

# 腳本會自動：
# 1. 檢查現有的 OPENAI_API_KEY
# 2. 提示輸入新的 API 金鑰
# 3. 更新 .env 檔案
# 4. 測試連接
```

## ✅ 驗證設定

### 檢查環境變數
```bash
echo "OpenAI API Key: ${OPENAI_API_KEY:0:20}..."
```

### 測試 OpenAI 連接
```bash
python3 -c "
import openai
import os
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✅ OpenAI 連接成功')
"
```

### 測試 TTS 功能
```bash
cd raspberrypi-dsi
python3 -c "
from config import TTS_CONFIG
print(f'OpenAI API Key: {TTS_CONFIG[\"openai_api_key\"][:20]}...')
print(f'TTS Engine: {TTS_CONFIG[\"engine\"]}')
print(f'Voice: {TTS_CONFIG[\"openai_voice\"]}')
"
```

## 🚫 避免的錯誤

### ❌ 不要這樣做
```python
# 不要在 config.py 中硬編碼
TTS_CONFIG = {
    'openai_api_key': 'sk-your-key-here',  # ❌ 不要硬編碼
}
```

### ✅ 正確做法
```python
# 使用環境變數
TTS_CONFIG = {
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),  # ✅ 從環境變數讀取
}
```

## 🔧 故障排除

### 問題：API 金鑰未生效
```bash
# 1. 檢查 .env 檔案是否存在
ls -la .env

# 2. 檢查環境變數是否載入
echo $OPENAI_API_KEY

# 3. 重新載入環境變數
source .env

# 4. 重新啟動程式
```

### 問題：config.py 讀取不到環境變數
```bash
# 確保在正確的目錄執行
cd /path/to/wakeupmap-pi

# 確保 .env 檔案在專案根目錄
ls -la .env

# 手動載入環境變數
export OPENAI_API_KEY="your-key-here"
```

## 📝 總結

- **單一來源**：所有 API 金鑰都在 `.env` 檔案中
- **自動讀取**：`config.py` 自動從環境變數讀取
- **易於管理**：只需要修改一個檔案
- **安全性**：`.env` 檔案在 `.gitignore` 中，不會被提交到版本控制
