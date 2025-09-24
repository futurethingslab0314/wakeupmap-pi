#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試使用者名稱修復
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

def test_user_name_consistency():
    """測試使用者名稱一致性"""
    print("🔧 測試使用者名稱一致性...")
    
    # 載入環境變數
    success = load_env_file()
    
    if success:
        # 測試環境變數
        env_user_name = os.getenv('USER_NAME', '未設定')
        print(f"✅ 環境變數 USER_NAME: {env_user_name}")
        
        # 測試各個模組的使用者名稱
        modules_to_test = [
            ('config.py', 'USER_CONFIG'),
            ('web_controller_dsi.py', 'USER_NAME'),
            ('main_web_dsi.py', 'USER_CONFIG')
        ]
        
        for module_name, config_name in modules_to_test:
            try:
                if module_name == 'config.py':
                    from config import USER_CONFIG
                    user_name = USER_CONFIG['display_name']
                elif module_name == 'web_controller_dsi.py':
                    from web_controller_dsi import USER_NAME
                    user_name = USER_NAME
                elif module_name == 'main_web_dsi.py':
                    from main_web_dsi import USER_CONFIG
                    user_name = USER_CONFIG['display_name']
                
                print(f"✅ {module_name} {config_name}: {user_name}")
                
                # 檢查是否與環境變數一致
                if user_name == env_user_name:
                    print(f"   ✅ 與環境變數一致")
                else:
                    print(f"   ❌ 與環境變數不一致！環境變數: {env_user_name}, 模組: {user_name}")
                    
            except Exception as e:
                print(f"❌ {module_name} 讀取失敗: {e}")
        
        print("\n🎉 使用者名稱一致性測試完成！")
        
        if env_user_name == '未設定':
            print("⚠️ 警告：USER_NAME 未設定，請檢查 .env 檔案")
        elif env_user_name == 'future':
            print("⚠️ 警告：使用者名稱仍為 'future'，請檢查 .env 檔案中的 USER_NAME 設定")
        else:
            print(f"✅ 使用者名稱已正確設定為: {env_user_name}")
    else:
        print("❌ 環境變數載入失敗！")

if __name__ == "__main__":
    test_user_name_consistency()
