#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試配置檔案載入
"""

import os
from config import TTS_CONFIG, USER_CONFIG

def test_config_loading():
    """測試配置檔案載入"""
    print("🔧 測試配置檔案載入...")
    
    # 測試基本配置
    print(f"✅ TTS 引擎: {TTS_CONFIG['engine']}")
    print(f"✅ OpenAI 語音: {TTS_CONFIG['openai_voice']}")
    print(f"✅ OpenAI 模型: {TTS_CONFIG['openai_model']}")
    
    # 測試環境變數讀取
    print(f"✅ OpenAI API Key: {TTS_CONFIG['openai_api_key'][:20] if TTS_CONFIG['openai_api_key'] else '未設定'}...")
    print(f"✅ 使用者名稱: {USER_CONFIG['display_name']}")
    
    # 測試環境變數
    print(f"✅ 環境變數 OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', '未設定')[:20] if os.getenv('OPENAI_API_KEY') else '未設定'}...")
    print(f"✅ 環境變數 USER_NAME: {os.getenv('USER_NAME', '未設定')}")
    
    print("\n🎉 配置檔案載入測試完成！")

if __name__ == "__main__":
    test_config_loading()
