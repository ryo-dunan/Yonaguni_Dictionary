# app.py - 与那国語辞典バックエンド主プログラム
# このファイルはWebアプリケーションの核心で、すべてのHTTPリクエストとデータベース操作を処理する

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # クロスドメインリクエストを処理
import sqlite3
import json
from datetime import datetime

# Flaskアプリケーションインスタンスを作成
app = Flask(__name__)
# CORSを有効化し、フロントエンドのクロスドメインアクセスを許可
CORS(app)

# データベースファイルパス
DATABASE = 'database/yonaguni_dict.db'

def get_db_connection():
    """
    データベース接続を作成して返す
    データベースにアクセスする必要があるたびにこの関数を呼び出す
    """
    conn = sqlite3.connect(DATABASE)
    # row_factoryを設定し、クエリ結果を辞書のようにアクセスできるようにする
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    データベースを初期化
    SQLファイルを読み込んで実行し、必要なテーブルをすべて作成
    """
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    conn = get_db_connection()
    conn.executescript(sql_script)
    conn.commit()
    conn.close()
    print("データベース初期化完了！")

@app.route('/')
def index():
    """
    メインページルート
    メインHTMLページを返す
    """
    return render_template('index.html')

@app.route('/admin')
def admin():
    """
    管理ページルート
    管理用HTMLページを返す
    """
    return render_template('admin.html')

@app.route('/api/ui-translations/<language>')
def get_ui_translations(language):
    """
    指定言語のUI翻訳を取得
    パラメータ：language - 言語コード（ja, zh-tw, en, yonaguni）
    戻り値：JSON形式の翻訳キーと値のペア
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 指定言語のすべてのUI翻訳をクエリ
    cursor.execute('''
        SELECT key, translation 
        FROM ui_translations 
        WHERE language = ?
    ''', (language,))
    
    # 結果を辞書形式に変換
    translations = {}
    for row in cursor.fetchall():
        translations[row['key']] = row['translation']
    
    conn.close()
    return jsonify(translations)

@app.route('/api/search', methods=['POST'])
def search():
    """
    検索APIエンドポイント
    検索パラメータを受け取り、マッチする見出し語リストを返す
    """
    # リクエストパラメータを取得
    data = request.json
    query = data.get('query', '')  # 検索キーワード
    search_type = data.get('search_type', 'headword')  # 検索タイプ：headword、fulltext、conjugation
    match_type = data.get('match_type', 'prefix')  # マッチタイプ：prefix または suffix
    direction = data.get('direction', 'yo_to_ja')  # 検索方向
    language = data.get('language', 'ja')  # インターフェース言語
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    
    # インターフェース言語に基づいて検索結果言語を調整
    # インターフェースが与那国語の場合、日本語の釈義を優先表示
    result_language = 'ja' if language == 'yonaguni' else language
    
    if search_type == 'headword':
        # 見出し語検索
        if direction == 'yo_to_ja':
            # 与那国語から他言語へ
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
                ''', (query + '%', query + '%', result_language))
            else:
                # 後方一致
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
                ''', ('%' + query, '%' + query, result_language))
        else:
            # 他言語から与那国語へ
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
                ''', (query + '%', result_language))
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
                ''', ('%' + query, result_language))
    
    elif search_type == 'conjugation':
        # 動詞活用形検索
        if match_type == 'prefix':
            cursor.execute('''
                SELECT DISTINCT e.id, e.headword, e.kana, e.pos,
                       m.definition, c.form_name, c.conjugated_form
                FROM entries e
                JOIN conjugations c ON e.id = c.entry_id
                LEFT JOIN meanings m ON e.id = m.entry_id
                WHERE c.conjugated_form LIKE ?
                AND m.language = ?
                AND m.meaning_number = 1
                ORDER BY e.headword
                LIMIT 50
            ''', (query + '%', result_language))
        else:
            cursor.execute('''
                SELECT DISTINCT e.id, e.headword, e.kana, e.pos,
                       m.definition, c.form_name, c.conjugated_form
                FROM entries e
                JOIN conjugations c ON e.id = c.entry_id
                LEFT JOIN meanings m ON e.id = m.entry_id
                WHERE c.conjugated_form LIKE ?
                AND m.language = ?
                AND m.meaning_number = 1
                ORDER BY e.headword
                LIMIT 50
            ''', ('%' + query, result_language))
    
    else:
        # 全文検索（例文を含む）
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
             '%' + query + '%', '%' + query + '%', result_language))
    
    # 検索結果をフォーマット
    seen_ids = set()  # 重複除去用
    for row in cursor.fetchall():
        if row['id'] not in seen_ids:
            seen_ids.add(row['id'])
            result_item = {
                'id': row['id'],
                'headword': row['headword'],
                'kana': row['kana'],
                'pos': row['pos'],
                'definition': row['definition']
            }
            # 活用形検索の場合、マッチした活用形も含める
            if search_type == 'conjugation' and 'conjugated_form' in row.keys():
                result_item['matched_form'] = row['conjugated_form']
                result_item['form_name'] = row['form_name']
            results.append(result_item)
    
    conn.close()
    return jsonify({'results': results})

@app.route('/api/entry/<int:entry_id>')
def get_entry(entry_id):
    """
    単一の見出し語の詳細情報を取得
    パラメータ：entry_id - 見出し語ID
    戻り値：見出し語のすべての情報を含むJSONオブジェクト
    """
    language = request.args.get('language', 'ja')
    # インターフェース言語が与那国語の場合、日本語で釈義を表示
    display_language = 'ja' if language == 'yonaguni' else language
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 見出し語の基本情報を取得
    cursor.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        conn.close()
        return jsonify({'error': 'Entry not found'}), 404
    
    # レスポンスデータを構築
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
    
    # 意味を取得（多義語対応）
    cursor.execute('''
        SELECT meaning_number, definition 
        FROM meanings 
        WHERE entry_id = ? AND language = ?
        ORDER BY meaning_number
    ''', (entry_id, display_language))
    result['meanings'] = [{'number': row['meaning_number'], 
                          'definition': row['definition']} 
                         for row in cursor.fetchall()]
    
    # 同義語を取得
    cursor.execute('SELECT synonym FROM synonyms WHERE entry_id = ?', (entry_id,))
    result['synonyms'] = [row['synonym'] for row in cursor.fetchall()]
    
    # 動詞活用を取得（動詞の場合）
    if entry['pos'] == '動詞':
        cursor.execute('''
            SELECT form_name, conjugated_form 
            FROM conjugations 
            WHERE entry_id = ?
        ''', (entry_id,))
        result['conjugations'] = [{'form': row['form_name'], 
                                  'conjugated': row['conjugated_form']} 
                                 for row in cursor.fetchall()]
    
    # 例文と翻訳を取得
    cursor.execute('''
        SELECT ex.id, ex.yonaguni_sentence,
               et.word_by_word, et.free_translation
        FROM examples ex
        LEFT JOIN example_translations et ON ex.id = et.example_id
        WHERE ex.entry_id = ? AND et.language = ?
    ''', (entry_id, display_language))
    
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

@app.route('/api/entries')
def get_all_entries():
    """
    すべての見出し語を取得（管理ページ用）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.id, e.headword, e.kana, e.pos,
               GROUP_CONCAT(m.definition, '、') as definitions
        FROM entries e
        LEFT JOIN meanings m ON e.id = m.entry_id
        WHERE m.language = 'ja' AND m.meaning_number = 1
        GROUP BY e.id
        ORDER BY e.headword
    ''')
    
    entries = []
    for row in cursor.fetchall():
        entries.append({
            'id': row['id'],
            'headword': row['headword'],
            'kana': row['kana'],
            'pos': row['pos'],
            'definition': row['definitions']
        })
    
    conn.close()
    return jsonify({'entries': entries})

@app.route('/api/add-entry', methods=['POST'])
def add_entry():
    """
    新しい見出し語を追加
    JSON形式の見出し語データを受け取り、データベースに挿入
    """
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # トランザクション開始
        conn.execute('BEGIN')
        
        # 見出し語の基本情報を挿入
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
        
        # 意味を挿入（多言語対応）
        for lang_code, meanings in data.get('meanings', {}).items():
            for i, meaning in enumerate(meanings, 1):
                cursor.execute('''
                    INSERT INTO meanings 
                    (entry_id, language, meaning_number, definition)
                    VALUES (?, ?, ?, ?)
                ''', (entry_id, lang_code, i, meaning))
        
        # 同義語を挿入
        for synonym in data.get('synonyms', []):
            cursor.execute('''
                INSERT INTO synonyms (entry_id, synonym)
                VALUES (?, ?)
            ''', (entry_id, synonym))
        
        # 動詞活用を挿入
        for conjugation in data.get('conjugations', []):
            cursor.execute('''
                INSERT INTO conjugations 
                (entry_id, form_name, conjugated_form)
                VALUES (?, ?, ?)
            ''', (entry_id, conjugation['form'], conjugation['conjugated']))
        
        # 例文を挿入
        for example in data.get('examples', []):
            cursor.execute('''
                INSERT INTO examples (entry_id, yonaguni_sentence)
                VALUES (?, ?)
            ''', (entry_id, example['yonaguni']))
            
            example_id = cursor.lastrowid
            
            # 例文翻訳を挿入
            for lang_code, translation in example.get('translations', {}).items():
                cursor.execute('''
                    INSERT INTO example_translations 
                    (example_id, language, word_by_word, free_translation)
                    VALUES (?, ?, ?, ?)
                ''', (example_id, lang_code, 
                      translation.get('word_by_word'), 
                      translation.get('free_translation')))
        
        # トランザクションをコミット
        conn.commit()
        
        return jsonify({'success': True, 'entry_id': entry_id})
        
    except Exception as e:
        # エラー発生時はロールバック
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    
    finally:
        conn.close()

@app.route('/api/update-entry/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    """
    既存の見出し語を更新
    """
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # トランザクション開始
        conn.execute('BEGIN')
        
        # 見出し語の基本情報を更新
        cursor.execute('''
            UPDATE entries SET
                headword = ?, kana = ?, ipa = ?, pos = ?, 
                verb_class = ?, tone = ?, etymology = ?, historical_change = ?
            WHERE id = ?
        ''', (
            data['headword'],
            data.get('kana'),
            data.get('ipa'),
            data.get('pos'),
            data.get('verb_class'),
            data.get('tone'),
            data.get('etymology'),
            data.get('historical_change'),
            entry_id
        ))
        
        # 既存の関連データを削除
        cursor.execute('DELETE FROM meanings WHERE entry_id = ?', (entry_id,))
        cursor.execute('DELETE FROM synonyms WHERE entry_id = ?', (entry_id,))
        cursor.execute('DELETE FROM conjugations WHERE entry_id = ?', (entry_id,))
        cursor.execute('DELETE FROM examples WHERE entry_id = ?', (entry_id,))
        
        # 新しいデータを挿入
        # 意味
        for lang_code, meanings in data.get('meanings', {}).items():
            for i, meaning in enumerate(meanings, 1):
                cursor.execute('''
                    INSERT INTO meanings 
                    (entry_id, language, meaning_number, definition)
                    VALUES (?, ?, ?, ?)
                ''', (entry_id, lang_code, i, meaning))
        
        # 同義語
        for synonym in data.get('synonyms', []):
            cursor.execute('''
                INSERT INTO synonyms (entry_id, synonym)
                VALUES (?, ?)
            ''', (entry_id, synonym))
        
        # 動詞活用
        for conjugation in data.get('conjugations', []):
            cursor.execute('''
                INSERT INTO conjugations 
                (entry_id, form_name, conjugated_form)
                VALUES (?, ?, ?)
            ''', (entry_id, conjugation['form'], conjugation['conjugated']))
        
        # 例文
        for example in data.get('examples', []):
            cursor.execute('''
                INSERT INTO examples (entry_id, yonaguni_sentence)
                VALUES (?, ?)
            ''', (entry_id, example['yonaguni']))
            
            example_id = cursor.lastrowid
            
            # 例文翻訳
            for lang_code, translation in example.get('translations', {}).items():
                cursor.execute('''
                    INSERT INTO example_translations 
                    (example_id, language, word_by_word, free_translation)
                    VALUES (?, ?, ?, ?)
                ''', (example_id, lang_code, 
                      translation.get('word_by_word'), 
                      translation.get('free_translation')))
        
        # トランザクションをコミット
        conn.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        # エラー発生時はロールバック
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    
    finally:
        conn.close()

@app.route('/api/delete-entry/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """
    見出し語を削除
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # カスケード削除により関連データも自動的に削除される
        cursor.execute('DELETE FROM entries WHERE id = ?', (entry_id,))
        conn.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    
    finally:
        conn.close()

# メインプログラムエントリーポイント
if __name__ == '__main__':
    # データベースを初期化（初回実行時）
    # init_db()  # 初回実行時はコメントを外す
    
    # Flask開発サーバーを起動
    # debug=True デバッグモードを有効化、コード変更後に自動再起動
    # port=5000 ポート番号を設定
    app.run(debug=True, port=5000)