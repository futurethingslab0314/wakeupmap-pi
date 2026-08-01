#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WakeUpMap - 音頻管理模組
處理 TTS 語音生成、音頻播放和音量控制
"""

import os
import time
import threading
import logging
import hashlib
import subprocess
import struct
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

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

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import (
    AUDIO_CONFIG, 
    TTS_CONFIG, 
    SPEAKER_CONFIG,
    MORNING_GREETINGS,
    TTS_LANGUAGE_MAP,
    AUDIO_FILES
)

class AudioManager:
    """音頻管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tts_engine = None
        self.audio_initialized = False
        self.current_volume = AUDIO_CONFIG['volume']
        self.cache_dir = Path(TTS_CONFIG['cache_dir'])
        
        # 確保快取目錄存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化音頻系統
        self._initialize_audio()
        
        # 初始化 TTS 引擎
        self._initialize_tts()
        
        # 清理過期快取
        self._cleanup_cache()
    
    def _initialize_audio(self):
        """初始化音頻系統"""
        try:
            if not AUDIO_CONFIG['enabled']:
                self.logger.info("音頻功能已禁用")
                return
            
            # 嘗試初始化 pygame mixer
            if PYGAME_AVAILABLE:
                try:
                    pygame.mixer.pre_init(
                        frequency=AUDIO_CONFIG['sample_rate'],
                        size=-16,
                        channels=AUDIO_CONFIG['channels'],
                        buffer=512
                    )
                    pygame.mixer.init()
                    self.audio_initialized = True
                    self.logger.info("Pygame 音頻系統初始化成功")
                except Exception as e:
                    self.logger.warning(f"Pygame 初始化失敗: {e}")
            
            # 如果 pygame 不可用，使用 ALSA
            if not self.audio_initialized:
                self._check_alsa_audio()
            
            # 設置音量
            self.set_volume(self.current_volume)
            
        except Exception as e:
            self.logger.error(f"音頻系統初始化失敗: {e}")
    
    def _check_alsa_audio(self):
        """檢查 ALSA 音頻系統"""
        try:
            # 檢查 ALSA 設備
            result = subprocess.run(['aplay', '-l'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                self.audio_initialized = True
                self.logger.info("ALSA 音頻系統可用")
            else:
                self.logger.warning("ALSA 音頻設備檢查失敗")
        except Exception as e:
            self.logger.warning(f"ALSA 檢查失敗: {e}")
    
    def _initialize_tts(self):
        """初始化 TTS 引擎 - 僅支援 OpenAI TTS"""
        try:
            # 強制使用 OpenAI TTS
            self.openai_client = None
            
            # 檢查 OpenAI 是否可用
            if not OPENAI_AVAILABLE:
                self.logger.error("❌ OpenAI 庫未安裝，請安裝: pip install openai")
                raise Exception("OpenAI 庫未安裝")
            
            if not TTS_CONFIG['openai_api_key']:
                self.logger.error("❌ OpenAI API 金鑰未設定，請在 .env 檔案中設定 OPENAI_API_KEY")
                raise Exception("OpenAI API 金鑰未設定")
            
            # 初始化 OpenAI 客戶端
            try:
                self.openai_client = openai.OpenAI(
                    api_key=TTS_CONFIG['openai_api_key']
                )
                self.logger.info("✨ OpenAI TTS 引擎初始化成功！")
                self.logger.info(f"🎤 使用語音: {TTS_CONFIG['openai_voice']}")
                self.logger.info(f"🎵 使用模型: {TTS_CONFIG['openai_model']}")
            except Exception as e:
                self.logger.error(f"❌ OpenAI TTS 初始化失敗: {e}")
                raise Exception(f"OpenAI TTS 初始化失敗: {e}")
                
        except Exception as e:
            self.logger.error(f"❌ TTS 引擎初始化失敗: {e}")
            raise Exception(f"TTS 引擎初始化失敗: {e}")
    
    # 已移除備用語音引擎相關函數
    # 現在只支援 OpenAI TTS
    
    def play_greeting(self, country_code: str, city_name: str = "", country_name: str = "") -> bool:
        """
        播放早安問候語和城市故事（使用 Nova 整合模式）
        
        Args:
            country_code: 國家代碼
            city_name: 城市名稱
            country_name: 國家名稱
        
        Returns:
            bool: 播放是否成功
        """
        try:
            if not AUDIO_CONFIG['enabled']:
                self.logger.info("音頻功能已禁用，跳過音頻播放")
                return True
            
            self.logger.info("🎧 開始準備完整問候語和故事...")
            
            # 📡 獲取完整問候語和故事
            greeting_data = self._fetch_greeting_and_story_from_api(city_name, country_name, country_code)
            
            if greeting_data:
                greeting_text = greeting_data['greeting']
                language_code = greeting_data['languageCode']
                story_text = greeting_data.get('chineseStory', '')
                
                # 🔍 調試資訊
                self.logger.info(f"🔍 調試 - 問候語資料: {greeting_data}")
                self.logger.info(f"🔍 調試 - story_text: '{story_text}'")
                self.logger.info(f"🔍 調試 - TTS引擎: {TTS_CONFIG['engine']}")
                self.logger.info(f"🔍 調試 - nova_integrated_mode: {TTS_CONFIG.get('nova_integrated_mode', True)}")
                
                # 🌟 Nova 整合模式：先播放當地語言問候語，再播放中文故事
                self.logger.info(f"🌟 Nova 整合模式：先播放當地語言問候語，再播放中文故事")
                self.logger.info(f"當地問候語: {greeting_text} ({language_code})")
                self.logger.info(f"中文故事: {story_text}")
                
                # 創建完整的音頻內容：問候語 + 故事
                full_content = f"{greeting_text}。{story_text}"
                self.logger.info(f"完整音頻內容: {full_content}")
                
                return self._play_integrated_nova_content(full_content, language_code)
            else:
                # 備用方案：使用內建問候語
                self.logger.warning("ChatGPT API 失敗，使用備用問候語")
                greeting_text = self._get_greeting_text(country_code, city_name)
                language_code = self._get_language_code(country_code)
                return self._play_text_with_language(greeting_text, language_code)
                
        except Exception as e:
            self.logger.error(f"播放問候語失敗: {e}")
            return False
    
    def prepare_greeting_audio(self, country_code: str, city_name: str = "", country_name: str = "") -> Optional[Path]:
        """
        準備完整問候語音頻但不播放（同步loading模式專用）
        
        Args:
            country_code: 國家代碼
            city_name: 城市名稱
            country_name: 國家名稱
        
        Returns:
            Path: 準備好的音頻文件路徑，失敗時返回 None
        """
        try:
            if not AUDIO_CONFIG['enabled']:
                self.logger.info("音頻功能已禁用，跳過音頻準備")
                return None
            
            self.logger.info("🎧 準備完整問候語音頻（同步模式）...")
            
            # 📡 獲取完整問候語和故事（與播放模式相同的 API）
            greeting_data = self._fetch_greeting_and_story_from_api(city_name, country_name, country_code)

            if greeting_data:
                greeting_text = greeting_data['greeting']
                language_code = greeting_data['languageCode']
                story_text = greeting_data.get('chineseStory', '')
                
                # 🔍 調試資訊
                self.logger.info(f"🔍 準備音頻 - 問候語資料: {greeting_data}")
                self.logger.info(f"🔍 準備音頻 - story_text: '{story_text}'")
                
                # 🌟 Nova 整合模式：只生成中文故事
                if (story_text and 
                    TTS_CONFIG['engine'] == 'openai' and 
                    TTS_CONFIG.get('nova_integrated_mode', True)):
                    
                    self.logger.info(f"🌟 準備 Nova 音頻：只播放中文故事")
                    self.logger.info(f"中文故事: {story_text}")
                    
                    # 只使用中文故事，不包含問候語
                    return self._generate_integrated_audio(story_text)
                    
                else:
                    # 🔄 分離模式：只準備中文故事（如果有）
                    if story_text:
                        self.logger.info(f"🔄 準備分離音頻：中文故事")
                        self.logger.info(f"中文故事: {story_text}")
                        
                        if TTS_CONFIG['engine'] == 'openai':
                            return self._generate_audio_openai_direct(story_text, 'zh')
                        else:
                            return self._generate_audio(story_text, 'zh')
                    else:
                        self.logger.info("沒有故事內容，跳過音頻準備")
                        return None
            else:
                # API 失敗，沒有故事內容
                self.logger.warning("ChatGPT API 失敗，沒有故事內容可播放")
                return None
                
        except Exception as e:
            self.logger.error(f"準備問候語音頻失敗: {e}")
            return None
    
    def prepare_greeting_audio_with_content(self, country_code: str, city_name: str = "", country_name: str = "", city_data: dict = None) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        """
        準備完整問候語音頻並返回故事內容（用於網頁顯示）
        
        Args:
            country_code: 國家代碼
            city_name: 城市名稱
            country_name: 國家名稱
            city_data: 完整城市數據，包含坐標信息
        
        Returns:
            Tuple[Path, Dict]: (音頻文件路徑, 故事內容字典)
        """
        try:
            if not AUDIO_CONFIG['enabled']:
                self.logger.info("音頻功能已禁用，返回空結果")
                return None, None
            
            self.logger.info("🎧 準備完整問候語音頻（同步模式）...")
            
            # 📡 獲取完整問候語和故事
            greeting_data = self._fetch_greeting_and_story_from_api(city_name, country_name, country_code)
            
            if greeting_data:
                greeting_text = greeting_data['greeting']
                language_code = greeting_data['languageCode']
                story_text = greeting_data.get('chineseStory', '')
                
                self.logger.info(f"🔍 準備音頻 - 問候語資料: {greeting_data}")
                self.logger.info(f"🔍 準備音頻 - story_text: '{story_text}'")
                
                # 創建完整的音頻內容：問候語 + 故事
                full_content = f"{greeting_text}。{story_text}"
                self.logger.info(f"完整音頻內容: {full_content}")
                
                # 🌟 準備 Nova 音頻
                self.logger.info("🌟 準備 Nova 音頻：整合模式")
                
                # 生成音頻文件
                audio_file = self._generate_audio_openai_direct(full_content, language_code, voice='nova')
                
                if audio_file and audio_file.exists():
                    self.logger.info(f"✨ Nova 整合音頻生成成功: {audio_file.name}")
                    
                    # 準備返回的故事內容，包含城市和國家資訊
                    story_content = {
                        'greeting': greeting_text,
                        'language': greeting_data.get('language', ''),
                        'languageCode': language_code,
                        'story': greeting_data.get('story', ''),
                        'story_zh': story_text,
                        'fullContent': full_content,
                        'city': greeting_data.get('city', city_name),
                        'city_zh': greeting_data.get('city_zh', city_data.get('city_zh', city_name) if city_data else city_name),
                        'country': greeting_data.get('country', country_name),
                        'country_zh': greeting_data.get('country_zh', city_data.get('country_zh', country_name) if city_data else country_name),
                        'countryCode': country_code,
                        'latitude': city_data.get('latitude', 0) if city_data else 0,
                        'longitude': city_data.get('longitude', 0) if city_data else 0
                    }
                    
                    # 🔧 立即上傳故事到Firebase，確保數據持久化
                    self.logger.info("🔥 故事生成成功，立即上傳到Firebase...")
                    upload_success = self._upload_story_to_firebase(story_content, city_data)
                    if upload_success:
                        self.logger.info("✅ 故事已成功上傳到Firebase")
                    else:
                        self.logger.warning("⚠️ 故事上傳到Firebase失敗")
                    
                    return audio_file, story_content
                else:
                    self.logger.error("Nova 整合音頻生成失敗")
                    return None, None
            else:
                self.logger.warning("ChatGPT API 失敗，無法準備音頻")
                return None, None
                
        except Exception as e:
            self.logger.error(f"準備完整音頻失敗: {e}")
            return None, None
    
    # 快速模式已移除 - 只使用完整 Nova 語音播放
    
    def _generate_integrated_audio(self, content: str) -> Optional[Path]:
        """
        生成整合音頻但不播放
        
        Args:
            content: 整合的文本內容
        
        Returns:
            Path: 生成的音頻文件路徑
        """
        try:
            self.logger.info("🤖 Nova 整合音頻生成中...")
            
            # 使用 OpenAI TTS 生成音頻（Nova 會自動處理多語言）
            audio_file = self._generate_audio(content, 'auto')  # 使用 auto 讓 Nova 自動檢測語言
            
            if audio_file and audio_file.exists():
                self.logger.info(f"✨ Nova 整合音頻生成成功: {audio_file.name}")
                return audio_file
            else:
                self.logger.error("Nova 整合音頻生成失敗")
                return None
                
        except Exception as e:
            self.logger.error(f"Nova 整合音頻生成失敗: {e}")
            return None
    
    def play_audio_file_direct(self, audio_file: Path) -> bool:
        """
        直接播放音頻文件（同步模式專用）
        
        Args:
            audio_file: 音頻文件路徑
        
        Returns:
            bool: 播放是否成功
        """
        try:
            if not audio_file or not audio_file.exists():
                self.logger.error("音頻文件不存在")
                return False
            
            self.logger.info(f"🎵 直接播放音頻: {audio_file.name}")
            
            # 使用現有的播放方法
            success = self._play_audio_file(audio_file)
            
            if success:
                self.logger.info("✅ 直接音頻播放成功")
                return True
            else:
                self.logger.error("❌ 直接音頻播放失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"直接播放音頻失敗: {e}")
            return False

    def _play_integrated_nova_content(self, content: str, language_code: str) -> bool:
        """
        使用 Nova 播放故事內容
        
        Args:
            content: 故事文本內容
            language_code: 語言代碼
        
        Returns:
            bool: 播放是否成功
        """
        try:
            self.logger.info("🤖 Nova 整合音頻生成中...")
            self.logger.info(f"🤖 使用 OpenAI TTS 生成 {language_code} 語音")
            self.logger.info(f"🤖 使用 OpenAI TTS 生成音頻: nova")
            
            # 使用 OpenAI TTS 生成音頻，使用指定的語言代碼
            audio_file = self._generate_audio_openai_direct(content, language_code, voice='nova')
            
            if audio_file and audio_file.exists():
                self.logger.info(f"✨ OpenAI TTS 音頻生成成功: {audio_file}")
                self.logger.info(f"音頻文件生成成功: {audio_file}")
                self.logger.info(f"✨ Nova 整合音頻生成成功: {audio_file.name}")
                
                # 播放音頻
                success = self._play_audio_file(audio_file)
                
                if success:
                    self.logger.info("✨ Nova 故事朗讀完成")
                    return True
                else:
                    self.logger.error("Nova 音頻播放失敗")
                    return False
            else:
                self.logger.error("Nova 整合音頻生成失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"Nova 整合播放失敗: {e}")
            return False
    
    def _play_text_with_nova(self, text: str, language_code: str) -> bool:
        """
        強制使用 OpenAI TTS Nova 播放文字
        
        Args:
            text: 要播放的文字
            language_code: 語言代碼
        
        Returns:
            bool: 播放是否成功
        """
        try:
            self.logger.info(f"🤖 Nova 強制播放 {language_code} 語音: {text}")
            
            # 強制使用 OpenAI TTS 生成音頻
            audio_file = self._generate_audio_openai_direct(text, language_code)
            
            if audio_file and audio_file.exists():
                # 播放音頻
                success = self._play_audio_file(audio_file)
                
                if success:
                    self.logger.info(f"✨ Nova 播放成功: {language_code}")
                    return True
                else:
                    self.logger.error(f"Nova 音頻播放失敗: {language_code}")
                    return False
            else:
                self.logger.error(f"Nova 音頻生成失敗: {language_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Nova 播放失敗: {e}")
            return False
    
    def _play_text_with_language(self, text: str, language_code: str) -> bool:
        """
        播放指定語言的文字
        
        Args:
            text: 要播放的文字
            language_code: 語言代碼
        
        Returns:
            bool: 播放是否成功
        """
        try:
            # 檢查快取
            audio_file = self._get_cached_audio(text, language_code)
            
            if not audio_file:
                # 生成新的音頻文件
                audio_file = self._generate_audio(text, language_code)
            
            if audio_file and audio_file.exists():
                # 播放音頻
                return self._play_audio_file(audio_file)
            else:
                self.logger.error(f"無法生成或找到音頻文件: {text}")
                return False
                
        except Exception as e:
            self.logger.error(f"播放文字失敗: {e}")
            return False

    def _fetch_greeting_and_story_from_api(self, city: str, country: str, country_code: str) -> Optional[Dict[str, Any]]:
        """
        從 ChatGPT API 獲取當地語言問候語與中英文故事
        
        Args:
            city: 城市名稱
            country: 國家名稱
            country_code: 國家代碼
        
        Returns:
            Dict: 問候語和故事資料，包含 greeting, language, languageCode, story, story_zh 等
        """
        try:
            import requests
            import json
            
            # API 端點 - 使用正確的 Pi 故事生成 API
            api_url = 'https://wakeupmap-pi.vercel.app/api/generatePiStory'
            
            # 清理城市名稱（移除冒號和空格）
            city = city.strip().rstrip(':').strip() if city else ''
            country = country.strip() if country else ''
            
            # 如果沒有提供國家代碼，嘗試從國家名稱獲取
            if not country_code:
                country_code = self._get_country_code(country)
            
            # 請求資料
            request_data = {
                "city": city,
                "country": country,
                "countryCode": country_code
            }
            
            self.logger.info(f"調用故事生成 API: {api_url}")
            self.logger.info(f"請求資料: {request_data}")
            
            # 發送請求
            response = requests.post(
                api_url,
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                greeting_data = {
                    'greeting': result['greeting'],
                    'language': result['language'],
                    'languageCode': result['languageCode'],
                    'story': result.get('story', ''),
                    'story_zh': result.get('story_zh', result.get('chineseStory', '')),
                    'chineseStory': result.get('story_zh', result.get('chineseStory', '')),
                    'city': result.get('city', city),
                    'country': result.get('country', country),
                    'city_zh': result.get('city_zh', city),
                    'country_zh': result.get('country_zh', country)
                }
                self.logger.info(f"API 返回故事: {greeting_data['chineseStory']}")
                return greeting_data
            else:
                self.logger.error(f"API 請求失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"調用故事生成 API 時發生錯誤: {e}")
            return None
    
    def _upload_story_to_firebase(self, story_content: Dict[str, Any], city_data: Optional[Dict[str, Any]]) -> bool:
        """
        將故事內容上傳到Firebase
        
        Args:
            story_content: 包含故事、問候語、城市等信息的字典
            
        Returns:
            bool: 上傳是否成功
        """
        try:
            import requests
            import json
            
            # 從環境變數獲取使用者名稱
            user_name = os.getenv('USER_NAME', 'unknown')
            
            # 構建上傳到Firebase的數據
            api_data = {
                'userDisplayName': user_name,  # 從 .env 的 USER_NAME 讀取
                'dataIdentifier': user_name,
                'groupName': 'Pi',  # Pi群組
                'city': story_content.get('city', 'Unknown City'),
                'country': story_content.get('country', 'Unknown Country'),
                'city_zh': story_content.get('city_zh', story_content.get('city', 'Unknown City')),
                'country_zh': story_content.get('country_zh', story_content.get('country', 'Unknown Country')),
                'story': story_content.get('story', ''),
                'story_zh': story_content.get('story_zh', story_content.get('story', '')),
                'greeting': story_content.get('greeting', ''),
                'language': story_content.get('language', ''),
                'languageCode': story_content.get('languageCode', ''),
                'latitude': city_data.get('latitude', 0) if city_data else 0,  # 將由前端補充正確的坐標
                'longitude': city_data.get('longitude', 0) if city_data else 0,
                'longtitude': city_data.get('longitude', 0) if city_data else 0
            }
            
            self.logger.info(f"🔥 [Firebase上傳] 準備上傳數據: {api_data}")
            
            # 調用save-record API
            api_url = 'https://wakeupmap-pi.vercel.app/api/save-record'
            response = requests.post(
                api_url,
                json=api_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"✅ [Firebase上傳] 成功上傳到Firebase: {result}")
                return True
            else:
                self.logger.error(f"❌ [Firebase上傳] 上傳失敗: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ [Firebase上傳] 上傳時發生錯誤: {e}")
            return False
            
    def _get_country_code(self, country_name: str) -> str:
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
    
    def _get_greeting_text(self, country_code: str, city_name: str = "") -> str:
        """獲取問候語文本"""
        # 根據國家代碼確定語言
        language_map = {
            'TW': 'zh-TW', 'CN': 'zh-CN', 'HK': 'zh-TW', 'MO': 'zh-TW',
            'JP': 'ja', 'KR': 'ko', 'US': 'en', 'GB': 'en', 'AU': 'en',
            'ES': 'es', 'FR': 'fr', 'DE': 'de', 'IT': 'it', 'PT': 'pt',
            'RU': 'ru', 'TH': 'th', 'VN': 'vi', 'IN': 'hi'
        }
        
        language = language_map.get(country_code.upper(), 'default')
        greeting = MORNING_GREETINGS.get(language, MORNING_GREETINGS['default'])
        
        # 如果有城市名稱，可以添加到問候語中
        if city_name:
            if language.startswith('zh'):
                greeting = f"來自{city_name}的{greeting}"
            elif language == 'en':
                greeting = f"Good morning from {city_name}! {greeting}"
            elif language == 'ja':
                greeting = f"{city_name}から{greeting}"
        
        return greeting
    
    def _get_language_code(self, country_code: str) -> str:
        """獲取 TTS 語言代碼"""
        language_map = {
            'TW': 'zh-TW', 'CN': 'zh-CN', 'HK': 'zh-TW', 'MO': 'zh-TW',
            'JP': 'ja', 'KR': 'ko', 'US': 'en', 'GB': 'en', 'AU': 'en',
            'ES': 'es', 'FR': 'fr', 'DE': 'de', 'IT': 'it', 'PT': 'pt',
            'RU': 'ru', 'TH': 'th', 'VN': 'vi', 'IN': 'hi',
            'ZA': 'af',  # 南非 -> 南非語
            'KE': 'sw',  # 肯雅 -> 斯瓦希里語
            'NG': 'en',  # 奈及利亞 -> 英語
            'MA': 'ar',  # 摩洛哥 -> 阿拉伯語
            'ET': 'en',  # 衣索比亞 -> 英語（備用）
            'GH': 'en',  # 迦納 -> 英語
            'TF': 'fr',  # 法國南方領土 -> 法語
        }
        
        language = language_map.get(country_code.upper(), 'default')
        return TTS_LANGUAGE_MAP.get(language, TTS_LANGUAGE_MAP['default'])
    
    def _get_cached_audio(self, text: str, language: str) -> Optional[Path]:
        """檢查快取中是否有對應的音頻文件"""
        if not TTS_CONFIG['cache_enabled']:
            return None
        
        # 生成文本的哈希值作為文件名
        text_hash = hashlib.md5(f"{text}_{language}".encode()).hexdigest()
        audio_file = self.cache_dir / f"greeting_{language}_{text_hash}.wav"
        
        if audio_file.exists():
            # 檢查文件是否過期
            file_age = time.time() - audio_file.stat().st_mtime
            if file_age < AUDIO_FILES['cache_timeout']:
                self.logger.debug(f"使用快取音頻文件: {audio_file}")
                return audio_file
            else:
                # 刪除過期文件
                audio_file.unlink()
        
        return None
    
    def _generate_audio(self, text: str, language: str) -> Optional[Path]:
        """生成音頻文件，提供多重備用方案"""
        try:
            text_hash = hashlib.md5(f"{text}_{language}".encode()).hexdigest()
            audio_file = self.cache_dir / f"greeting_{language}_{text_hash}.wav"
            
            # 主要引擎嘗試
            result_file = None
            
            # OpenAI TTS 優先（最高品質，支援所有語言）
            if TTS_CONFIG['engine'] == 'openai' and self.openai_client:
                self.logger.info(f"🤖 使用 OpenAI TTS 生成 {language} 語音")
                result_file = self._generate_audio_openai(text, audio_file)
                
                # OpenAI 失敗時，根據語言選擇備用
                if result_file is None:
                    self.logger.warning("OpenAI TTS 失敗，使用備用引擎")
                    if language in ['zh', 'zh-CN', 'zh-TW', 'ru']:
                        result_file = self._generate_audio_espeak(text, language, audio_file)
                    else:
                        # 嘗試 Festival
                        result_file = self._generate_audio_festival(text, audio_file)
                        if result_file is None:
                            result_file = self._generate_audio_espeak(text, language, audio_file)
            
            # 如果不是 OpenAI 引擎，中文、俄語等特定語言使用 espeak
            elif language in ['zh', 'zh-CN', 'zh-TW', 'ru']:
                self.logger.info(f"語言 {language} 使用 espeak 引擎（非 OpenAI 模式）")
                result_file = self._generate_audio_espeak(text, language, audio_file)
            elif TTS_CONFIG['engine'] == 'festival':
                # 使用 Festival（更自然的聲音）
                result_file = self._generate_audio_festival(text, audio_file)
                
                # Festival 失敗時，自動回退到 espeak
                if result_file is None:
                    self.logger.warning("Festival 失敗，回退到 espeak")
                    result_file = self._generate_audio_espeak(text, language, audio_file)
                    
            elif TTS_CONFIG['engine'] == 'pyttsx3' and self.tts_engine:
                # 使用 pyttsx3
                try:
                    self.tts_engine.save_to_file(text, str(audio_file))
                    self.tts_engine.runAndWait()
                    
                    if audio_file.exists() and self._validate_wav_file(audio_file):
                        result_file = audio_file
                    else:
                        self.logger.warning("pyttsx3 失敗，回退到 espeak")
                        result_file = self._generate_audio_espeak(text, language, audio_file)
                except Exception as e:
                    self.logger.warning(f"pyttsx3 失敗: {e}，回退到 espeak")
                    result_file = self._generate_audio_espeak(text, language, audio_file)
                    
            else:
                # 使用 espeak（備用方案，優化參數）
                result_file = self._generate_audio_espeak(text, language, audio_file)
            
            # 最終驗證和備用
            if result_file and result_file.exists():
                # 根據文件格式進行驗證
                if result_file.suffix.lower() == '.wav':
                    is_valid = self._validate_wav_file(result_file)
                else:
                    # MP3 或其他格式，檢查文件大小
                    is_valid = result_file.stat().st_size > 1000  # 至少 1KB
                
                # 測試播放能力
                can_play = self._test_audio_playback(result_file)
                
                if is_valid and can_play:
                    self.logger.info(f"音頻文件生成成功: {result_file}")
                    return result_file
                else:
                    self.logger.warning(f"音頻文件驗證失敗 - 格式: {is_valid}, 播放: {can_play}")
            
            # 如果主要方法失敗，嘗試備用方案
            if result_file is None or not result_file.exists():
                # 最終備用：如果所有方法都失敗，嘗試簡單的 espeak
                if TTS_CONFIG['engine'] != 'espeak':
                    self.logger.warning("所有 TTS 引擎失敗，使用簡單 espeak 作為最終備用")
                    simple_audio_file = audio_file.with_suffix('.simple.wav')
                    try:
                        cmd = ['espeak', '-w', str(simple_audio_file), text]
                        result = subprocess.run(cmd, capture_output=True, timeout=30)
                        if result.returncode == 0 and simple_audio_file.exists():
                            simple_audio_file.rename(audio_file)
                            return audio_file
                    except:
                        pass
                        
                self.logger.error("所有音頻生成方法都失敗")
                return None
                
        except Exception as e:
            self.logger.error(f"生成音頻失敗: {e}")
            return None

    def _generate_audio_openai_direct(self, text: str, language_code: str, voice: str = None) -> Optional[Path]:
        """
        直接使用 OpenAI TTS 生成音頻（繞過其他引擎選擇）
        
        Args:
            text: 要轉換的文字
            language_code: 語言代碼
            voice: 指定的語音模型（可選，默認使用配置中的語音）
        
        Returns:
            Path: 生成的音頻文件路徑，如果失敗則返回 None
        """
        try:
            # 創建音頻文件路徑
            import hashlib
            selected_voice = voice or TTS_CONFIG['openai_voice']
            text_hash = hashlib.md5(f"{text}_{language_code}_{selected_voice}".encode()).hexdigest()
            audio_file = self.cache_dir / f"openai_direct_{language_code}_{selected_voice}_{text_hash}.wav"
            
            # 檢查是否已有快取
            if audio_file.exists():
                self.logger.info(f"使用快取的音頻文件: {audio_file}")
                return audio_file
            
            # 調用 OpenAI TTS API
            if not self.openai_client:
                self.logger.error("OpenAI 客戶端未初始化")
                return None
                
            self.logger.info(f"🤖 使用 OpenAI TTS 生成音頻: {selected_voice}")
            
            # 調用 OpenAI TTS API
            response = self.openai_client.audio.speech.create(
                model=TTS_CONFIG['openai_model'],
                voice=selected_voice,
                input=text,
                speed=TTS_CONFIG['openai_speed']
            )
            
            # OpenAI 返回 MP3，直接保存為 MP3 然後轉換
            temp_mp3_file = audio_file.with_suffix('.mp3')
            
            # 將音頻數據寫入 MP3 文件
            with open(temp_mp3_file, 'wb') as f:
                for chunk in response.iter_bytes(1024):
                    f.write(chunk)
            
            # 驗證 MP3 文件
            if temp_mp3_file.exists() and temp_mp3_file.stat().st_size > 0:
                self.logger.info(f"OpenAI MP3 文件生成成功: {temp_mp3_file.stat().st_size} bytes")
                
                # 轉換 MP3 到 WAV
                try:
                    import subprocess
                    # 嘗試 ffmpeg
                    convert_cmd = ['ffmpeg', '-i', str(temp_mp3_file), '-y', str(audio_file)]
                    result = subprocess.run(convert_cmd, capture_output=True, timeout=30)
                    
                    if result.returncode == 0 and audio_file.exists():
                        self.logger.info("ffmpeg 轉換成功")
                        temp_mp3_file.unlink()  # 刪除臨時 MP3
                    else:
                        # ffmpeg 失敗，嘗試 sox
                        self.logger.warning("ffmpeg 失敗，嘗試 sox")
                        convert_cmd = ['sox', str(temp_mp3_file), str(audio_file)]
                        result = subprocess.run(convert_cmd, capture_output=True, timeout=30)
                        
                        if result.returncode == 0 and audio_file.exists():
                            self.logger.info("sox 轉換成功")
                            temp_mp3_file.unlink()  # 刪除臨時 MP3
                        else:
                            # 兩個都失敗，直接用 MP3
                            self.logger.warning("格式轉換失敗，直接使用 MP3")
                            temp_mp3_file.rename(audio_file.with_suffix('.mp3'))
                            audio_file = audio_file.with_suffix('.mp3')
                            
                except Exception as e:
                    self.logger.warning(f"音頻格式轉換失敗: {e}")
                    # 如果轉換失敗，使用原始 MP3
                    temp_mp3_file.rename(audio_file.with_suffix('.mp3'))
                    audio_file = audio_file.with_suffix('.mp3')
                
                # 最終驗證文件
                if audio_file.exists() and audio_file.stat().st_size > 0:
                    self.logger.info(f"✨ OpenAI TTS 音頻生成成功: {audio_file}")
                    return audio_file
                else:
                    self.logger.error("音頻文件轉換後無效")
                    return None
            else:
                self.logger.error("OpenAI MP3 文件生成失敗")
                return None
                
        except Exception as e:
            self.logger.error(f"Nova 直接生成失敗: {e}")
            return None
    
    def _generate_audio_openai(self, text: str, audio_file: Path) -> Optional[Path]:
        """使用 OpenAI TTS 生成音頻"""
        try:
            if not self.openai_client:
                self.logger.error("OpenAI 客戶端未初始化")
                return None
                
            self.logger.info(f"🤖 使用 OpenAI TTS 生成音頻: {selected_voice}")
            
            # 調用 OpenAI TTS API
            response = self.openai_client.audio.speech.create(
                model=TTS_CONFIG['openai_model'],
                voice=selected_voice,
                input=text,
                speed=TTS_CONFIG['openai_speed']
            )
            
            # OpenAI 返回 MP3，直接保存為 MP3 然後轉換
            temp_mp3_file = audio_file.with_suffix('.mp3')
            
            # 將音頻數據寫入 MP3 文件
            with open(temp_mp3_file, 'wb') as f:
                for chunk in response.iter_bytes(1024):
                    f.write(chunk)
            
            # 驗證 MP3 文件
            if temp_mp3_file.exists() and temp_mp3_file.stat().st_size > 0:
                self.logger.info(f"OpenAI MP3 文件生成成功: {temp_mp3_file.stat().st_size} bytes")
                
                # 轉換 MP3 到 WAV
                try:
                    # 嘗試 ffmpeg
                    convert_cmd = ['ffmpeg', '-i', str(temp_mp3_file), '-y', str(audio_file)]
                    result = subprocess.run(convert_cmd, capture_output=True, timeout=30)
                    
                    if result.returncode == 0 and audio_file.exists():
                        self.logger.info("ffmpeg 轉換成功")
                        temp_mp3_file.unlink()  # 刪除臨時 MP3
                    else:
                        # ffmpeg 失敗，嘗試 sox
                        self.logger.warning("ffmpeg 失敗，嘗試 sox")
                        convert_cmd = ['sox', str(temp_mp3_file), str(audio_file)]
                        result = subprocess.run(convert_cmd, capture_output=True, timeout=30)
                        
                        if result.returncode == 0 and audio_file.exists():
                            self.logger.info("sox 轉換成功")
                            temp_mp3_file.unlink()  # 刪除臨時 MP3
                        else:
                            # 兩個都失敗，直接用 MP3
                            self.logger.warning("格式轉換失敗，直接使用 MP3")
                            temp_mp3_file.rename(audio_file.with_suffix('.mp3'))
                            audio_file = audio_file.with_suffix('.mp3')
                            
                except Exception as e:
                    self.logger.warning(f"音頻格式轉換失敗: {e}")
                    # 如果轉換失敗，使用原始 MP3
                    temp_mp3_file.rename(audio_file.with_suffix('.mp3'))
                    audio_file = audio_file.with_suffix('.mp3')
                
                # 最終驗證文件
                if audio_file.exists() and audio_file.stat().st_size > 0:
                    self.logger.info(f"✨ OpenAI TTS 音頻生成成功: {audio_file}")
                    return audio_file
                else:
                    self.logger.error("音頻文件轉換後無效")
                    return None
            else:
                self.logger.error("OpenAI TTS 生成的 MP3 文件無效")
                return None
                
        except Exception as e:
            self.logger.error(f"OpenAI TTS 音頻生成失敗: {e}")
            return None

    # 已移除備用語音引擎生成函數
    # 現在只支援 OpenAI TTS

    def _validate_wav_file(self, audio_file: Path) -> bool:
        """驗證 WAV 文件格式是否正確"""
        try:
            # 檢查文件大小（至少需要 44 字節的 WAV 頭 + 一些音頻數據）
            if not audio_file.exists() or audio_file.stat().st_size < 100:
                return False
            
            # 讀取 WAV 文件頭
            with open(audio_file, 'rb') as f:
                # 檢查 RIFF 標識
                riff_header = f.read(4)
                if riff_header != b'RIFF':
                    return False
                
                # 讀取文件大小
                file_size = int.from_bytes(f.read(4), byteorder='little')
                
                # 檢查 WAVE 標識
                wave_header = f.read(4)
                if wave_header != b'WAVE':
                    return False
                
                # 尋找必要的 chunks
                found_fmt = False
                found_data = False
                data_size = 0
                
                while f.tell() < len(riff_header) + 4 + file_size:
                    try:
                        chunk_header = f.read(4)
                        if len(chunk_header) < 4:
                            break
                        
                        chunk_size_bytes = f.read(4)
                        if len(chunk_size_bytes) < 4:
                            break
                            
                        chunk_size = int.from_bytes(chunk_size_bytes, byteorder='little')
                        
                        if chunk_header == b'fmt ':
                            found_fmt = True
                            # 跳過 fmt chunk 內容
                            f.seek(chunk_size, 1)
                        elif chunk_header == b'data':
                            found_data = True
                            data_size = chunk_size
                            # 不需要讀取 data chunk 內容
                            f.seek(chunk_size, 1)
                        else:
                            # 跳過其他 chunk
                            f.seek(chunk_size, 1)
                        
                        # 對齊到偶數字節邊界
                        if chunk_size % 2 == 1:
                            f.seek(1, 1)
                            
                    except (struct.error, OSError):
                        break
                
                # 檢查是否找到必要的 chunks 且有實際音頻數據
                return found_fmt and found_data and data_size > 0
                
        except Exception as e:
            self.logger.debug(f"WAV 文件驗證失敗: {e}")
            return False

    def _test_audio_playback(self, audio_file: Path) -> bool:
        """測試音頻文件是否能正確播放（支援 WAV 和 MP3）"""
        try:
            if not PYGAME_AVAILABLE:
                return True  # 如果沒有 pygame，假設可以播放
            
            # 嘗試用 pygame 載入文件
            try:
                pygame.mixer.music.load(str(audio_file))
                return True
            except pygame.error:
                # pygame 失敗，檢查是否有其他播放器
                if audio_file.suffix.lower() == '.mp3':
                    # 檢查是否有 MP3 播放器
                    try:
                        result = subprocess.run(['which', 'mpg123'], 
                                              capture_output=True, timeout=5)
                        if result.returncode == 0:
                            return True
                    except:
                        pass
                    
                    try:
                        result = subprocess.run(['which', 'ffplay'], 
                                              capture_output=True, timeout=5)
                        if result.returncode == 0:
                            return True
                    except:
                        pass
                
                return False
            
        except Exception as e:
            self.logger.debug(f"音頻文件播放測試失敗: {e}")
            return False

    def _enhance_audio_quality(self, audio_file: Path):
        """使用 sox 提高音頻質量"""
        try:
            # 檢查 sox 是否可用
            result = subprocess.run(['sox', '--version'], 
                                  capture_output=True, timeout=5)
            if result.returncode != 0:
                return
            
            # 創建臨時文件用於處理
            temp_file = audio_file.with_suffix('.temp.wav')
            
            # sox 音質增強處理（修復參數格式）
            enhancement_cmd = [
                'sox', str(audio_file), str(temp_file),
                'rate', str(TTS_CONFIG.get('sample_rate_override', 22050)),  # 提高採樣率
                'reverb', '20', '0.5', '50',  # 輕微混響
                'equalizer', '1000', '0.5q', '2',  # 增強中頻
                'compand', '0.3,1', '6:-70,-60,-20', '-5', '-90', '0.2',  # 壓縮和標準化
                'norm', '-1'  # 標準化音量
            ]
            
            result = subprocess.run(enhancement_cmd, 
                                  capture_output=True, timeout=30)
            
            if result.returncode == 0 and temp_file.exists():
                # 替換原文件
                temp_file.replace(audio_file)
                self.logger.debug("音質增強完成")
            else:
                # 如果增強失敗，刪除臨時文件
                if temp_file.exists():
                    temp_file.unlink()
                    
        except Exception as e:
            self.logger.debug(f"音質增強失敗（非致命錯誤）: {e}")
    
    def _play_audio_file(self, audio_file: Path) -> bool:
        """播放音頻文件（支援 WAV 和 MP3）"""
        try:
            if PYGAME_AVAILABLE and self.audio_initialized:
                # 使用 pygame 播放
                try:
                    pygame.mixer.music.load(str(audio_file))
                    pygame.mixer.music.play()
                    
                    # 等待播放完成
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                        
                    self.logger.info(f"音頻播放完成（pygame）: {audio_file.suffix}")
                    return True
                except pygame.error as e:
                    self.logger.warning(f"pygame 播放失敗: {e}")
                    # 如果是 MP3 播放失敗，嘗試其他播放器
                    if audio_file.suffix.lower() == '.mp3':
                        return self._play_with_alternative_player(audio_file)
                    return False
            else:
                # 使用替代播放器
                return self._play_with_alternative_player(audio_file)
                    
        except Exception as e:
            self.logger.error(f"音頻播放失敗: {e}")
            return False
    
    def _play_with_alternative_player(self, audio_file: Path) -> bool:
        """使用替代播放器播放音頻"""
        try:
            # 根據文件格式選擇播放器
            if audio_file.suffix.lower() == '.mp3':
                # 嘗試 mpg123 播放 MP3
                try:
                    result = subprocess.run(['mpg123', str(audio_file)], 
                                          capture_output=True, timeout=30)
                    if result.returncode == 0:
                        self.logger.info("音頻播放完成（mpg123）")
                        return True
                except FileNotFoundError:
                    pass
                
                # 嘗試 ffplay 播放 MP3
                try:
                    result = subprocess.run(['ffplay', '-nodisp', '-autoexit', str(audio_file)], 
                                          capture_output=True, timeout=30)
                    if result.returncode == 0:
                        self.logger.info("音頻播放完成（ffplay）")
                        return True
                except FileNotFoundError:
                    pass
            
            # 使用 aplay 播放 WAV（或作為最後嘗試）
            result = subprocess.run(['aplay', str(audio_file)], 
                                  capture_output=True, timeout=30)
            if result.returncode == 0:
                self.logger.info("音頻播放完成（aplay）")
                return True
            else:
                self.logger.error(f"aplay 播放失敗: {result.stderr}")
                return False
                    
        except Exception as e:
            self.logger.error(f"替代播放器失敗: {e}")
            return False
    
    def set_volume(self, volume: int) -> bool:
        """
        設置音量
        
        Args:
            volume: 音量 (0-100)
        
        Returns:
            bool: 設置是否成功
        """
        try:
            volume = max(0, min(100, volume))  # 限制範圍
            
            # 嘗試不同的音量控制名稱
            volume_controls = ['PCM', 'Master', 'Speaker', 'Headphone', 'HDMI']
            
            for control in volume_controls:
                try:
                    # 使用 amixer 設置系統音量
                    result = subprocess.run([
                        'amixer', 'sset', control, f'{volume}%'
                    ], capture_output=True, timeout=5)
                    
                    if result.returncode == 0:
                        self.current_volume = volume
                        self.logger.info(f"音量設置為: {volume}% (使用 {control} 控制)")
                        return True
                    else:
                        self.logger.debug(f"嘗試 {control} 控制失敗: {result.stderr.decode().strip()}")
                        
                except Exception as e:
                    self.logger.debug(f"嘗試 {control} 控制時發生錯誤: {e}")
                    continue
            
            # 如果所有控制都失敗，記錄警告但不阻止程序運行
            self.logger.warning("無法設置音量，但音頻播放可能仍然正常")
            self.current_volume = volume
            return True
                
        except Exception as e:
            self.logger.error(f"音量設置失敗: {e}")
            return False

    def play_notification_sound(self, sound_type: str = 'success') -> bool:
        """
        播放通知音效
        
        Args:
            sound_type: 音效類型 ('success', 'error', 'click')
        
        Returns:
            bool: 播放是否成功
        """
        try:
            if not AUDIO_CONFIG['enabled']:
                self.logger.debug("音頻功能已禁用，跳過通知音效")
                return True
            
            # 根據音效類型選擇不同的問候語
            if sound_type == 'success':
                # 播放簡短的成功音效（使用嗶聲而不是完整問候語）
                self.logger.info("播放成功提示音")
                return self._play_simple_beep(frequency=880, duration=0.1)
            elif sound_type == 'error':
                # 播放錯誤提示音
                self.logger.info("播放錯誤提示音")
                return self._play_simple_beep()
            elif sound_type == 'click':
                # 播放點擊音效
                self.logger.info("播放點擊音效")
                return self._play_simple_beep(frequency=800, duration=0.1)
            else:
                self.logger.warning(f"未知的音效類型: {sound_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"播放通知音效失敗: {e}")
            return False

    def _play_simple_beep(self, frequency: int = 440, duration: float = 0.2) -> bool:
        """
        播放簡單的嗶聲
        
        Args:
            frequency: 頻率 (Hz)
            duration: 持續時間 (秒)
        
        Returns:
            bool: 播放是否成功
        """
        try:
            # 首先嘗試使用 aplay 播放預設的提示音
            beep_file = Path(AUDIO_FILES.get('error', ''))
            if beep_file.exists():
                try:
                    subprocess.run(
                        ['aplay', str(beep_file)],
                        timeout=2,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return True
                except Exception:
                    self.logger.warning("使用 aplay 播放提示音失敗，嘗試其他方法")
            
            # 如果沒有提示音檔案，嘗試使用 beep 命令
            try:
                subprocess.run(
                    ['beep', '-f', str(frequency), '-l', str(int(duration * 1000))],
                    timeout=2,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
            except Exception:
                self.logger.warning("使用 beep 命令失敗，嘗試 espeak")
            
            # 最後嘗試使用 espeak
            subprocess.run(
                ['espeak', '-s', '200', 'beep'],
                timeout=2,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
                
        except Exception as e:
            self.logger.error(f"播放嗶聲失敗: {e}")
            return False
    
    def get_volume(self) -> int:
        """獲取當前音量"""
        return self.current_volume
    
    def test_audio(self) -> bool:
        """測試音頻系統"""
        try:
            return self.play_greeting('US', 'Test City')
        except Exception as e:
            self.logger.error(f"音頻測試失敗: {e}")
            return False
    
    def _cleanup_cache(self):
        """清理過期的快取文件"""
        try:
            if not TTS_CONFIG['cache_enabled']:
                return
            
            current_time = time.time()
            cache_files = list(self.cache_dir.glob("greeting_*.wav"))
            
            # 按修改時間排序
            cache_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # 刪除過期文件
            for audio_file in cache_files:
                file_age = current_time - audio_file.stat().st_mtime
                if file_age > AUDIO_FILES['cache_timeout']:
                    audio_file.unlink()
                    self.logger.debug(f"刪除過期快取文件: {audio_file}")
            
            # 限制快取文件數量
            if len(cache_files) > AUDIO_FILES['max_cache_size']:
                for audio_file in cache_files[AUDIO_FILES['max_cache_size']:]:
                    if audio_file.exists():
                        audio_file.unlink()
                        self.logger.debug(f"刪除超量快取文件: {audio_file}")
                        
        except Exception as e:
            self.logger.error(f"清理快取失敗: {e}")
    
    def cleanup(self):
        """清理資源"""
        try:
            if PYGAME_AVAILABLE and self.audio_initialized:
                pygame.mixer.quit()
            
            if self.tts_engine:
                try:
                    self.tts_engine.stop()
                except:
                    pass
            
            self.logger.info("音頻管理器已清理")
            
        except Exception as e:
            self.logger.error(f"音頻管理器清理失敗: {e}")

# 全域音頻管理器實例
audio_manager = None

def get_audio_manager() -> AudioManager:
    """獲取音頻管理器實例"""
    global audio_manager
    if audio_manager is None:
        audio_manager = AudioManager()
    return audio_manager

def cleanup_audio_manager():
    """清理音頻管理器"""
    global audio_manager
    if audio_manager:
        audio_manager.cleanup()
        audio_manager = None 
