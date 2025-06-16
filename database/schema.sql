-- 与那国语词典数据库设计
-- 这个SQL文件用于创建数据库表结构

-- 1. 词条主表
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 自动递增的主键
    headword TEXT NOT NULL,                -- 见出语（与那国语原文）
    kana TEXT,                             -- 假名表记
    ipa TEXT,                              -- IPA（罗马字）表记
    pos TEXT,                              -- 品词（名词、动词等）
    verb_class TEXT,                       -- 动词类别（仅动词需要）
    tone TEXT,                             -- 音调
    etymology TEXT,                        -- 语源
    historical_change TEXT,                -- 历史音变
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 词义表（支持多语言和多义词）
CREATE TABLE IF NOT EXISTS meanings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,             -- 关联到entries表
    language TEXT NOT NULL,                -- 语言代码：ja, zh-tw, en
    meaning_number INTEGER DEFAULT 1,      -- 义项编号（支持多义词）
    definition TEXT NOT NULL,              -- 词义解释
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

-- 3. 同义词表
CREATE TABLE IF NOT EXISTS synonyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    synonym TEXT NOT NULL,                 -- 同义词
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

-- 4. 动词活用表
CREATE TABLE IF NOT EXISTS conjugations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    form_name TEXT NOT NULL,               -- 活用形式名称（如：过去式、否定式等）
    conjugated_form TEXT NOT NULL,         -- 活用后的形式
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

-- 5. 例句表
CREATE TABLE IF NOT EXISTS examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    yonaguni_sentence TEXT NOT NULL,       -- 与那国语例句
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

-- 6. 例句翻译表（支持多语言）
CREATE TABLE IF NOT EXISTS example_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    example_id INTEGER NOT NULL,
    language TEXT NOT NULL,                -- 语言代码
    word_by_word TEXT,                     -- 逐语译
    free_translation TEXT,                 -- 意译
    FOREIGN KEY (example_id) REFERENCES examples(id) ON DELETE CASCADE
);

-- 7. 界面翻译表（用于存储UI文本的多语言版本）
CREATE TABLE IF NOT EXISTS ui_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,                     -- 翻译键（如：dict_name, search_button等）
    language TEXT NOT NULL,                -- 语言代码
    translation TEXT NOT NULL,             -- 翻译文本
    UNIQUE(key, language)                  -- 确保每个键+语言组合唯一
);

-- 创建索引以提高查询性能
CREATE INDEX idx_entries_headword ON entries(headword);
CREATE INDEX idx_entries_kana ON entries(kana);
CREATE INDEX idx_meanings_entry_id ON meanings(entry_id);
CREATE INDEX idx_meanings_language ON meanings(language);
CREATE INDEX idx_examples_entry_id ON examples(entry_id);

-- 插入UI翻译示例数据
INSERT INTO ui_translations (key, language, translation) VALUES
-- 词典名称
('dict_name', 'ja', '与那国語辞典'),
('dict_name', 'yonaguni', 'どぅなんむぬい辞典'),
('dict_name', 'zh-tw', '與那國語詞典'),
('dict_name', 'en', 'Yonaguni Dictionary'),
-- 导航菜单
('nav_home', 'ja', 'ホーム'),
('nav_about_language', 'ja', '与那国語について'),
('nav_grammar', 'ja', '文法'),
('nav_dialect_materials', 'ja', '方言資料'),
('nav_about_dict', 'ja', 'この辞典について'),
-- 搜索选项
('search_direction_ja_to_yo', 'ja', '日本語→与那国語'),
('search_direction_yo_to_ja', 'ja', '与那国語→日本語'),
('search_button', 'ja', '検索'),
('search_type_headword', 'ja', '見出し語のみ'),
('search_type_fulltext', 'ja', '例文全文検索'),
('match_type_prefix', 'ja', '前方一致'),
('match_type_suffix', 'ja', '後方一致'),
-- 开发中提示
('under_development', 'ja', '開発中'),
-- 词条详情页标签
('label_kana', 'ja', 'かな表記'),
('label_ipa', 'ja', 'IPA表記'),
('label_pos', 'ja', '品詞'),
('label_verb_class', 'ja', '動詞クラス'),
('label_tone', 'ja', '音調'),
('label_meaning', 'ja', '意味'),
('label_synonyms', 'ja', '同義語'),
('label_conjugation', 'ja', '活用形'),
('label_etymology', 'ja', '語源'),
('label_historical_change', 'ja', '歴史的音変化'),
('label_examples', 'ja', '例文'),
('label_word_by_word', 'ja', '逐語訳'),
('label_free_translation', 'ja', '意訳');

-- 插入测试词条数据
INSERT INTO entries (headword, kana, ipa, pos, tone, etymology) VALUES
('どぅなん', 'どぅなん', 'dunan', '名詞', '平板型', '与那国の古称'),
('あがる', 'あがる', 'agaru', '動詞', '上昇型', '日本語「上がる」から');

-- 插入词义
INSERT INTO meanings (entry_id, language, meaning_number, definition) VALUES
(1, 'ja', 1, '与那国島'),
(1, 'zh-tw', 1, '與那國島'),
(1, 'en', 1, 'Yonaguni Island'),
(2, 'ja', 1, '上がる、登る'),
(2, 'ja', 2, '（太陽が）昇る');

-- 插入例句
INSERT INTO examples (entry_id, yonaguni_sentence) VALUES
(1, 'どぅなんぬ　くとぅば'),
(2, 'てぃだぬ　あがたん');

-- 插入例句翻译
INSERT INTO example_translations (example_id, language, word_by_word, free_translation) VALUES
(1, 'ja', '与那国-の　言葉', '与那国の言葉'),
(2, 'ja', '太陽-が　上がった', '太陽が昇った');