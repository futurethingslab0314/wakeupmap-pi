#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試環境變數載入
"""

import os
from pathlib import Path

def load_env_file():
    """載入 .env 檔案到環境變數"""
    env_file = Path(__file__).parent.parent / '.env'
    print(f"🔍 尋找 .env 檔案: {env_file}")
    
    if env_file.exists():
        print(f"✅ 找到 .env 檔案")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f"  📝 載入: {key} = {value[:20] if len(value) > 20 else value}...")
        print("✅ 環境變數載入完成")
        return True
    else:
        print(f"❌ .env 檔案不存在: {env_file}")
        return False

def test_env_variables():
    """測試環境變數"""
    print("\n🧪 測試環境變數:")
    print(f"  OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', '未設定')[:20] if os.getenv('OPENAI_API_KEY') else '未設定'}...")
    print(f"  USER_NAME: {os.getenv('USER_NAME', '未設定')}")
    print(f"  FIREBASE_PROJECT_ID: {os.getenv('FIREBASE_PROJECT_ID', '未設定')}")

if __name__ == "__main__":
    print("🔧 測試環境變數載入...")
    
    # 載入前
    print("\n📋 載入前:")
    test_env_variables()
    
    # 載入 .env
    success = load_env_file()
    
    # 載入後
    print("\n📋 載入後:")
    test_env_variables()
    
    if success:
        print("\n🎉 環境變數載入測試完成！")
    else:
        print("\n❌ 環境變數載入失敗！")
