# Raspberry Pi Square Display

這是一份給「第一次使用 Raspberry Pi」的人看的安裝手冊。

這個版本會：

- 顯示地圖
- 顯示故事文字
- 在故事出現時自動使用瀏覽器 TTS 朗讀
- 讓 Raspberry Pi 的按鈕負責啟動新的紀錄流程
- 讓電位器控制地圖 zoom in / zoom out
- 讓 4 段波段開關回看最新的歷史紀錄

如果你是第一次拿到一台新的 Raspberry Pi，請直接從下面第一章開始照做。

---

## 你需要準備

- Raspberry Pi
- Raspberry Pi OS
- 網路連線
- 一個螢幕
- 一個按鈕
- 一個電位器
- 一個 4 段波段開關
- 一個 speaker
- GitHub 帳號與 `yutingpi` 專案網址

---

## 1. 硬體接線

### 1-1. 按鈕

按鈕是用來啟動新的紀錄流程，也就是畫面上看到的 `Press the Button`。

- **GPIO：`GPIO18`**
- **接法：** `GPIO18` -> 按鈕 -> `GND`

這個腳位和你原本的 DSI 版本一致。

### 1-2. 電位器

電位器用來控制地圖 zoom in / zoom out。

> 注意：Raspberry Pi 沒有內建類比輸入，所以電位器不能直接接單一 GPIO。

你需要使用 **MCP3008** ADC。

- 電位器中間腳（wiper） -> `MCP3008 CH0`
- `MCP3008` 供電 -> `3.3V`
- `MCP3008` 連接 Pi 的 `SPI0`

#### `SPI0` 要接到 MCP3008 哪一隻腳？

這一段是最重要的，因為 Pi 的 `SPI0` 不是只接一條線，而是要對到 MCP3008 的 4 個通訊腳位。

| Raspberry Pi `SPI0` | Pi 腳位名稱 | 接到 MCP3008 | MCP3008 腳位 |
| --- | --- | --- | --- |
| `GPIO11` | `SCLK` | `CLK` | `13` |
| `GPIO10` | `MOSI` | `DIN` | `11` |
| `GPIO9` | `MISO` | `DOUT` | `12` |
| `GPIO8` | `CE0` | `CS/SHDN` | `10` |

另外還要接供電與接地：

| 供電 / GND | 接到 MCP3008 | MCP3008 腳位 |
| --- | --- | --- |
| `3.3V` | `VDD` | `16` |
| `3.3V` | `VREF` | `15` |
| `GND` | `AGND` | `14` |
| `GND` | `DGND` | `9` |

如果你只是先接最基本版本，`CH1 ~ CH7` 可以先不接。

### 1-3. 4 段波段開關

4 段波段開關是用來切換「從最新位置往回推的歷史紀錄」。

邏輯如下：

- 第 1 段 = 最新 visit
- 第 2 段 = 往回 1 筆
- 第 3 段 = 往回 2 筆
- 第 4 段 = 往回 3 筆

#### 建議接法

你可以讓 4 個檔位各自接到 4 個 GPIO 輸入腳，然後共地：

- 第 1 段 -> `GPIO22`
- 第 2 段 -> `GPIO23`
- 第 3 段 -> `GPIO24`
- 第 4 段 -> `GPIO25`
- 共用端 -> `GND`

#### 這個開關怎麼用

當開關切到不同段位時，系統會直接切換到對應的歷史紀錄，並自動顯示與朗讀。

> 注意：Raspberry Pi 的 GPIO 只能讀開關狀態，真正把這個狀態送進畫面的，是 Pi 上的程式橋接。這個 square 介面已經提供 `window.setBandSwitchPosition(position)` 和 `window.setHistoryOffset(offset)` 讓你接。

### 1-3. Raspberry Pi 需要接的 SPI 腳位

| Pi 腳位 | 功能 |
| --- | --- |
| `GPIO11` | `SCLK` |
| `GPIO10` | `MOSI` |
| `GPIO9` | `MISO` |
| `GPIO8` | `CE0` |

### 1-4. 簡單總表

| 功能 | 接法 |
| --- | --- |
| 按鈕 | `GPIO18` -> 按鈕 -> `GND` |
| 電位器 | 電位器 -> `MCP3008 CH0` |
| 4 段波段開關 | `GPIO22 / GPIO23 / GPIO24 / GPIO25` -> 各段位 -> `GND` |
| MCP3008 | `GPIO11 -> CLK`，`GPIO10 -> DIN`，`GPIO9 -> DOUT`，`GPIO8 -> CS/SHDN`，再加 `3.3V` + `GND` |
| speaker | 接 Raspberry Pi 音訊輸出 |
| screen | 接 Raspberry Pi 顯示輸出 |

---

## 2. 第一次設定 Raspberry Pi

### 2-1. 開啟終端機

在 Raspberry Pi 桌面上打開 `Terminal`。

### 2-2. 更新系統

```bash
sudo apt update
sudo apt upgrade -y
```

### 2-3. 安裝基本工具

```bash
sudo apt install -y git curl
```

如果還沒有 Node.js，之後也會安裝。

---

## 3. 從 GitHub 下載專案

如果你是第一次使用這個專案，最簡單的方式就是從 GitHub 下載。

> 這份 README 對應的是 `yutingpi` 版本。請下載你 GitHub 上的 `yutingpi` repo，不要下載舊的 DSI 版本。

### 3-1. 先選一個你要放專案的資料夾

常見位置是：

```bash
cd ~/Documents/GitHub
```

如果沒有這個資料夾，可以先建立：

```bash
mkdir -p ~/Documents/GitHub
cd ~/Documents/GitHub
```

### 3-2. 下載專案

```bash
git clone <你的 GitHub Repo URL>
```

如果你是從自己的 GitHub 倉庫下載，請把 `<你的 GitHub Repo URL>` 換成 `yutingpi` 這個 repo 的實際網址。

例如：

```bash
git clone https://github.com/yourname/yutingpi.git
```

### 3-3. 進入專案資料夾

```bash
cd wakeupmap-pi
```

---

## 4. 安裝 Node.js

這個 square 版本是用 Node.js 跑的。

### 4-1. 安裝 Node.js 18+

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 4-2. 確認有安裝成功

```bash
node -v
npm -v
```

如果看到版本號，代表成功。

---

## 5. 安裝專案依賴

進到 `raspberrypi-square` 資料夾：

```bash
cd raspberrypi-square
npm install
```

如果你是第一次用這台 Pi，這一步會下載需要的套件。

### 5-1. 開啟 GPIO 與 SPI

如果你有接按鈕、電位器或 4 段波段開關，建議先打開 Raspberry Pi 的介面設定。

```bash
sudo raspi-config
```

然後進去：

- `Interface Options`
- 開啟 `SPI`

如果你之後要用 `pigpio` 讀 GPIO，也建議把 `pigpiod` 裝好並啟動。

### 5-2. 安裝硬體 bridge 需要的套件

如果你要讓按鈕、波段開關和電位器真的控制畫面，請再安裝這些 Python 套件：

```bash
pip3 install selenium pigpio spidev
```

如果你看到權限問題，請先確認：

- `pigpiod` 有啟動
- `SPI` 有啟用
- 你已經用 `sudo raspi-config` 開過介面設定

---

## 6. 設定 `.env`

在專案根目錄建立 `.env` 檔案。

### 6-1. 建立或編輯 `.env`

如果還沒有 `.env`，可以這樣做：

```bash
cd ..
nano .env
```

### 6-2. 填入內容

```env
PORT=3000
USER_NAME=YuPie
OPENAI_API_KEY=你的_OPENAI_API_金鑰
OPENAI_MODEL=gpt-4o-mini
WEBSITE_URL=http://127.0.0.1:3000
```

### 6-3. 這些欄位代表什麼

- `PORT`：本機網站埠號
- `USER_NAME`：這台 Raspberry Pi 顯示的使用者名稱
- `OPENAI_API_KEY`：後端實際使用的 API key，放在 Raspberry Pi 本機 `.env`
- `OPENAI_MODEL`：要用哪個 OpenAI 模型來生成故事摘要，預設是 `gpt-4o-mini`
- `WEBSITE_URL`：DSI / browser 要打開的網址

### 6-4. API key 要放在哪裡？

這個 `square` 版本的 API 呼叫是由 Raspberry Pi 本機的 `Node.js server` 負責處理，所以：

- API key 要放在 Raspberry Pi 本機的 `.env`
- 不要把 API key 寫進前端 `index.html`
- 不要把 API key 上傳到 GitHub

如果你之後要換成別的金鑰，只要改本機 `.env`，再重新啟動就可以。

---

## 7. 如果你要更換不同 Raspberry Pi 的使用者名稱

最簡單的方法就是改 `.env` 裡的 `USER_NAME`。

例如：

```env
USER_NAME=Alice
```

或：

```env
USER_NAME=Pi-North
```

然後重新啟動應用程式即可。

### 建議

- 一台 Pi 用一個固定名稱
- `square` 和 `DSI` 的 `USER_NAME` 最好一致
- 如果你有多台 Raspberry Pi，可以讓每台的 `.env` 使用不同 `USER_NAME`

---

## 8. 啟動應用程式

### 8-1. 手動啟動

在 `raspberrypi-square` 資料夾中執行：

```bash
npm start
```

預設會在：

```text
http://localhost:3000
```

啟動。

### 8-2. 用瀏覽器打開

你可以直接用 Chromium 打開：

```text
http://localhost:3000
```

如果是實體裝置，建議用全螢幕模式。

### 8-3. 4 段波段開關如何控制歷史紀錄

這個 square 頁面已經提供了對外函式：

- `window.setHistoryOffset(offset)`
- `window.setBandSwitchPosition(position)`

如果你在 Raspberry Pi 上有一個 GPIO 讀取程式，只要讀到波段開關的段位，就呼叫這兩個函式之一即可。

段位對應如下：

- `0` = 最新
- `1` = 往回 1 筆
- `2` = 往回 2 筆
- `3` = 往回 3 筆

### 8-4. 一鍵啟動完整硬體版

如果你希望「雙擊桌面圖示後，整台 Raspberry Pi 都啟動」，請使用這個 launcher：

```bash
cd ~/Documents/GitHub/wakeupmap-pi/raspberrypi-square
chmod +x wakeup-map-launcher.sh
./wakeup-map-launcher.sh
```

這個 launcher 會做三件事：

1. 啟動 `square` 的 Node.js 服務
2. 啟動 `pi_hardware_bridge.py`
3. 讓橋接程式去打開全螢幕 Chromium

所以這才是完整的硬體版本。

### 8-5. 桌面快捷方式

如果你要雙擊桌面圖示就啟動完整硬體版，請到 `raspberrypi-dsi` 執行：

```bash
cd ~/Documents/GitHub/wakeupmap-pi/raspberrypi-dsi
chmod +x create-desktop-shortcut.sh
./create-desktop-shortcut.sh
```

新的桌面快捷方式會直接指向 `raspberrypi-square/wakeup-map-launcher.sh`。

也就是說，雙擊圖示時會：

- 先開 square 服務
- 再開 hardware bridge
- 最後顯示完整裝置畫面

### 8-4. 如果你要讓硬體真的控制畫面

這個資料夾裡已經放好一個 bridge：

- `pi_hardware_bridge.py`

它會負責：

- 讀按鈕
- 讀 4 段波段開關
- 讀電位器
- 把狀態送進 `square` 頁面

你可以這樣啟動：

```bash
cd ~/Documents/GitHub/wakeupmap-pi/raspberrypi-square
python3 pi_hardware_bridge.py
```

如果你第一次要用這個 bridge，先確認：

- `pigpiod` 有啟動
- `SPI` 有開啟
- `spidev` 與 `pigpio` 可以使用

如果出現權限問題，通常是因為 Raspberry Pi 還沒把 `SPI` 或 `GPIO` 功能打開。

---

## 9. 全螢幕顯示

這個 square 介面本來就是設計成全螢幕使用。

如果你是手動打開 Chromium，建議：

- 使用全螢幕
- 隱藏網址列
- 不要顯示分頁列
- 用 kiosk / fullscreen 模式

如果你使用桌面快捷方式，請確認 launcher 腳本會用全螢幕方式開啟。

---

## 10. 聲音行為

這個版本使用瀏覽器 TTS。

所以它會：

- 每次新故事出現時自動朗讀
- `Press the Button` 只負責啟動新的紀錄
- 單純用網頁打開時，也可以聽到聲音

---

## 11. 故事與按鈕的流程

流程是這樣：

1. 按下實體按鈕
2. 畫面進入 `locating`
3. 找到新故事
4. 顯示地圖與文字
5. 瀏覽器 TTS 自動朗讀

所以：

- 按鈕不是播音按鈕
- 按鈕是「開始下一筆故事」的按鈕

---

## 12. 常見問題

### 12-1. 第一次使用 Raspberry Pi，一定要先裝 Git 嗎？

如果你要從 GitHub 下載專案，**是的，建議先安裝 Git**。

如果你的專案已經被你手動複製到 Pi 上，那就不一定需要。

### 12-2. 我只會照著做，不懂指令怎麼辦？

可以，只要照順序執行即可。

### 12-3. 如果沒聲音怎麼辦？

先確認：

- Chromium 沒有靜音
- 有發生過一次按鈕互動
- 系統音量正常

### 12-4. 按鈕沒有反應怎麼辦？

先檢查：

- `GPIO18` 是否接到按鈕
- 按鈕另一端是否接 `GND`
- `pigpiod` 是否有啟動

### 12-5. 電位器沒反應怎麼辦？

先檢查：

- 電位器是否接到 `MCP3008`
- `MCP3008` 是否接到 `SPI0`
- `GPIO8 / 9 / 10 / 11` 是否接對

### 12-6. 4 段波段開關沒反應怎麼辦？

先檢查：

- 第 1 段是否接 `GPIO22`
- 第 2 段是否接 `GPIO23`
- 第 3 段是否接 `GPIO24`
- 第 4 段是否接 `GPIO25`
- 共用端是否接 `GND`
- Raspberry Pi 上是否有讀取 GPIO 的橋接程式

### 12-7. 點桌面圖示後只開網站，沒有接硬體

請確認你開的是新的 launcher：

- `~/Documents/GitHub/wakeupmap-pi/raspberrypi-square/wakeup-map-launcher.sh`

如果你還在用舊的 launcher，只會開網站，不會啟動 bridge。

---

## 13. 如果你要把整台 Pi 設成開機就跑

接下來你可以做這三件事：

1. 建立桌面快捷方式
2. 把 Chromium 設成開機自動開啟
3. 把 `npm start` 包進 launcher

如果你要，我可以下一步直接幫你補一份：

- `setup.sh`
- `wakeup-map-launcher.sh`
- `desktop shortcut` 說明
