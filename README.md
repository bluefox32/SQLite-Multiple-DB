# SQLite複数DB圧縮管理システム / Multi-DB Compression Manager

P2P分散型コンパイラとの統合を想定した、**軽量仮想化レイヤー** を実装したSQLiteDB管理フレームワーク。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)

---

## 特徴 Features

### 🎯 コア機能

- **複数DB管理**: 1つのmaster.dbで複数の圧縮済みDB群を統一管理
- **zlib圧縮**: 96-97%の圧縮率で大幅なストレージ削減
- **整合性検証**: SHA256チェックサムでDB改ざん検知（すり替え対策）
- **メモリ仮想化**: 圧縮DB → インメモリ展開 → 再圧縮のライフサイクル
- **コンテキストマネージャ**: `with`文でリソース安全に管理
- **監査ログ**: 全アクセス・操作をmasterDBに記録

### 🔒 セキュリティ

| チェック項目 | 実装状況 |
|------------|--------|
| Checksum Verification | ✅ SHA256 |
| File Integrity Check | ✅ すり替え検知 |
| Exception Handling | ✅ 4/4パス |
| Transaction Safety | ✅ バックアップ対応 |
| Resource Cleanup | ✅ 11ポイント |

### ⚡ パフォーマンス

```
圧縮率          : 96.8% - 97.1%
展開時間        : < 100ms（典型）
メモリオーバーヘッド : 最小限
並列処理対応    : 可能（拡張用）
```

### 🏗️ アーキテクチャ

```
┌─────────────────────────────────┐
│   アプリケーション層             │
│  (db_manager.py)                │
└──────────────┬──────────────────┘
               │
        ┌──────▼──────┐
        │ master.db   │  ← 中央管理・メタデータ
        └──────┬──────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│users  │ │ product│ │ logs  │
│.db.z  │ │.db.z  │ │.db.z  │
└───────┘ └───────┘ └───────┘
圧縮済みDB群
    │
    └──► メモリ展開（仮想マウント）
         ↓
         高速処理
         ↓
         再圧縮保存
```

---

## インストール Installation

### 必要環境

- Python 3.7+
- sqlite3（標準搭載）
- zlib（標準搭載）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/sqlite-compression-manager.git
cd sqlite-compression-manager

# 依存パッケージをインストール（実はほぼ不要）
pip install -r requirements.txt

# または、setup.pyで
python setup.py install
```

### Pyto環境（iOS）

```python
# db_manager.pyをiCloudドライブに配置
exec(open('db_manager.py', encoding='utf-8').read()); demo()
```

---

## 使い方 Usage

### 基本的な使用例

```python
from db_manager import MasterDBManager

# masterDB初期化
with MasterDBManager('master.db') as manager:
    
    # Step 1: DBを登録・圧縮
    manager.register_db('users')
    manager.register_db('products')
    
    # Step 2: DBを開いて使用（with文で自動保存）
    with manager.use_db('users') as db:
        # テーブル作成
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        ''')
        
        # データ挿入（プリペアドステートメント）
        db.execute(
            'INSERT INTO users (name, email) VALUES (?, ?)',
            ('田中太郎', 'tanaka@example.com')
        )
        db.commit()
    
    # Step 3: データ確認（自動的に展開される）
    with manager.use_db('users') as db:
        rows = db.execute('SELECT * FROM users').fetchall()
        for row in rows:
            print(row['name'], row['email'])
    
    # Step 4: 整合性検証（改ざん検知）
    manager.verify_all()
    
    # Step 5: DB一覧・ログ確認
    manager.list_dbs()
    manager.show_logs(limit=20)
```

### 詳細API

#### `MasterDBManager.__init__()`
```python
manager = MasterDBManager(
    master_path='master.db',  # masterDBのパス
    work_dir=None             # 作業ディレクトリ（省略時は同じ場所）
)
```

#### `manager.register_db()`
```python
# 新規DB作成
manager.register_db('users')

# 既存DBを登録・圧縮
manager.register_db('legacy_data', source_path='./old_data.db')
```

#### `manager.use_db()` - with文対応
```python
with manager.use_db('users') as db:
    db.execute("INSERT INTO ...")
    db.commit()
# ← ここで自動的にsave_db()が呼ばれる
```

#### `manager.verify_all()`
```python
# 全DBの整合性検証（改ざん検知）
is_valid = manager.verify_all()
```

#### `manager.list_dbs()`
```python
# 登録済みDB一覧と統計
dbs = manager.list_dbs()
```

#### `manager.show_logs()`
```python
# アクセスログ表示
manager.show_logs(db_name='users', limit=50)
```

---

## コンパイラ統合 Compiler Integration

### 中間表現（IR）の生成

```python
from db_manager_compiler_ir import CompilerIR

compiler = CompilerIR('db_manager.py')
ir = compiler.generate_ir_json()

# JSON形式でコンパイラに渡す
import json
with open('db_manager_ir.json', 'w') as f:
    json.dump(ir, f)
```

### 検証ルール

| Rule ID | 名前 | 重要度 | 説明 |
|---------|------|--------|------|
| rule_001 | Checksum Must Verify | CRITICAL | SHA256検証が常に実行される |
| rule_002 | File Handle Close | HIGH | ファイルハンドルは必ずクローズ |
| rule_003 | Exception Complete | HIGH | 例外処理が完全 |
| rule_004 | Memory Safety | CRITICAL | メモリリーク防止 |
| rule_005 | Transaction Atomic | HIGH | 原子性保証 |
| rule_006 | SQL Injection Free | CRITICAL | SQLi対策済み |

### コンパイラ検証チェックリスト

```
[ ] rule_001: Checksum Must Always Verify (CRITICAL)
[ ] rule_002: File Handle Always Close (HIGH)
[ ] rule_003: Exception Handling Complete (HIGH)
[ ] rule_004: No Memory Leak on Compression (CRITICAL)
[ ] rule_005: Transaction Atomicity (HIGH)
[ ] rule_006: No SQL Injection (CRITICAL)
```

---

## パフォーマンス最適化 Optimization

### すでに実装されている最適化

- ✅ zlib level 9（高圧縮率）
- ✅ メモリバックアップ（高速コピー）
- ✅ インデックス利用（DB検索高速化）

### 将来の最適化案

| 案 | 期待効果 | 難度 |
|----|---------|------|
| マルチスレッド圧縮 | 30-40% | 中 |
| 差分バックアップ | 50-70% | 高 |
| 遅延展開（Lazy Decompression） | 20-30% | 中 |

---

## テスト Tests

```bash
# デモ実行
python db_manager.py

# ユニットテスト
python -m pytest tests/

# カバレッジ確認
python -m pytest --cov=db_manager tests/
```

### テストスイート

```
tests/
├── test_basic_operations.py      # 基本機能テスト
├── test_compression.py           # 圧縮・展開テスト
├── test_security.py              # セキュリティテスト
├── test_integrity_check.py       # 整合性検証テスト
└── test_concurrent.py            # 並行処理テスト
```

---

## セキュリティ Security

### 実装済みセキュリティ対策

1. **改ざん検知**
   - SHA256チェックサムで全DBを保護
   - 起動時に自動検証

2. **例外処理**
   - ファイルI/O時の確実なリソース解放
   - コンテキストマネージャでリソース安全性確保

3. **SQL インジェクション対策**
   - プリペアドステートメントのみ使用推奨
   - パラメータ化クエリの統一

4. **トランザクション安全性**
   - メモリDB ← → ファイルDB のバックアップで実現
   - エラー時は自動ロールバック

### セキュリティアドバイス

⚠️ **重要**:
- 本番環境ではmaster.dbのファイルパーミッションを`600`に設定してください
- 暗号化が必要な場合は`SQLCipher`の使用を検討してください
- アクセスログは定期的にバックアップしてください

---

## ライセンス License

MIT License - 詳細は [LICENSE](LICENSE) を参照

---

## 貢献 Contributing

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

```bash
# 開発環境セットアップ
git clone <repo>
cd sqlite-compression-manager
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# テスト実行
pytest tests/

# コード整形
black db_manager.py
```

---

## 関連リンク Links

- 📖 [詳細ドキュメント](docs/)
- 🔧 [API リファレンス](docs/api_reference.md)
- 💡 [使用例集](examples/)
- 🐛 [Issue Tracker](https://github.com/yourusername/sqlite-compression-manager/issues)

---

## 著者 Author

SQLite Compression Manager Team

**バージョン**: 1.0.0  
**最終更新**: 2026-06-08  
**ステータス**: Production Ready ✅
