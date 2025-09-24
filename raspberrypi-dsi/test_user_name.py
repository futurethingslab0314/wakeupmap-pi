#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試使用者名稱設定
"""

import os
from pathlib import Path

# 自動載入 .env 檔案
def load_env_file():
    """載入 .env 檔案到環境變數"""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        print(f"🔧 載入環境變數檔案: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ 環境變數載入完成")
        return True
    else:
        print(f"❌ .env 檔案不存在: {env_file}")
        return False

def test_user_name():
    """測試使用者名稱設定"""
    print("🔧 測試使用者名稱設定...")
    
    # 載入環境變數
    success = load_env_file()
    
    if success:
        # 測試環境變數
        user_name = os.getenv('USER_NAME', '未設定')
        print(f"✅ 環境變數 USER_NAME: {user_name}")
        
        # 測試配置讀取
        try:
            from config import USER_CONFIG
            print(f"✅ 配置 USER_CONFIG['display_name']: {USER_CONFIG['display_name']}")
            print(f"✅ 配置 USER_CONFIG['identifier']: {USER_CONFIG['identifier']}")
        except Exception as e:
            print(f"❌ 配置讀取失敗: {e}")
        
        # 測試 web_controller_dsi 讀取
        try:
            from web_controller_dsi import USER_NAME
            print(f"✅ web_controller_dsi USER_NAME: {USER_NAME}")
        except Exception as e:
            print(f"❌ web_controller_dsi 讀取失敗: {e}")
        
        print("\n🎉 使用者名稱設定測試完成！")
        
        if user_name == '未設定':
            print("⚠️ 警告：USER_NAME 未設定，請檢查 .env 檔案")
        else:
            print(f"✅ 使用者名稱已正確設定為: {user_name}")
    else:
        print("❌ 環境變數載入失敗！")

if __name__ == "__main__":
    test_user_name()
