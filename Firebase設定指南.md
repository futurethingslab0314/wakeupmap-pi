# 🔥 Firebase 雲端同步設定指南

## 🎯 **為什麼需要 Firebase？**

甦醒地圖使用 Firebase 提供：
- 🌐 **雲端資料同步** - 樹莓派和網頁版資料共享
- 📊 **歷史記錄保存** - 所有甦醒記錄永久保存
- 📱 **多設備存取** - 任何設備都能查看歷史軌跡
- 🔒 **安全資料儲存** - 企業級安全保護

---

## 🚀 **步驟 1: 建立 Firebase 專案**

### **1.1 前往 Firebase Console**
```
https://console.firebase.google.com/
```

### **1.2 建立新專案**
1. 點擊「建立專案」
2. 輸入專案名稱 (例如: `wakeupmap-pi`)
3. 選擇是否啟用 Google Analytics (可選)
4. 點擊「建立專案」

### **1.3 設定 Firestore 資料庫**
1. 在專案控制台中，點擊「Firestore Database」
2. 點擊「建立資料庫」
3. 選擇「以測試模式啟動」(稍後可調整規則)
4. 選擇資料庫位置 (建議選擇最接近您的地區)

---

## 🔑 **步驟 2: 建立服務帳戶金鑰**

### **2.1 進入專案設定**
1. 點擊專案控制台左上角的齒輪圖示
2. 選擇「專案設定」
3. 切換到「服務帳戶」分頁

### **2.2 產生新的私密金鑰**
1. 確保選取了「Firebase Admin SDK」
2. 選擇語言：「Node.js」
3. 點擊「產生新的私密金鑰」
4. 下載 JSON 文件 (例如: `wakeupmap-pi-firebase-adminsdk-xxxxx.json`)

### **2.3 記錄必要資訊**
從下載的 JSON 文件中記錄：
```json
{
  "project_id": "your-project-id",
  "client_email": "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIB..."
}
```

---

## 🌐 **步驟 3: 設定 Web 應用程式**

### **3.1 新增 Web 應用程式**
1. 在專案概覽中，點擊「Web」圖示 (`</>`)
2. 註冊應用程式名稱 (例如: `wakeupmap-web`)
3. **不要**勾選「同時設定 Firebase Hosting」
4. 點擊「註冊應用程式」

### **3.2 記錄 Web 配置**
複製顯示的配置程式碼：
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdefghijklmnop"
};
```

---

## 🔧 **步驟 4: 在樹莓派上設定**

### **4.1 設定環境變數**
```bash
cd ~/wakeupmap-pi
nano .env
```

在文件中輸入：
```bash
# Firebase Admin SDK (後端認證)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
...您的完整私鑰內容...
-----END PRIVATE KEY-----"

# Firebase Web SDK (前端配置)
FIREBASE_WEB_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdefghijklmnop
```

### **4.2 載入環境變數**
```bash
# 永久載入環境變數
echo 'export $(cat ~/wakeupmap-pi/.env | xargs)' >> ~/.bashrc
source ~/.bashrc

# 驗證設定
echo "專案ID: $FIREBASE_PROJECT_ID"
echo "API Key: $FIREBASE_WEB_API_KEY"
```

---

## ✅ **步驟 5: 驗證設定**

### **5.1 測試 API 配置**
```bash
# 啟動測試服務器
cd ~/wakeupmap-pi
python3 -m http.server 8000 &

# 測試配置端點
curl http://localhost:8000/api/config

# 應該返回類似以下的 JSON:
# {
#   "apiKey": "AIzaSy...",
#   "authDomain": "your-project.firebaseapp.com",
#   "projectId": "your-project-id",
#   ...
# }
```

### **5.2 測試瀏覽器連接**
1. 開啟瀏覽器訪問 `http://localhost:8000/pi.html`
2. 按 F12 開啟開發者工具
3. 查看控制台，應該看到：
   ```
   🔥 開始初始化 Firebase...
   ✅ Firebase SDK 已準備就緒
   ```

### **5.3 測試資料寫入**
1. 在甦醒地圖中觸發一次 (按 Ctrl+H)
2. 前往 Firebase Console > Firestore Database
3. 檢查是否有新的資料記錄產生

---

## 🚨 **常見問題排除**

### **問題 1: 私鑰格式錯誤**
```bash
# 確保私鑰格式正確
# 1. 必須包含完整的 BEGIN 和 END 標記
# 2. 不能有額外的空格或特殊字符
# 3. 多行私鑰需要用引號包圍
```

### **問題 2: 環境變數未載入**
```bash
# 重新載入 shell 配置
source ~/.bashrc

# 或重新登入 SSH
exit
ssh yutingpi@raspberrypi
```

### **問題 3: API 配置返回錯誤**
```bash
# 檢查 Node.js 是否可用
node --version

# 如果沒有 Node.js，安裝它
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### **問題 4: Firestore 權限拒絕**
在 Firebase Console > Firestore Database > 規則中，暫時設定為：
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```
⚠️ **注意**: 這是測試設定，正式環境需要更嚴格的權限控制

---

## 🎉 **完成！**

現在您的甦醒地圖已經可以使用 Firebase 雲端同步功能了！

### **享受的功能：**
- 📱 **多設備同步** - 樹莓派和網頁版資料即時同步
- 📊 **無限歷史** - 所有甦醒記錄永久保存
- 🌍 **隨處存取** - 任何有網路的地方都能查看您的甦醒軌跡
- 🔐 **安全可靠** - Google 企業級基礎設施保護您的資料

Happy Wake-Up Mapping! 🍓✨
