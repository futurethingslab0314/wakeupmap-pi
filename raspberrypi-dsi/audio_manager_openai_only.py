#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WakeUpMap - 音頻管理模組 (僅支援 OpenAI TTS)
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

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from config import (
    AUDIO_CONFIG, 
    TTS_CONFIG, 
    SPEAKER_CONFIG,
    MORNING_GREETINGS,
    TTS_LANGUAGE_MAP,
    AUDIO_FILES
)

class AudioManager:
    """音頻管理器 - 僅支援 OpenAI TTS"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.openai_client = None
        self.audio_initialized = False
        self.current_volume = AUDIO_CONFIG['volume']
        self.cache_dir = Path(TTS_CONFIG['cache_dir'])
        
        # 確保快取目錄存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化音頻系統
        self._initialize_audio()
        
        # 初始化 TTS 引擎
        self._initialize_tts()
    
    def _initialize_audio(self):
        """初始化音頻系統"""
        try:
            # 檢查音頻設備
            self._check_audio_devices()
            
            # 初始化 Pygame 音頻
            if PYGAME_AVAILABLE:
                try:
                    pygame.mixer.init(
                        frequency=AUDIO_CONFIG['sample_rate'],
                        size=-16,  # 16-bit
                        channels=AUDIO_CONFIG['channels'],
                        buffer=1024
                    )
                    self.audio_initialized = True
                    self.logger.info("Pygame 音頻系統初始化成功")
                except Exception as e:
                    self.logger.warning(f"Pygame 初始化失敗: {e}")
            
            # 設置音量
            self.set_volume(self.current_volume)
            
        except Exception as e:
            self.logger.error(f"音頻系統初始化失敗: {e}")
    
    def _check_audio_devices(self):
        """檢查音頻設備"""
        try:
            # 檢查 ALSA 音頻設備
            result = subprocess.run(['aplay', '-l'], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.logger.info("ALSA 音頻設備檢查成功")
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
            self.logger.info(f"🎧 播放問候語: {city_name}, {country_name}")
            
            # 準備音頻內容
            audio_file, greeting_data = self.prepare_greeting_audio_with_content(
                country_code, city_name, country_name
            )
            
            if audio_file and audio_file.exists():
                # 播放音頻
                success = self.play_audio_file_direct(audio_file)
                if success:
                    self.logger.info("✅ 問候語播放成功")
                    return True
                else:
                    self.logger.error("❌ 問候語播放失敗")
                    return False
            else:
                self.logger.warning("⚠️ 沒有音頻文件可播放")
                return False
                
        except Exception as e:
            self.logger.error(f"播放問候語失敗: {e}")
            return False
    
    def prepare_greeting_audio_with_content(self, country_code: str, city_name: str = "", country_name: str = "", city_data: dict = None) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        """
        準備完整問候語音頻（同步模式）
        
        Returns:
            Tuple[Path, Dict]: (音頻文件路徑, 問候語資料)
        """
        try:
            if not AUDIO_CONFIG['enabled']:
                self.logger.info("音頻功能已禁用，返回空結果")
                return None, None
            
            self.logger.info("🎧 準備完整問候語音頻（同步模式）...")
            
            # 調用故事生成 API
            greeting_data = self._call_story_generation_api(country_code, city_name, country_name, city_data)
            
            if greeting_data and greeting_data.get('success'):
                # 生成 Nova 整合音頻
                audio_file = self._generate_nova_integrated_audio(greeting_data, city_name, country_name)
                
                if audio_file and audio_file.exists():
                    self.logger.info(f"✨ Nova 整合音頻生成成功: {audio_file.name}")
                    return audio_file, greeting_data
                else:
                    self.logger.error("Nova 整合音頻生成失敗")
                    return None, None
            else:
                self.logger.warning("ChatGPT API 失敗，無法準備音頻")
                return None, None
                
        except Exception as e:
            self.logger.error(f"準備完整音頻失敗: {e}")
            return None, None
    
    def _call_story_generation_api(self, country_code: str, city_name: str, country_name: str, city_data: dict = None) -> Optional[Dict[str, Any]]:
        """調用故事生成 API"""
        try:
            import requests
            
            # 準備 API 請求資料
            api_data = {
                'country_code': country_code,
                'city_name': city_name,
                'country_name': country_name,
                'city_data': city_data or {}
            }
            
            # 調用 API
            response = requests.post(
                TTS_CONFIG.get('story_api_url', 'https://subjective-clock.vercel.app/api/generatePiStory'),
                json=api_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info("✅ 故事生成 API 調用成功")
                return result
            else:
                self.logger.error(f"API 請求失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"調用故事生成 API 時發生錯誤: {e}")
            return None
    
    def _generate_nova_integrated_audio(self, greeting_data: Dict[str, Any], city_name: str, country_name: str) -> Optional[Path]:
        """生成 Nova 整合音頻"""
        try:
            # 提取問候語和故事內容
            greeting_text = greeting_data.get('greeting', '')
            story_text = greeting_data.get('chineseStory', '')
            language_code = greeting_data.get('language', 'en')
            
            if not story_text:
                self.logger.warning("沒有故事內容，跳過音頻生成")
                return None
            
            # 準備完整內容
            full_content = f"{greeting_text}\n\n{story_text}"
            
            # 生成音頻文件
            audio_file = self._generate_audio_openai_direct(full_content, language_code, voice='nova')
            
            if audio_file and audio_file.exists():
                self.logger.info(f"✨ Nova 整合音頻生成成功: {audio_file.name}")
                return audio_file
            else:
                self.logger.error("Nova 整合音頻生成失敗")
                return None
                
        except Exception as e:
            self.logger.error(f"Nova 整合音頻生成失敗: {e}")
            return None
    
    def _generate_audio_openai_direct(self, text: str, language_code: str, voice: str = None) -> Optional[Path]:
        """
        直接使用 OpenAI TTS 生成音頻
        
        Args:
            text: 要轉換的文字
            language_code: 語言代碼
            voice: 指定的語音模型（可選，默認使用配置中的語音）
        
        Returns:
            Path: 生成的音頻文件路徑，如果失敗則返回 None
        """
        try:
            if not self.openai_client:
                self.logger.error("OpenAI 客戶端未初始化")
                return None
            
            # 使用配置中的語音
            selected_voice = voice or TTS_CONFIG['openai_voice']
            
            self.logger.info(f"🤖 使用 OpenAI TTS 生成音頻: {selected_voice}")
            
            # 生成唯一的文件名
            text_hash = hashlib.md5(f"{text}_{language_code}_{selected_voice}".encode()).hexdigest()
            audio_file = self.cache_dir / f"nova_{language_code}_{text_hash}.mp3"
            
            # 調用 OpenAI TTS API
            response = self.openai_client.audio.speech.create(
                model=TTS_CONFIG['openai_model'],
                voice=selected_voice,
                input=text,
                speed=TTS_CONFIG['openai_speed']
            )
            
            # 保存音頻文件
            with open(audio_file, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            if audio_file.exists() and audio_file.stat().st_size > 1000:
                self.logger.info(f"✨ OpenAI TTS 音頻生成成功: {audio_file}")
                return audio_file
            else:
                self.logger.error("OpenAI MP3 文件生成失敗")
                return None
                
        except Exception as e:
            self.logger.error(f"OpenAI TTS 音頻生成失敗: {e}")
            return None
    
    def play_audio_file_direct(self, audio_file: Path) -> bool:
        """直接播放音頻文件"""
        try:
            if not audio_file.exists():
                self.logger.error(f"音頻文件不存在: {audio_file}")
                return False
            
            if PYGAME_AVAILABLE and self.audio_initialized:
                # 使用 Pygame 播放
                try:
                    pygame.mixer.music.load(str(audio_file))
                    pygame.mixer.music.play()
                    
                    # 等待播放完成
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    self.logger.info("✅ Pygame 音頻播放完成")
                    return True
                except Exception as e:
                    self.logger.warning(f"Pygame 播放失敗: {e}")
                    return self._play_with_alternative_player(audio_file)
            else:
                # 使用替代播放器
                return self._play_with_alternative_player(audio_file)
                
        except Exception as e:
            self.logger.error(f"音頻播放失敗: {e}")
            return False
    
    def _play_with_alternative_player(self, audio_file: Path) -> bool:
        """使用替代播放器播放音頻"""
        try:
            # 嘗試使用 aplay 播放
            cmd = ['aplay', str(audio_file)]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("✅ aplay 音頻播放成功")
                return True
            else:
                self.logger.error(f"aplay 播放失敗: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"替代播放器失敗: {e}")
            return False
    
    def set_volume(self, volume: int) -> bool:
        """設置音量 (0-100)"""
        try:
            volume = max(0, min(100, volume))
            self.current_volume = volume
            
            # 設置 ALSA 音量
            alsa_volume = int(volume * 0.63)  # 轉換為 ALSA 範圍 (0-63)
            
            # 嘗試不同的音量控制方法
            controls = ['Master', 'PCM', 'Speaker']
            for control in controls:
                try:
                    cmd = ['amixer', 'set', control, f'{alsa_volume}%']
                    result = subprocess.run(cmd, capture_output=True, timeout=5)
                    if result.returncode == 0:
                        self.logger.info(f"音量設置成功: {control} = {volume}%")
                        return True
                except:
                    continue
            
            return True
                
        except Exception as e:
            self.logger.error(f"音量設置失敗: {e}")
            return False
    
    def test_audio(self) -> bool:
        """測試音頻系統"""
        try:
            return self.play_greeting('US', 'Test City')
        except Exception as e:
            self.logger.error(f"音頻測試失敗: {e}")
            return False
    
    def cleanup(self):
        """清理資源"""
        try:
            if PYGAME_AVAILABLE and self.audio_initialized:
                pygame.mixer.quit()
            
            # 清理快取
            self._cleanup_cache()
            
            self.logger.info("音頻管理器已清理")
            
        except Exception as e:
            self.logger.error(f"音頻管理器清理失敗: {e}")
    
    def _cleanup_cache(self):
        """清理音頻快取"""
        try:
            if not self.cache_dir.exists():
                return
            
            # 刪除超過 24 小時的快取文件
            current_time = time.time()
            for audio_file in self.cache_dir.glob("*.mp3"):
                if current_time - audio_file.stat().st_mtime > 86400:  # 24小時
                    audio_file.unlink()
                    self.logger.debug(f"刪除過期快取文件: {audio_file}")
                    
        except Exception as e:
            self.logger.error(f"清理快取失敗: {e}")
