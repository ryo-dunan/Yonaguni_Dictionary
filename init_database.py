# init_database.py - 数据库初始化和数据管理脚本
# 这个脚本用于初始化数据库和添加词条数据

import sqlite3
import json
import os

def create_database():
    """创建数据库并初始化表结构"""
    # 确保database文件夹存在
    if not os.path.exists('database'):
        os.makedirs('database')
    
    # 连接数据库（如果不存在会自动创建）
    conn = sqlite3.connect('database/yonaguni_dict.db')
    cursor = conn.cursor()

    # 读取并执行SQL schema文件
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read() 
    
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    
    print("✅ 数据库创建成功！")

def add_sample_entries():
    """添加示例词条数据"""
    conn = sqlite3.connect('database/yonaguni_dict.db')
    cursor = conn.cursor()
    
    # 示例词条数据
    sample_entries = [
        {
            'headword': 'てぃだん',
            'kana': 'てぃだん',
            'ipa': '/tidan/',
            'pos': '名詞',
            'tone': 'C',
            'meanings': {
                'ja': ['太陽'],
                'zh-tw': ['太陽'],
                'en': ['sun']
            },
            'examples': [
                {
                    'yonaguni': 'てぃだんや ‘とぅや くらぬん',
                    'translations': {
                        'ja': {
                            'word_by_word': '太陽-主題 人-主題　殺さない',
                            'free_translation': '太陽は人を殺さない(太陽は人間を殺さない。すべてに恵みを与えてくれる)「与那国のことわざ」より。'
                        },
                        'zh-tw': {
                            'word_by_word': '太陽-主題 人-主題　不杀',
                            'free_translation': '太陽不會殺人(太陽不會殺人，而是會給予一切以恩惠)出自「与那国のことわざ（與那國的諺語）」。'
                        },
                        'en': {
                            'word_by_word': 'sun-TOP people-TOP　kill-NEG-IND',
                            'free_translation': 'The sun never kills(but benefits everything in the world).'
                        },
                        
                       
                    }
                }
            ]
        },
        {
            'headword': 'あいぐん',
            'kana': 'あいぐん',
            'ipa': 'aiguŋ',
            'pos': '動詞',
            'verb_class': 'C-',
            'tone': 'B',
            'meanings': {
                'ja': ['歩く', '走る'],
                'zh-tw': ['走', '跑'],
                'en': ['to walk', 'to run']
            },
            'conjugations': [
                {'form': '現在形', 'conjugated': 'あいぐん'},
                {'form': '過去形', 'conjugated': 'あいてぃたん'},
                {'form': '完了形', 'conjugated': 'あいてゃん'},
                {'form': '否定形', 'conjugated': 'あいがぬん'},
                {'form': '連用形', 'conjugated': 'あいてぃ'},
                {'form': '連体形', 'conjugated': 'あいぐ'},
                {'form': '受身形', 'conjugated': 'あいがりるん'},
                {'form': '使役形', 'conjugated': 'あいがみるん'}
            ],
            'examples': [
                {
                    'yonaguni': 'はま　あいぐん',
                    'translations': {
                        'ja': {
                            'word_by_word': '砂浜　歩く',
                            'free_translation': '砂浜を歩く'
                        }
                    }
                }
            ]
        },
        {
            'headword': 'どぅー',
            'kana': 'どぅー',
            'ipa': 'duː',
            'pos': '名詞',
            'tone': '平板型',
            'meanings': {
                'ja': ['自分', '自身'],
                'zh-tw': ['自己'],
                'en': ['self', 'oneself']
            }
        }
    ]
    
    # 插入示例数据
    for entry_data in sample_entries:
        try:
            # 插入主词条
            cursor.execute('''
                INSERT INTO entries 
                (headword, kana, ipa, pos, verb_class, tone, etymology, historical_change)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_data['headword'],
                entry_data.get('kana'),
                entry_data.get('ipa'),
                entry_data.get('pos'),
                entry_data.get('verb_class'),
                entry_data.get('tone'),
                entry_data.get('etymology'),
                entry_data.get('historical_change')
            ))
            
            entry_id = cursor.lastrowid
            
            # 插入词义
            if 'meanings' in entry_data:
                for lang, meanings in entry_data['meanings'].items():
                    for i, meaning in enumerate(meanings, 1):
                        cursor.execute('''
                            INSERT INTO meanings 
                            (entry_id, language, meaning_number, definition)
                            VALUES (?, ?, ?, ?)
                        ''', (entry_id, lang, i, meaning))
            
            # 插入动词活用
            if 'conjugations' in entry_data:
                for conj in entry_data['conjugations']:
                    cursor.execute('''
                        INSERT INTO conjugations 
                        (entry_id, form_name, conjugated_form)
                        VALUES (?, ?, ?)
                    ''', (entry_id, conj['form'], conj['conjugated']))
            
            # 插入例句
            if 'examples' in entry_data:
                for example in entry_data['examples']:
                    cursor.execute('''
                        INSERT INTO examples (entry_id, yonaguni_sentence)
                        VALUES (?, ?)
                    ''', (entry_id, example['yonaguni']))
                    
                    example_id = cursor.lastrowid
                    
                    # 插入例句翻译
                    if 'translations' in example:
                        for lang, trans in example['translations'].items():
                            cursor.execute('''
                                INSERT INTO example_translations 
                                (example_id, language, word_by_word, free_translation)
                                VALUES (?, ?, ?, ?)
                            ''', (example_id, lang, 
                                  trans.get('word_by_word'), 
                                  trans.get('free_translation')))
            
            print(f"✅ 添加词条: {entry_data['headword']}")
            
        except sqlite3.IntegrityError as e:
            print(f"⚠️  词条 {entry_data['headword']} 可能已存在: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ 示例数据添加完成！")

def add_new_entry():
    """交互式添加新词条"""
    print("\n=== 添加新词条 ===")
    
    # 收集基本信息
    headword = input("见出语（与那国语）: ").strip()
    if not headword:
        print("见出语不能为空！")
        return
    
    kana = input("假名表记（可选）: ").strip() or None
    ipa = input("IPA表记（可选）: ").strip() or None
    pos = input("品词（名詞/動詞/形容詞等）: ").strip() or None
    
    verb_class = None
    if pos == '動詞':
        verb_class = input("动词类别: ").strip() or None
    
    tone = input("音调（可选）: ").strip() or None
    etymology = input("语源（可选）: ").strip() or None
    
    # 收集词义
    meanings = {'ja': [], 'zh-tw': [], 'en': []}
    
    print("\n添加日语词义（输入空行结束）:")
    while True:
        meaning = input("  词义: ").strip()
        if not meaning:
            break
        meanings['ja'].append(meaning)
    
    if input("\n是否添加中文词义？(y/n): ").lower() == 'y':
        print("添加繁体中文词义（输入空行结束）:")
        while True:
            meaning = input("  词义: ").strip()
            if not meaning:
                break
            meanings['zh-tw'].append(meaning)
    
    if input("\n是否添加英文词义？(y/n): ").lower() == 'y':
        print("添加英文词义（输入空行结束）:")
        while True:
            meaning = input("  词义: ").strip()
            if not meaning:
                break
            meanings['en'].append(meaning)
    
    # 构建数据结构
    entry_data = {
        'headword': headword,
        'kana': kana,
        'ipa': ipa,
        'pos': pos,
        'verb_class': verb_class,
        'tone': tone,
        'etymology': etymology,
        'meanings': {k: v for k, v in meanings.items() if v}  # 只保留有内容的语言
    }
    
    # 保存到数据库
    conn = sqlite3.connect('database/yonaguni_dict.db')
    cursor = conn.cursor()
    
    try:
        # 插入主词条
        cursor.execute('''
            INSERT INTO entries 
            (headword, kana, ipa, pos, verb_class, tone, etymology)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry_data['headword'],
            entry_data.get('kana'),
            entry_data.get('ipa'),
            entry_data.get('pos'),
            entry_data.get('verb_class'),
            entry_data.get('tone'),
            entry_data.get('etymology')
        ))
        
        entry_id = cursor.lastrowid
        
        # 插入词义
        for lang, meanings in entry_data.get('meanings', {}).items():
            for i, meaning in enumerate(meanings, 1):
                cursor.execute('''
                    INSERT INTO meanings 
                    (entry_id, language, meaning_number, definition)
                    VALUES (?, ?, ?, ?)
                ''', (entry_id, lang, i, meaning))
        
        conn.commit()
        print(f"\n✅ 词条 '{headword}' 添加成功！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 添加失败: {e}")
    
    finally:
        conn.close()

def export_data():
    """导出数据库数据为JSON格式"""
    conn = sqlite3.connect('database/yonaguni_dict.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有词条
    cursor.execute('SELECT * FROM entries')
    entries = cursor.fetchall()
    
    export_data = []
    
    for entry in entries:
        entry_dict = dict(entry)
        entry_id = entry['id']
        
        # 获取词义
        cursor.execute('''
            SELECT language, meaning_number, definition 
            FROM meanings 
            WHERE entry_id = ?
            ORDER BY language, meaning_number
        ''', (entry_id,))
        
        meanings = {}
        for row in cursor.fetchall():
            lang = row['language']
            if lang not in meanings:
                meanings[lang] = []
            meanings[lang].append(row['definition'])
        entry_dict['meanings'] = meanings
        
        # 获取例句
        cursor.execute('''
            SELECT ex.id, ex.yonaguni_sentence
            FROM examples ex
            WHERE ex.entry_id = ?
        ''', (entry_id,))
        
        examples = []
        for ex_row in cursor.fetchall():
            example = {
                'yonaguni': ex_row['yonaguni_sentence'],
                'translations': {}
            }
            
            # 获取例句翻译
            cursor.execute('''
                SELECT language, word_by_word, free_translation
                FROM example_translations
                WHERE example_id = ?
            ''', (ex_row['id'],))
            
            for trans_row in cursor.fetchall():
                example['translations'][trans_row['language']] = {
                    'word_by_word': trans_row['word_by_word'],
                    'free_translation': trans_row['free_translation']
                }
            
            examples.append(example)
        
        if examples:
            entry_dict['examples'] = examples
        
        export_data.append(entry_dict)
    
    conn.close()
    
    # 保存为JSON文件
    with open('yonaguni_dict_export.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 导出成功！共导出 {len(export_data)} 个词条到 yonaguni_dict_export.json")

def main_menu():
    """主菜单"""
    while True:
        print("\n=== 与那国语词典数据库管理 ===")
        print("1. 初始化数据库")
        print("2. 添加示例数据")
        print("3. 添加新词条")
        print("4. 导出数据")
        print("0. 退出")
        
        choice = input("\n请选择操作 (0-4): ").strip()
        
        if choice == '1':
            create_database()
        elif choice == '2':
            add_sample_entries()
        elif choice == '3':
            add_new_entry()
        elif choice == '4':
            export_data()
        elif choice == '0':
            print("再见！")
            break
        else:
            print("无效的选择，请重试。")

if __name__ == '__main__':
    # 首先检查schema.sql文件是否存在
    if not os.path.exists('database/schema.sql'):
        print("❌ 错误：database/schema.sql 文件不存在！")
        print("请先将之前提供的SQL代码保存为 database/schema.sql 文件。")
    else:
        main_menu()