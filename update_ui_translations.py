# update_ui_translations.py - 更新数据库中的UI翻译
# 运行此脚本以添加所有语言的UI翻译

import sqlite3
import os

def update_ui_translations():
    """更新数据库中的UI翻译"""
    
    # 检查数据库是否存在
    if not os.path.exists('database/yonaguni_dict.db'):
        print("❌ 错误：数据库文件不存在！请先运行 init_database.py 初始化数据库。")
        return
    
    # 检查SQL文件是否存在
    if not os.path.exists('database/ui_translations.sql'):
        print("❌ 错误：ui_translations.sql 文件不存在！")
        print("请将提供的UI翻译SQL代码保存为 database/ui_translations.sql")
        return
    
    # 连接数据库
    conn = sqlite3.connect('database/yonaguni_dict.db')
    cursor = conn.cursor()
    
    try:
        # 读取并执行SQL文件
        with open('database/ui_translations.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        cursor.executescript(sql_script)
        conn.commit()
        
        # 验证翻译数量
        cursor.execute("SELECT COUNT(DISTINCT key) as key_count, COUNT(DISTINCT language) as lang_count FROM ui_translations")
        result = cursor.fetchone()
        
        print(f"✅ UI翻译更新成功！")
        print(f"   - 翻译键数量: {result[0]}")
        print(f"   - 支持语言数: {result[1]}")
        
        # 显示支持的语言
        cursor.execute("SELECT DISTINCT language FROM ui_translations ORDER BY language")
        languages = [row[0] for row in cursor.fetchall()]
        print(f"   - 支持的语言: {', '.join(languages)}")
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    update_ui_translations()