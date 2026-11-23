# Raspberry Pi Desktop Launcher Setup

這份說明是給 Raspberry Pi 桌面快捷啟動用的。

目標是：

- 點桌面 icon 就直接啟動 `main_web_dsi.py`
- 每次啟動都固定使用你指定的 `USER_NAME`
- 不需要再在畫面中輸入代號

## 1. 先確認啟動腳本存在

本專案已提供：

- [launch-main-web-dsi.sh](/Users/yutingcheng/Documents/GitHub/wakeupmap-pi/raspberrypi-dsi/launch-main-web-dsi.sh)

這支腳本會：

- 進入正確資料夾
- 讀取 `USER_NAME`
- 自動將 `USER_NAME` 轉成全大寫
- 啟動 `main_web_dsi.py`

## 2. 給啟動腳本執行權限

在 Raspberry Pi 的 terminal 執行：

```bash
chmod +x /home/future/wakeupmap-pi/raspberrypi-dsi/launch-main-web-dsi.sh
```

如果你的使用者不是 `future`，請把路徑改成你自己的 home 目錄。

## 3. 建立桌面 `.desktop` 檔

在 Raspberry Pi terminal 執行：

```bash
nano /home/future/Desktop/WakeupMap.desktop
```

貼上以下內容：

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Wakeup Map
Comment=Launch main_web_dsi.py
Exec=env USER_NAME=YUPIE /home/future/wakeupmap-pi/raspberrypi-dsi/launch-main-web-dsi.sh
Path=/home/future/wakeupmap-pi/raspberrypi-dsi
Icon=/home/future/wakeupmap-pi/icon-512x512.png
Terminal=true
Categories=Utility;
```

## 4. 修改你要的使用者代號

只要改 `Exec=` 這一行裡的 `USER_NAME=YUPIE`。

例如你要改成 `HELLO01`：

```ini
Exec=env USER_NAME=HELLO01 /home/future/wakeupmap-pi/raspberrypi-dsi/launch-main-web-dsi.sh
```

注意：

- 你輸入小寫也沒關係
- 啟動腳本會自動轉成全大寫

## 5. 給桌面捷徑執行權限

在 Raspberry Pi terminal 執行：

```bash
chmod +x /home/future/Desktop/WakeupMap.desktop
```

## 6. 完成後的行為

之後每次你從桌面點開 `Wakeup Map`：

- 都會直接啟動 `main_web_dsi.py`
- 都會自動使用 `.desktop` 裡指定的 `USER_NAME`
- 上傳 Notion 與查詢歷史都會用同一個代號

## 7. 如果你想換 icon

目前推薦直接用：

- `/home/future/wakeupmap-pi/icon-512x512.png`

如果你要改，可以在 `.desktop` 裡改這一行：

```ini
Icon=/home/future/wakeupmap-pi/icon-512x512.png
```

## 8. 如果桌面 icon 沒有立刻更新

可以試：

1. 重新執行 `chmod +x /home/future/Desktop/WakeupMap.desktop`
2. 關閉再重新打開桌面
3. 登出再登入 Raspberry Pi

## 9. 建議的最終設定

如果你之後每次都固定用同一個代號，最穩的方式就是只改 `.desktop`：

```ini
Exec=env USER_NAME=YUPIE /home/future/wakeupmap-pi/raspberrypi-dsi/launch-main-web-dsi.sh
```

這樣不需要再改前端，也不需要額外輸入 UI。
