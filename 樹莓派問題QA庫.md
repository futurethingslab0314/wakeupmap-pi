# 🍓 Raspberry Pi QA(本章節還未驗證與更新)


### **問題 1: Firebase 配置錯誤**
```bash
# 1. 檢查環境變數是否正確設定
env | grep FIREBASE

# 2. 檢查 .env 文件格式
cat ~/wakeupmap-pi/.env

# 3. 測試 Firebase 配置載入
curl http://localhost:8000/api/config
# 應該返回包含 projectId 等的 JSON

# 4. 檢查私鑰格式 (常見問題)
# 確保私鑰包含 -----BEGIN PRIVATE KEY----- 和 -----END PRIVATE KEY-----
# 確保沒有額外的空格或換行符問題
```

### **問題 3: JavaScript 錯誤**
```bash
# 在瀏覽器控制台檢查錯誤信息
# 常見問題：

# 1. Firebase 初始化失敗
# 檢查控制台是否有 "Firebase 初始化失敗" 錯誤
# 確認 API 配置端點可訪問

# 2. 地圖載入失敗
# 檢查網路連接，Leaflet 需要從 CDN 載入
```

### **問題 4: 地圖不顯示**
在瀏覽器控制台檢查：
```javascript
// 檢查地圖狀態
console.log('地圖狀態:', {
    leafletLoaded: typeof L !== 'undefined',
    mapInstance: !!window.mainInteractiveMap,
    mapContainer: !!document.getElementById('mainMapContainer')
});

// 如果地圖容器存在但地圖未初始化，手動初始化:
if (typeof L !== 'undefined' && !window.mainInteractiveMap) {
    console.log('嘗試重新初始化地圖...');
    // 可能需要重新載入頁面
}
```

### **問題 5: 功能按鈕無反應**
```javascript
// 檢查主要函數是否載入
console.log({
    startTheDay: typeof window.startTheDay,
    hiddenButtonControl: typeof window.hiddenButtonControl
});

// 如果函數不存在，檢查 pi-script.js 是否正常載入
// 查看瀏覽器網路面板確認文件載入狀態
```

### **問題 6: 網路相關問題**
```bash
# 檢查網路連接
ping 8.8.8.8

# 檢查 DNS 解析
nslookup googleapis.com

# 檢查防火牆設定 (如果使用)
sudo ufw status
```

### **問題 7: GPIO 按鈕無反應** (模式 B 用戶)
```bash
# 1. 檢查 GPIO 控制程式是否運行
ps aux | grep main_web_dsi

# 2. 檢查按鈕接線
# 確認按鈕連接到 GPIO18 和 GND

# 3. 測試 GPIO 權限
sudo usermod -a -G gpio $USER
# 需要重新登入才生效

# 4. 檢查 pigpio 守護程序 (如果使用)
sudo systemctl status pigpiod
sudo systemctl start pigpiod  # 如果未啟動

# 5. 手動測試 GPIO
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('GPIO18 狀態:', 'HIGH' if GPIO.input(18) else 'LOW')
GPIO.cleanup()
"
```

### **問題 8: Python 依賴安裝失敗**

#### **PEP 668 錯誤 (externally-managed-environment)**
```bash
# 新版 Raspberry Pi OS 需要使用虛擬環境

# 1. 確保已安裝必要系統套件
sudo apt install python3-full python3-venv python3-dev python3-setuptools -y

# 2. 創建並使用虛擬環境
cd ~/wakeupmap-pi/raspberrypi-dsi
python3 -m venv venv
source venv/bin/activate

# 3. 更新虛擬環境中的 pip
pip install --upgrade pip

# 4. 安裝依賴
pip install -r requirements.txt

# 5. 如果個別套件失敗，逐個安裝
pip install RPi.GPIO
pip install selenium
pip install pygame
pip install psutil
pip install requests

# 6. 如果 selenium 失敗，手動安裝瀏覽器驅動
sudo apt install chromium-browser chromium-chromedriver -y
```


### **問題 9: OpenAI TTS 語音問題** (可選功能)

```bash
# 1. 檢查 OpenAI API Key 是否正確
echo "API Key 前綴: ${OPENAI_API_KEY:0:7}"
# 應該顯示: sk-proj 或 sk-

# 2. 測試 OpenAI 連接
cd ~/wakeupmap-pi/raspberrypi-dsi
source venv/bin/activate
python3 -c "
import openai
import os
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✅ OpenAI 連接成功')
"

# 3. 檢查 TTS 設定
cat config.py | grep -A 5 "TTS_CONFIG"

# 4. 重新設定 TTS
python3 setup_openai_tts.py

# 5. 如果沒有 API Key，使用預設語音引擎
# 編輯 config.py，將 engine 改為 'festival'
```

### **問題 10: 回到原始狀態**
```bash
# 如果所有方法都失敗，重新下載:
cd ~
rm -rf wakeupmap-pi-backup
mv wakeupmap-pi wakeupmap-pi-backup  # 備份有問題的版本
git clone https://github.com/yutingcheng/wakeupmap-pi.git
cd wakeupmap-pi
```


### **問題 111: GPIO 實體按鈕無法正常工作** 

```bash
# 1. 檢查按鈕硬體連接
# 確認按鈕已正確連接到 GPIO 18 (實體針腳 12) 和 GND

# 2. 測試 GPIO 按鈕電路
python3 -c "
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('🔘 GPIO 18 按鈕測試 - 請按下按鈕...')
for i in range(20):
    if GPIO.input(18) == GPIO.LOW:
        print('✅ 按鈕觸發成功！電路連接正常')
        break
    time.sleep(0.5)
    print(f'等待中... ({i+1}/20)')
else:
    print('❌ 未偵測到按鈕觸發，請檢查接線')
GPIO.cleanup()
"

# 3. 檢查 GPIO 控制程式狀態
cd ~/wakeupmap-pi/raspberrypi-dsi
source venv/bin/activate
python3 main_web_dsi.py --test  # 測試模式

# 4. 常見接線問題排除：
# - 確認按鈕連接到 GPIO 18 (針腳 12)，不是其他針腳
# - 確認另一端連接到 GND (針腳 6, 9, 14, 20, 25, 30, 34, 39 任一個)
# - 確認使用瞬時按鈕 (momentary switch)，不是切換開關 (toggle switch)
# - 確認接線穩固，沒有鬆脫

# 5. 檢查權限問題
sudo usermod -a -G gpio $USER  # 將用戶加入 gpio 群組
# 重新登入後再測試

deactivate
```


## 🛠️ 故障排除

### 查看日誌
```bash
# 查看服務日誌
sudo journalctl -u wakeupmap-dsi -f

# 查看最近的錯誤
sudo journalctl -u wakeupmap-dsi --since "1 hour ago"
```

### 常見問題

#### 1. 螢幕無顯示
```bash
# 檢查DSI配置
cat /boot/config.txt | grep -A 10 "WakeUpMap DSI"

# 重新啟動圖形服務
sudo systemctl restart display-manager
```

#### 2. 按鈕無反應
```bash
# 測試按鈕
cd /home/pi/wakeupmap-dsi
python3 button_handler.py

# 檢查GPIO權限
groups pi | grep gpio
```

#### 3. 網路連線問題
```bash
# 測試API連線
python3 api_client.py

# 檢查網路連線
ping -c 3 google.com
```

#### 4. 字體顯示問題
```bash
# 重新安裝字體
sudo apt install -y fonts-noto-cjk
sudo fc-cache -fv
```