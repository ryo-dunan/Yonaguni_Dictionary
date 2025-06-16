# app.py - 与那国语词典后端主程序
# 这个文件是整个Web应用的核心，处理所有的HTTP请求和数据库操作

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # 处理跨域请求
import sqlite3
import json
from datetime import datetime

# 创建Flask应用实例
app = Flask(__name__)
# 启用CORS，允许前端跨域访问
CORS(app)

# 数据库文件路径
DATABASE = 'database/yonaguni_dict.db'

def get_db_connection():
    """
    创建并返回数据库连接
    每次需要访问数据库时调用此函数
    """
    conn = sqlite3.connect(DATABASE)
    # 设置row_factory，使查询结果可以像字典一样访问
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    初始化数据库
    读取SQL文件并执行，创建所有必要的表
    """
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    conn = get_db_connection()
    conn.executescript(sql_script)
    conn.commit()
    conn.close()
    print("数据库初始化完成！")

@app.route('/')
def index():
    """
    主页路由
    返回主HTML页面
    """
    return render_template('index.html')

@app.route('/api/ui-translations/<language>')
def get_ui_translations(language):
    """
    获取指定语言的UI翻译
    参数：language - 语言代码（ja, zh-tw, en, yonaguni）
    返回：JSON格式的翻译键值对
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 查询指定语言的所有UI翻译
    cursor.execute('''
        SELECT key, translation 
        FROM ui_translations 
        WHERE language = ?
    ''', (language,))
    
    # 将结果转换为字典格式
    translations = {}
    for row in cursor.fetchall():
        translations[row['key']] = row['translation']
    
    conn.close()
    return jsonify(translations)

@app.route('/api/search', methods=['POST'])
def search():
    """
    搜索API端点
    接收搜索参数，返回匹配的词条列表
    """
    # 获取请求参数
    data = request.json
    query = data.get('query', '')  # 搜索关键词
    search_type = data.get('search_type', 'headword')  # 搜索类型：headword或fulltext
    match_type = data.get('match_type', 'prefix')  # 匹配类型：prefix或suffix
    direction = data.get('direction', 'yo_to_ja')  # 搜索方向
    language = data.get('language', 'ja')  # 界面语言
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    
    if search_type == 'headword':
        # 见出语搜索
        if direction == 'yo_to_ja':
            # 与那国语到其他语言
            if match_type == 'prefix':
                # 前方一致
                cursor.execute('''
                    SELECT DISTINCT e.id, e.headword, e.kana, e.pos,
                           m.definition
                    FROM entries e
                    LEFT JOIN meanings m ON e.id = m.entry_id
                    WHERE (e.headword LIKE ? OR e.kana LIKE ?)
                    AND m.language = ?
                    AND m.meaning_number = 1
                    ORDER BY e.headword
                    LIMIT 50
                ''', (query + '%', query + '%', language))
            else:
                # 后方一致
                cursor.execute('''
                    SELECT DISTINCT e.id, e.headword, e.kana, e.pos,
                           m.definition
                    FROM entries e
                    LEFT JOIN meanings m ON e.id = m.entry_id
                    WHERE (e.headword LIKE ? OR e.kana LIKE ?)
                    AND m.language = ?
                    AND m.meaning_number = 1
                    ORDER BY e.headword
                    LIMIT 50
                ''', ('%' + query, '%' + query, language))
        else:
            # 其他语言到与那国语
            if match_type == 'prefix':
                cursor.execute('''
                    SELECT DISTINCT e.id, e.headword, e.kana, e.pos,
                           m.definition
                    FROM entries e
                    JOIN meanings m ON e.id = m.entry_id
                    WHERE m.definition LIKE ?
                    AND m.language = ?
                    ORDER BY e.headword
                    LIMIT 50
                ''', (query + '%', language))
            else:
                cursor.execute('''
                    SELECT DISTINCT e.id, e.headword, e.kana, e.pos,
                           m.definition
                    FROM entries e
                    JOIN meanings m ON e.id = m.entry_id
                    WHERE m.definition LIKE ?
                    AND m.language = ?
                    ORDER BY e.headword
                    LIMIT 50
                ''', ('%' + query, language))
    
    else:
        # 全文搜索（包括例句）
        cursor.execute('''
            SELECT DISTINCT e.id, e.headword, e.kana, e.pos,
                   m.definition, ex.yonaguni_sentence
            FROM entries e
            LEFT JOIN meanings m ON e.id = m.entry_id
            LEFT JOIN examples ex ON e.id = ex.entry_id
            LEFT JOIN example_translations et ON ex.id = et.example_id
            WHERE (e.headword LIKE ? OR e.kana LIKE ? 
                   OR ex.yonaguni_sentence LIKE ?
                   OR et.free_translation LIKE ?)
            AND m.language = ?
            AND m.meaning_number = 1
            ORDER BY e.headword
            LIMIT 50
        ''', ('%' + query + '%', '%' + query + '%', 
             '%' + query + '%', '%' + query + '%', language))
    
    # 格式化搜索结果
    for row in cursor.fetchall():
        results.append({
            'id': row['id'],
            'headword': row['headword'],
            'kana': row['kana'],
            'pos': row['pos'],
            'definition': row['definition']
        })
    
    conn.close()
    return jsonify({'results': results})

@app.route('/api/entry/<int:entry_id>')
def get_entry(entry_id):
    """
    获取单个词条的详细信息
    参数：entry_id - 词条ID
    返回：包含词条所有信息的JSON对象
    """
    language = request.args.get('language', 'ja')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取词条基本信息
    cursor.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        conn.close()
        return jsonify({'error': 'Entry not found'}), 404
    
    # 构建响应数据
    result = {
        'id': entry['id'],
        'headword': entry['headword'],
        'kana': entry['kana'],
        'ipa': entry['ipa'],
        'pos': entry['pos'],
        'verb_class': entry['verb_class'],
        'tone': entry['tone'],
        'etymology': entry['etymology'],
        'historical_change': entry['historical_change']
    }
    
    # 获取词义（支持多义词）
    cursor.execute('''
        SELECT meaning_number, definition 
        FROM meanings 
        WHERE entry_id = ? AND language = ?
        ORDER BY meaning_number
    ''', (entry_id, language))
    result['meanings'] = [{'number': row['meaning_number'], 
                          'definition': row['definition']} 
                         for row in cursor.fetchall()]
    
    # 获取同义词
    cursor.execute('SELECT synonym FROM synonyms WHERE entry_id = ?', (entry_id,))
    result['synonyms'] = [row['synonym'] for row in cursor.fetchall()]
    
    # 获取动词活用（如果是动词）
    if entry['pos'] == '動詞':
        cursor.execute('''
            SELECT form_name, conjugated_form 
            FROM conjugations 
            WHERE entry_id = ?
        ''', (entry_id,))
        result['conjugations'] = [{'form': row['form_name'], 
                                  'conjugated': row['conjugated_form']} 
                                 for row in cursor.fetchall()]
    
    # 获取例句和翻译
    cursor.execute('''
        SELECT ex.id, ex.yonaguni_sentence,
               et.word_by_word, et.free_translation
        FROM examples ex
        LEFT JOIN example_translations et ON ex.id = et.example_id
        WHERE ex.entry_id = ? AND et.language = ?
    ''', (entry_id, language))
    
    examples = []
    for row in cursor.fetchall():
        examples.append({
            'yonaguni': row['yonaguni_sentence'],
            'word_by_word': row['word_by_word'],
            'translation': row['free_translation']
        })
    result['examples'] = examples
    
    conn.close()
    return jsonify(result)

@app.route('/api/add-entry', methods=['POST'])
def add_entry():
    """
    添加新词条
    接收JSON格式的词条数据，插入数据库
    """
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 开始事务
        conn.execute('BEGIN')
        
        # 插入词条基本信息
        cursor.execute('''
            INSERT INTO entries 
            (headword, kana, ipa, pos, verb_class, tone, etymology, historical_change)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['headword'],
            data.get('kana'),
            data.get('ipa'),
            data.get('pos'),
            data.get('verb_class'),
            data.get('tone'),
            data.get('etymology'),
            data.get('historical_change')
        ))
        
        entry_id = cursor.lastrowid
        
        # 插入词义（支持多语言）
        for lang_code, meanings in data.get('meanings', {}).items():
            for i, meaning in enumerate(meanings, 1):
                cursor.execute('''
                    INSERT INTO meanings 
                    (entry_id, language, meaning_number, definition)
                    VALUES (?, ?, ?, ?)
                ''', (entry_id, lang_code, i, meaning))
        
        # 插入同义词
        for synonym in data.get('synonyms', []):
            cursor.execute('''
                INSERT INTO synonyms (entry_id, synonym)
                VALUES (?, ?)
            ''', (entry_id, synonym))
        
        # 插入动词活用
        for conjugation in data.get('conjugations', []):
            cursor.execute('''
                INSERT INTO conjugations 
                (entry_id, form_name, conjugated_form)
                VALUES (?, ?, ?)
            ''', (entry_id, conjugation['form'], conjugation['conjugated']))
        
        # 插入例句
        for example in data.get('examples', []):
            cursor.execute('''
                INSERT INTO examples (entry_id, yonaguni_sentence)
                VALUES (?, ?)
            ''', (entry_id, example['yonaguni']))
            
            example_id = cursor.lastrowid
            
            # 插入例句翻译
            for lang_code, translation in example.get('translations', {}).items():
                cursor.execute('''
                    INSERT INTO example_translations 
                    (example_id, language, word_by_word, free_translation)
                    VALUES (?, ?, ?, ?)
                ''', (example_id, lang_code, 
                      translation.get('word_by_word'), 
                      translation.get('free_translation')))
        
        # 提交事务
        conn.commit()
        
        return jsonify({'success': True, 'entry_id': entry_id})
        
    except Exception as e:
        # 发生错误时回滚
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    
    finally:
        conn.close()

# 主程序入口
if __name__ == '__main__':
    # 初始化数据库（第一次运行时）
    # init_db()  # 首次运行时取消注释
    
    # 启动Flask开发服务器
    # debug=True 开启调试模式，代码修改后自动重启
    # port=5000 设置端口号
    app.run(debug=True, port=5000)