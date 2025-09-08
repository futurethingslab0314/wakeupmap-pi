# 🍓 甦醒地圖 - 樹莓派版

這是甦醒地圖的樹莓派實體裝置版本，提供沉浸式的硬體體驗。

## 📋 功能特色

- 🔘 **實體按鈕控制**: GPIO18 按鈕觸發 [[memory:4254856]]
- 🎵 **OpenAI TTS 語音**: 高品質多語言語音播放
- 🖥️ **專屬 UI 設計**: 針對樹莓派螢幕最佳化 [[memory:5363728]]
- 🌅 **自動啟動**: 開機自動執行功能 [[memory:5363679]]
- 🎨 **像素風格**: 復古科技美學設計
- 🔊 **智能音頻**: Nova 模式多語言無縫播放

## 🛠️ 硬體需求

### 必要硬體
- **樹莓派 4B** (推薦 4GB+ RAM)
- **microSD 卡** (32GB+ Class 10)
- **實體按鈕** (連接到 GPIO18)
- **螢幕** (DSI 或 HDMI)
- **音響設備** (3.5mm 或 USB)

### 可選硬體
- **外殼** (保護和美觀)
- **散熱器** (長期運行穩定性)

## 📦 安裝步驟

### 1. 系統準備
```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝基本依賴
sudo apt install python3-pip git -y
```

### 2. 下載程式
```bash
# 克隆程式碼
git clone [your-pi-version-repo] ~/subjective-clock
cd ~/subjective-clock
```

### 3. 安裝依賴
```bash
# 自動安裝依賴
chmod +x fix-dependencies.sh
./fix-dependencies.sh

# 或手動安裝
pip3 install -r raspberrypi-dsi/requirements.txt
```

### 4. 設定 OpenAI TTS
```bash
cd raspberrypi-dsi
python3 setup_openai_tts.py
```

### 5. 建立桌面快捷方式 [[memory:5363679]]
```bash
chmod +x create-desktop-shortcut.sh
./create-desktop-shortcut.sh
```

## 📁 檔案結構

```
pi-version/
├── pi.html                 # Pi 專用介面
├── pi-script.js           # Pi 核心邏輯
├── pi-style.css           # Pi 專用樣式
├── raspberrypi-dsi/       # 核心程式目錄
│   ├── main_web_dsi.py   # 主控制程式
│   ├── web_controller_dsi.py
│   ├── audio_manager.py
│   ├── button_handler_pigpio.py
│   ├── config.py
│   └── modules/
├── api/                   # API 函數 (共用)
├── cities_data.json      # 城市資料庫
└── *.ico, *.png, *.svg   # 圖標資源
```

## 🚀 執行方式

### 手動執行
```bash
cd ~/subjective-clock/raspberrypi-dsi
python3 main_web_dsi.py
```

### 自動啟動
```bash
# 設定開機自啟
sudo systemctl enable wakeupclock.service
sudo systemctl start wakeupclock.service
```

### 桌面快捷方式
雙擊桌面上的「甦醒地圖」圖示即可啟動。

## 🎛️ 使用方式

1. **等待畫面**: 顯示 "PRESS THE BUTTON"
2. **按下按鈕**: 實體 GPIO18 按鈕
3. **載入處理**: 自動搜尋城市和生成內容
4. **結果展示**: 顯示位置、播放語音、展示故事
5. **自動循環**: 等待下次按鈕觸發

## 🔧 進階配置

### GPIO 按鈕設定
```python
# raspberrypi-dsi/config.py
BUTTON_CONFIG = {
    'pin': 18,          # GPIO 針腳
    'bounce_time': 200, # 防彈跳時間
    'hold_time': 1.0    # 長按時間
}
```

### 音頻設定
```python
# 音頻輸出配置
AUDIO_CONFIG = {
    'device': 'auto',   # 自動選擇音頻設備
    'volume': 0.8,      # 音量 (0.0-1.0)
    'speed': 1.0        # 播放速度
}
```

### 螢幕設定
修改 `pi-style.css` 中的響應式設計參數。

## 🐛 故障排除

### 常見問題

1. **按鈕無反應**
   ```bash
   # 檢查 GPIO 狀態
   gpio readall
   ```

2. **音頻無聲音**
   ```bash
   # 測試音頻
   aplay /usr/share/sounds/alsa/Front_Left.wav
   ```

3. **網路連線問題**
   ```bash
   # 檢查網路
   ping 8.8.8.8
   ```

4. **依賴問題**
   ```bash
   # 重新安裝依賴
   ./fix-dependencies.sh
   ```

### 日誌查看
```bash
# 查看主程式日誌
tail -f ~/subjective-clock/raspberrypi-dsi/logs/app.log

# 查看系統服務日誌
sudo journalctl -u wakeupclock -f
```

## 🎯 目標使用者

- 喜愛實體互動的使用者
- 追求沉浸式體驗的使用者
- 展示和教育用途
- 藝術裝置和創作

## 💡 創意用途

- **晨起儀式**: 每日第一件事的儀式感
- **冥想輔助**: 隨機地點的想像旅行
- **教育工具**: 地理和文化學習
- **藝術展示**: 互動藝術裝置

## 🔗 相關連結

- [網頁版](../web-version/) - 線上瀏覽器體驗
- [硬體組裝指南](./raspberrypi-dsi/README.md) - 詳細硬體設定
- [專案主頁](../README.md) - 完整專案說明

---

🍓 **提示**: Pi 版本專注於實體體驗和儀式感，適合日常使用和藝術展示。

