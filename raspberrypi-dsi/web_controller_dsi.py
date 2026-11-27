#!/usr/bin/env python3
"""
甦醒地圖 - 網頁控制器
透過 Selenium 控制瀏覽器開啟甦醒地圖網站
"""

import os
import time
import logging
from pathlib import Path
from selenium import webdriver

# 自動載入 .env 檔案
def load_env_file():
    """載入 .env 檔案到環境變數"""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# 載入環境變數
load_env_file()
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import subprocess
import platform

logger = logging.getLogger(__name__)

# 配置常數
WEBSITE_URL = os.getenv('WEBSITE_URL', "https://wakeupmap-pi.vercel.app/pi.html")
USER_NAME = os.getenv('USER_NAME', 'YuPie')  # 從環境變數設定，預設為 YuPie
WAIT_TIMEOUT = 30
LOAD_DELAY = 2

def get_chromedriver_path():
    """自動偵測 ChromeDriver 路徑"""
    possible_paths = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver", 
        "/opt/homebrew/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
        "chromedriver"
    ]
    
    for path in possible_paths:
        if os.path.exists(path) or subprocess.run(['which', path], 
                                                capture_output=True).returncode == 0:
            logger.info(f"找到 ChromeDriver: {path}")
            return path
    
    logger.warning("未找到 ChromeDriver，嘗試讓 Selenium 自動處理")
    return None

class WebControllerDSI:
    def __init__(self):
        """
        初始化網頁控制器
        """
        self.driver = None
        self.user_name = USER_NAME
        self.website_url = WEBSITE_URL
        self.wait = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("甦醒地圖網頁控制器初始化")

    def _setup_chrome_options(self):
        """設定 Chrome 瀏覽器選項"""
        options = Options()
        
        # 效能優化選項
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # 記憶體優化
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        
        # 網頁顯示設定 (適合 800x480 螢幕)
        options.add_argument('--window-size=800,480')
        options.add_argument('--window-position=0,0')
        
        # 全螢幕 kiosk 模式，隱藏瀏覽器分頁和工具列
      #  options.add_argument('--kiosk')
      #  options.add_argument('--disable-infobars')
      #  options.add_argument('--hide-scrollbars')
        
        # 用戶資料目錄
        options.add_argument('--user-data-dir=/tmp/chrome-data')
        
        # 自動播放政策
        options.add_argument('--autoplay-policy=no-user-gesture-required')
        
        return options

    def start_browser(self):
        """啟動瀏覽器"""
        try:
            self.logger.info("正在啟動瀏覽器...")
            
            # 設定 Chrome 選項
            options = self._setup_chrome_options()
            
            # 嘗試找到 ChromeDriver
            chromedriver_path = get_chromedriver_path()
            
            if chromedriver_path:
                service = Service(chromedriver_path)
                service.log_path = "/tmp/chromedriver.log"
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                # 讓 Selenium 自動管理 ChromeDriver
                self.driver = webdriver.Chrome(options=options)
            
            # 設定等待物件
            self.wait = WebDriverWait(self.driver, WAIT_TIMEOUT)
            
            self.logger.info("瀏覽器啟動成功")
            return True
            
        except Exception as e:
            self.logger.error(f"瀏覽器啟動失敗：{e}")
            return False

    def load_website(self):
        """載入網站並自動設定"""
        try:
            self.logger.info("正在載入甦醒地圖...")
            
            # 開啟網站
            self.driver.get(self.website_url)
            time.sleep(LOAD_DELAY)
            
            # 自動填入使用者名稱
            self._fill_username()
            
            # 自動點擊載入資料按鈕
            self._click_load_data_button()
            
            self.logger.info("網站載入和設定完成")
            return True
            
        except Exception as e:
            self.logger.error(f"網站載入失敗：{e}")
            return False

    def _fill_username(self):
        """填入使用者名稱（pi.html 版本：使用 JavaScript 設定隱藏輸入框）"""
        try:
            self.logger.info(f"正在設定使用者：{self.user_name}")
            
            # 對於 pi.html，使用者名稱是隱藏輸入框，我們直接用 JavaScript 設定
            # 確保使用者名稱沒有多餘空格
            clean_user_name = self.user_name.strip()
            self.logger.info(f"設定使用者名稱: '{clean_user_name}'")
            
            # 設定到前端的隱藏欄位
            self.driver.execute_script("""
                const userName = arguments[0];
                window.env = window.env || {};
                window.env.USER_NAME = userName;
                const input = document.getElementById('userName');
                if (input) input.value = userName;
            """, clean_user_name)
            
            self.logger.info("使用者名稱設定成功")
            return True
            
        except Exception as e:
            self.logger.error(f"使用者名稱設定失敗：{e}")
            return False

    def _click_load_data_button(self):
        """點擊載入資料按鈕"""
        try:
            self.logger.info("正在載入用戶資料...")
            
            clean_user_name = self.user_name.strip()
            loaded = self.driver.execute_script("""
                const userName = arguments[0];
                window.env = window.env || {};
                window.env.USER_NAME = userName;
                window.rawUserDisplayName = userName;
                localStorage.setItem('wakeupmap_username', userName);
                const loadButton = document.getElementById('setUserNameButton');
                if (!loadButton) return false;
                loadButton.click();
                return true;
            """, clean_user_name)
            if loaded:
                self.logger.info("已點擊載入資料按鈕")
            else:
                self.logger.warning("網頁找不到載入資料按鈕")

            # 等待前端初始化完成
            time.sleep(3)
            
            # 強制設置用戶資料和啟用按鈕
            force_setup_js = """
            const userName = arguments[0];
            // 強制設置用戶資料
            window.rawUserDisplayName = userName;
            localStorage.setItem('wakeupmap_username', userName);
            
            // 強制啟用開始按鈕
            const findCityButton = document.getElementById('findCityButton');
            if (findCityButton) {
                findCityButton.disabled = false;
                console.log('🔧 強制啟用開始按鈕');
            }
            
            // 更新用戶顯示
            const currentUserIdSpan = document.getElementById('currentUserId');
            const currentUserDisplayNameSpan = document.getElementById('currentUserDisplayName');
            if (currentUserIdSpan) currentUserIdSpan.textContent = userName;
            if (currentUserDisplayNameSpan) currentUserDisplayNameSpan.textContent = userName;
            
            console.log('🔧 用戶資料強制設置完成');
            """
            
            self.driver.execute_script(force_setup_js, clean_user_name)
            self.logger.info("✅ 用戶資料強制設置完成")
            
            # 等待前端初始化完成
            time.sleep(2)
            
            # 觸發強制故事顯示
            story_trigger_js = """
            if (window.forceDisplayStoryFromNotion) {
                console.log('🔧 樹莓派觸發強制故事顯示');
                window.forceDisplayStoryFromNotion();
            } else if (window.forceDisplayStoryFromFirebase) {
                console.log('🔧 樹莓派觸發舊版強制故事顯示');
                window.forceDisplayStoryFromFirebase();
            } else {
                console.log('⚠️ forceDisplayStoryFromNotion 函數未找到');
            }
            """
            
            self.driver.execute_script(story_trigger_js)
            self.logger.info("✅ 已觸發強制故事顯示")
            
            return True
            
        except Exception as e:
            self.logger.error(f"載入用戶資料失敗：{e}")
            return False

    def click_start_button(self):
        """啟動甦醒流程，等待這次請求的城市資料。"""
        try:
            attempt = self.driver.execute_script("""
                if (document.querySelector('#loadingState.active')) {
                    return {started: false, error: '甦醒流程仍在處理中'};
                }
                if (typeof window.startTheDay !== 'function') {
                    return {started: false, error: '網頁尚未提供 startTheDay'};
                }

                window.debugStartTheDay = 'NOT_STARTED';
                window.currentCityData = null;
                const pending = window.startTheDay();
                if (pending && typeof pending.catch === 'function') {
                    pending.catch(error => {
                        window.debugStartTheDay = 'ERROR: ' + error.message;
                    });
                }

                const status = window.debugStartTheDay;
                if (status !== 'STARTED' && status !== 'INITIALIZED') {
                    return {started: false, error: '網頁未進入定位流程 (' + status + ')'};
                }
                return {started: true};
            """)
            if not attempt['started']:
                self.logger.warning("無法啟動甦醒流程：%s", attempt['error'])
                return {'success': False, 'error': attempt['error']}

            def read_city_or_error(driver):
                return driver.execute_script("""
                    const status = window.debugStartTheDay;
                    if (typeof status === 'string' && status.startsWith('ERROR')) {
                        return {error: status};
                    }
                    const errorState = document.querySelector('#errorState.active');
                    if (errorState) {
                        return {error: errorState.querySelector('#errorMessage')?.textContent
                            || '網頁定位失敗'};
                    }

                    const data = window.currentCityData;
                    const city = data?.name || data?.city;
                    const isCoordinate = value => (
                        (typeof value === 'number' || (typeof value === 'string' && value.trim()))
                        && Number.isFinite(Number(value))
                    );
                    if (typeof city !== 'string' || !city.trim()
                            || !isCoordinate(data?.latitude) || !isCoordinate(data?.longitude)) {
                        return null;
                    }
                    return {city: city.trim()};
                """)

            # The browser publishes city data before it waits for the Pi to generate audio.
            outcome = WebDriverWait(self.driver, 90).until(read_city_or_error)
            if 'error' in outcome:
                self.logger.warning("網頁定位失敗：%s", outcome['error'])
                return {'success': False, 'error': outcome['error']}

            self.logger.info("甦醒城市：%s", outcome['city'])
            return {'success': True, 'message': '甦醒成功', 'result': f"甦醒城市: {outcome['city']}"}
        except TimeoutException:
            self.logger.warning("等待本次甦醒城市資料逾時")
            return {'success': False, 'error': '等待本次甦醒城市資料逾時'}
        except Exception as error:
            self.logger.exception("點擊開始按鈕失敗")
            return {'success': False, 'error': str(error)}

    def reload_website(self):
        """重新載入網站"""
        try:
            self.logger.info("正在重新載入網站...")
            
            # 重新載入頁面
            self.driver.refresh()
            time.sleep(LOAD_DELAY)
            
            # 重新設定使用者資料
            if self._fill_username() and self._click_load_data_button():
                self.logger.info("網站重新載入成功")
                return {'success': True, 'message': '網站重新載入成功'}
            else:
                return {'success': False, 'error': '重新設定失敗'}
                
        except Exception as e:
            self.logger.error(f"重新載入網站失敗：{e}")
            return {'success': False, 'error': str(e)}

    def stop(self):
        """停止並清理瀏覽器"""
        try:
            if self.driver:
                self.logger.info("正在關閉瀏覽器...")
                self.driver.quit()
                self.driver = None
                
        except Exception as e:
            self.logger.error(f"關閉瀏覽器時發生錯誤：{e}")

    def get_page_title(self):
        """取得頁面標題"""
        try:
            if self.driver:
                return self.driver.title
            return None
        except Exception as e:
            self.logger.error(f"取得頁面標題失敗：{e}")
            return None

    def is_browser_running(self):
        """檢查瀏覽器是否正在運行"""
        try:
            if self.driver:
                # 嘗試取得當前URL來測試連接
                _ = self.driver.current_url
                return True
            return False
        except Exception:
            return False

    def _extract_city_data(self):
        """從網頁提取城市資料"""
        try:
            # 等待城市名稱元素出現
            city_name = self.wait_for_element_text('.city-name', timeout=2)
            country_name = self.wait_for_element_text('.country-name', timeout=2)
            
            # 清理城市名稱（移除冒號和空格）
            city_name = city_name.strip().rstrip(':').strip() if city_name else ''
            country_name = country_name.strip() if country_name else ''
            
            # 從國家名稱獲取國家代碼
            country_code = self._get_country_code(country_name)
            
            # 獲取經緯度
            coordinates = self.wait_for_element_text('#coordinates', timeout=2)
            lat, lon = None, None
            if coordinates:
                try:
                    lat_str, lon_str = coordinates.split(',')
                    lat = float(lat_str.strip())
                    lon = float(lon_str.strip())
                except:
                    self.logger.warning(f'無法解析座標: {coordinates}')
            
            # 獲取時區
            timezone = self.wait_for_element_attribute('.timezone-info', 'data-timezone', timeout=2) or ''
            
            city_data = {
                'city': city_name,
                'country': country_name,
                'countryCode': country_code,
                'latitude': lat,
                'longitude': lon,
                'timezone': timezone
            }
            
            self.logger.info(f'甦醒城市：{city_name}')
            return city_data
            
        except Exception as e:
            self.logger.error(f'提取城市資料失敗: {e}')
            return None
            
    def _get_country_code(self, country_name):
        """根據國家名稱獲取國家代碼"""
        country_map = {
            'United States': 'US',
            'Chile': 'CL',
            'Peru': 'PE',
            'Brazil': 'BR',
            'Argentina': 'AR',
            'Mexico': 'MX',
            'Canada': 'CA',
            'China': 'CN',
            'Japan': 'JP',
            'South Korea': 'KR',
            'Taiwan': 'TW',
            'Hong Kong': 'HK',
            'Singapore': 'SG',
            'Malaysia': 'MY',
            'Thailand': 'TH',
            'Vietnam': 'VN',
            'Indonesia': 'ID',
            'Philippines': 'PH',
            'India': 'IN',
            'Australia': 'AU',
            'New Zealand': 'NZ',
            'United Kingdom': 'GB',
            'France': 'FR',
            'Germany': 'DE',
            'Italy': 'IT',
            'Spain': 'ES',
            'Portugal': 'PT',
            'Netherlands': 'NL',
            'Belgium': 'BE',
            'Switzerland': 'CH',
            'Austria': 'AT',
            'Sweden': 'SE',
            'Norway': 'NO',
            'Denmark': 'DK',
            'Finland': 'FI',
            'Russia': 'RU',
            'Poland': 'PL',
            'Czech Republic': 'CZ',
            'Hungary': 'HU',
            'Greece': 'GR',
            'Turkey': 'TR',
            'Israel': 'IL',
            'South Africa': 'ZA',
            'Egypt': 'EG',
            'Morocco': 'MA',
            'United Arab Emirates': 'AE',
            'Saudi Arabia': 'SA'
        }
        return country_map.get(country_name, '')

    def get_day_count(self):
        """獲取當前 Day 計數"""
        try:
            day_count = self.local_storage.get_current_day_number()
            self.logger.info(f"🔢 返回當前 Day 計數: {day_count}")
            return {'day': day_count}
        except Exception as e:
            self.logger.error(f"獲取 Day 計數失敗: {e}")
            return {'day': 1}

# 測試程式
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("甦醒地圖網頁控制器測試")
    
    controller = WebControllerDSI()
    
    try:
        # 啟動瀏覽器
        if controller.start_browser():
            print("瀏覽器啟動成功")
            
            # 載入網站
            if controller.load_website():
                print("網站載入成功")
                
                # 等待用戶輸入來測試按鈕功能
                input("按 Enter 鍵測試開始按鈕...")
                result = controller.click_start_button()
                print(f"開始按鈕結果：{result}")
                
            time.sleep(5)  # 等待觀察
        else:
            print("瀏覽器啟動失敗")
    
    except KeyboardInterrupt:
        print("測試中斷")
    
    finally:
        controller.stop()
        print("測試完成") 
