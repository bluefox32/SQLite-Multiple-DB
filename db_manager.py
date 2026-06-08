# -*- coding: utf-8 -*-
"""
db_manager.py
=============
Pyto（iOS Python環境）対応
SQLite複数DB 圧縮・仮想化管理システム

使い方:
    from db_manager import MasterDBManager
    manager = MasterDBManager()
"""

import sqlite3
import zlib
import hashlib
import os
import json
from datetime import datetime


# ============================================================
# カスタム例外
# ============================================================

class SecurityError(Exception):
    """改ざん・すり替え検知時の例外"""
    pass

class DBNotFoundError(Exception):
    """DB未登録時の例外"""
    pass


# ============================================================
# MasterDBManager：DB群を管理する中心クラス
# ============================================================

class MasterDBManager:
    """
    複数のSQLiteDBを圧縮・管理する仮想化レイヤー

    アーキテクチャ：
        master.db（メタ情報管理）
              |
        各DB群（圧縮済み .db.z ファイル）
              |
        必要時にメモリ展開して使用
    """

    def __init__(self, master_path='master.db', work_dir=None):
        """
        Args:
            master_path: masterDBのパス
            work_dir: 圧縮DBを保存するディレクトリ（省略時はmaster.dbと同じ場所）
        """
        # Pyto環境ではカレントディレクトリを明示的に指定
        if work_dir is None:
            self.work_dir = os.path.dirname(os.path.abspath(master_path))
        else:
            self.work_dir = work_dir

        self.master_path = os.path.join(self.work_dir, master_path)
        self.master = sqlite3.connect(self.master_path)
        self.master.row_factory = sqlite3.Row  # 辞書形式でアクセス可能に
        self._init_master()

    def _init_master(self):
        """masterDBの初期化（管理テーブル作成）"""
        self.master.executescript('''
            CREATE TABLE IF NOT EXISTS db_registry (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                db_name         TEXT UNIQUE NOT NULL,
                compressed_path TEXT NOT NULL,
                checksum        TEXT NOT NULL,
                original_size   INTEGER,
                compressed_size INTEGER,
                compression     TEXT DEFAULT 'zlib',
                created_at      TEXT,
                updated_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS access_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                db_name     TEXT NOT NULL,
                operation   TEXT NOT NULL,
                status      TEXT NOT NULL,
                message     TEXT,
                accessed_at TEXT
            );
        ''')
        self.master.commit()

    # ----------------------------------------------------------
    # ログ記録
    # ----------------------------------------------------------

    def _log(self, db_name, operation, status, message=''):
        """アクセスログをmasterDBに記録"""
        self.master.execute(
            '''INSERT INTO access_log (db_name, operation, status, message, accessed_at)
               VALUES (?, ?, ?, ?, ?)''',
            (db_name, operation, status, message, datetime.now().isoformat())
        )
        self.master.commit()

    # ----------------------------------------------------------
    # DB登録・圧縮
    # ----------------------------------------------------------

    def register_db(self, db_name, source_path=None):
        """
        新規DBを作成または既存DBを登録・圧縮する

        Args:
            db_name: DB識別名（例: 'users', 'products'）
            source_path: 既存DBファイルのパス（省略時は新規作成）

        Returns:
            compressed_path: 圧縮ファイルのパス
        """
        try:
            if source_path and os.path.exists(source_path):
                # 既存DBを圧縮登録
                with open(source_path, 'rb') as f:
                    raw_data = f.read()
            else:
                # 新規空DBをファイルとして作成してから読み込む
                temp_path = os.path.join(self.work_dir, f'_temp_{db_name}.db')
                temp_conn = sqlite3.connect(temp_path)
                temp_conn.close()
                with open(temp_path, 'rb') as f:
                    raw_data = f.read()
                os.remove(temp_path)

            # 圧縮処理
            compressed = zlib.compress(raw_data, level=9)

            # チェックサム生成（整合性検証用）
            checksum = hashlib.sha256(raw_data).hexdigest()

            # 圧縮ファイル保存
            compressed_path = os.path.join(self.work_dir, f'{db_name}.db.z')
            with open(compressed_path, 'wb') as f:
                f.write(compressed)

            # masterDBに登録
            now = datetime.now().isoformat()
            self.master.execute(
                '''INSERT OR REPLACE INTO db_registry
                   (db_name, compressed_path, checksum, original_size,
                    compressed_size, compression, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (db_name, compressed_path, checksum,
                 len(raw_data), len(compressed), 'zlib', now, now)
            )
            self.master.commit()

            ratio = (1 - len(compressed) / max(len(raw_data), 1)) * 100
            self._log(db_name, 'register', 'ok',
                      f'圧縮率: {ratio:.1f}% ({len(raw_data)}->{len(compressed)} bytes)')

            print(f"[OK] [{db_name}] 登録完了 圧縮率: {ratio:.1f}%")
            return compressed_path

        except Exception as e:
            self._log(db_name, 'register', 'error', str(e))
            raise

    # ----------------------------------------------------------
    # DB展開・使用
    # ----------------------------------------------------------

    def open_db(self, db_name):
        """
        圧縮DBをメモリ上に展開して接続を返す
        *使用後は必ず save_db() を呼ぶこと

        Args:
            db_name: DB識別名

        Returns:
            sqlite3.Connection（インメモリ）
        """
        try:
            row = self._get_registry(db_name)
            raw_data = self._decompress_and_verify(row)

            # メモリDB に展開（仮想マウント相当）
            mem_conn = sqlite3.connect(':memory:')
            mem_conn.row_factory = sqlite3.Row

            # バイナリデータをメモリDBに復元
            temp_path = os.path.join(self.work_dir, f'_mount_{db_name}.db')
            with open(temp_path, 'wb') as f:
                f.write(raw_data)

            # ファイルDBからメモリDBへコピー
            file_conn = sqlite3.connect(temp_path)
            file_conn.backup(mem_conn)
            file_conn.close()
            os.remove(temp_path)

            self._log(db_name, 'open', 'ok', 'メモリ展開成功')
            print(f"[OPEN] [{db_name}] メモリ展開完了")
            return mem_conn

        except SecurityError:
            self._log(db_name, 'open', 'security_error', '改ざん検知')
            raise
        except Exception as e:
            self._log(db_name, 'open', 'error', str(e))
            raise

    def save_db(self, db_name, mem_conn):
        """
        メモリDB の内容を圧縮して保存（仮想アンマウント相当）

        Args:
            db_name: DB識別名
            mem_conn: open_db()で取得したメモリ接続
        """
        try:
            # メモリDBをファイルに書き出し
            temp_path = os.path.join(self.work_dir, f'_save_{db_name}.db')
            file_conn = sqlite3.connect(temp_path)
            mem_conn.backup(file_conn)
            file_conn.close()

            # ファイルを読み込んで再圧縮
            with open(temp_path, 'rb') as f:
                raw_data = f.read()
            os.remove(temp_path)

            compressed = zlib.compress(raw_data, level=9)
            checksum = hashlib.sha256(raw_data).hexdigest()

            # 圧縮ファイル上書き
            compressed_path = os.path.join(self.work_dir, f'{db_name}.db.z')
            with open(compressed_path, 'wb') as f:
                f.write(compressed)

            # masterDB更新
            self.master.execute(
                '''UPDATE db_registry
                   SET checksum=?, original_size=?, compressed_size=?, updated_at=?
                   WHERE db_name=?''',
                (checksum, len(raw_data), len(compressed),
                 datetime.now().isoformat(), db_name)
            )
            self.master.commit()

            self._log(db_name, 'save', 'ok',
                      f'{len(raw_data)}->{len(compressed)} bytes')
            print(f"[SAVE] [{db_name}] 保存・圧縮完了")

        except Exception as e:
            self._log(db_name, 'save', 'error', str(e))
            raise

    # ----------------------------------------------------------
    # コンテキストマネージャ（with文対応）
    # ----------------------------------------------------------

    def use_db(self, db_name):
        """
        with文でDBを安全に使うためのコンテキストマネージャ

        使用例:
            with manager.use_db('users') as db:
                db.execute("INSERT INTO users VALUES (...)")
            # <- ここで自動的にsave_db()が呼ばれる
        """
        return _DBContext(self, db_name)

    # ----------------------------------------------------------
    # DB一覧・情報
    # ----------------------------------------------------------

    def list_dbs(self):
        """登録済みDB一覧を表示"""
        rows = self.master.execute(
            'SELECT * FROM db_registry ORDER BY created_at'
        ).fetchall()

        if not rows:
            print("登録済みDBはありません")
            return []

        print("\n[LIST] 登録済みDB一覧")
        print("-" * 60)
        result = []
        for row in rows:
            ratio = (1 - row['compressed_size'] / max(row['original_size'], 1)) * 100
            print(f"  [{row['db_name']}]")
            print(f"    圧縮率    : {ratio:.1f}%")
            print(f"    元サイズ  : {row['original_size']} bytes")
            print(f"    圧縮サイズ: {row['compressed_size']} bytes")
            print(f"    更新日時  : {row['updated_at']}")
            print()
            result.append(dict(row))
        return result

    def show_logs(self, db_name=None, limit=20):
        """アクセスログを表示"""
        if db_name:
            rows = self.master.execute(
                '''SELECT * FROM access_log WHERE db_name=?
                   ORDER BY accessed_at DESC LIMIT ?''',
                (db_name, limit)
            ).fetchall()
        else:
            rows = self.master.execute(
                'SELECT * FROM access_log ORDER BY accessed_at DESC LIMIT ?',
                (limit,)
            ).fetchall()

        print(f"\n[LOG] アクセスログ（最新{limit}件）")
        print("-" * 60)
        for row in rows:
            status_icon = '[OK]' if row['status'] == 'ok' else '[NG]'
            print(f"  {status_icon} {row['accessed_at'][:19]} "
                  f"[{row['db_name']}] {row['operation']} - {row['message']}")

    # ----------------------------------------------------------
    # 整合性チェック
    # ----------------------------------------------------------

    def verify_all(self):
        """全DBの整合性を検証（すり替え検知）"""
        rows = self.master.execute('SELECT * FROM db_registry').fetchall()
        print("\n[CHECK] 整合性検証開始")
        print("-" * 60)
        all_ok = True
        for row in rows:
            try:
                self._decompress_and_verify(row)
                print(f"  [OK] [{row['db_name']}] OK")
            except SecurityError as e:
                print(f"  [NG] [{row['db_name']}] 改ざん検知! {e}")
                all_ok = False
            except Exception as e:
                print(f"  [WARN]  [{row['db_name']}] エラー: {e}")
                all_ok = False

        print("-" * 60)
        print(f"  結果: {'全て正常 [OK]' if all_ok else '問題あり [NG]'}\n")
        return all_ok

    # ----------------------------------------------------------
    # 内部ヘルパー
    # ----------------------------------------------------------

    def _get_registry(self, db_name):
        """masterDBからDB情報を取得"""
        row = self.master.execute(
            'SELECT * FROM db_registry WHERE db_name=?', (db_name,)
        ).fetchone()
        if not row:
            raise DBNotFoundError(f"[{db_name}] はmasterDBに登録されていません")
        return row

    def _decompress_and_verify(self, row):
        """圧縮ファイルを展開してチェックサムで検証"""
        compressed_path = row['compressed_path']
        if not os.path.exists(compressed_path):
            raise FileNotFoundError(f"圧縮ファイルが見つかりません: {compressed_path}")

        with open(compressed_path, 'rb') as f:
            compressed = f.read()

        raw_data = zlib.decompress(compressed)

        # チェックサム検証（すり替え対策）
        current_checksum = hashlib.sha256(raw_data).hexdigest()
        if current_checksum != row['checksum']:
            raise SecurityError(
                f"チェックサム不一致!ファイルが改ざんされている可能性があります\n"
                f"  期待値: {row['checksum'][:16]}...\n"
                f"  現在値: {current_checksum[:16]}..."
            )
        return raw_data

    def close(self):
        """masterDB接続を閉じる"""
        self.master.close()
        print("[LOCK] masterDB クローズ")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================================
# コンテキストマネージャ補助クラス
# ============================================================

class _DBContext:
    """with文でDBを安全に使うための補助クラス"""

    def __init__(self, manager, db_name):
        self.manager = manager
        self.db_name = db_name
        self.conn = None

    def __enter__(self):
        self.conn = self.manager.open_db(self.db_name)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                # 正常終了時のみ保存
                self.manager.save_db(self.db_name, self.conn)
            else:
                print(f"[WARN]  [{self.db_name}] エラー発生のため保存をスキップ")
            self.conn.close()


# ============================================================
# 使用例・デモ
# ============================================================

def demo():
    """
    動作確認用デモ
    Pytoで実行: exec(open('db_manager.py').read()); demo()
    """
    print("=" * 60)
    print("  SQLite 複数DB 圧縮管理システム デモ")
    print("=" * 60)

    with MasterDBManager('master.db') as manager:

        # 1. DBを登録
        print("\n【ステップ1】DB登録")
        manager.register_db('users')
        manager.register_db('products')
        manager.register_db('logs')

        # 2. usersDBにデータ追加
        print("\n【ステップ2】usersDBにデータ追加")
        with manager.use_db('users') as db:
            db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    email TEXT
                )
            ''')
            db.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                       ('田中太郎', 'tanaka@example.com'))
            db.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                       ('山田花子', 'yamada@example.com'))
            db.commit()
        # <- ここで自動的に圧縮保存される

        # 3. productsDBにデータ追加
        print("\n【ステップ3】productsDBにデータ追加")
        with manager.use_db('products') as db:
            db.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    price INTEGER
                )
            ''')
            db.execute("INSERT INTO products (name, price) VALUES (?, ?)",
                       ('りんご', 150))
            db.execute("INSERT INTO products (name, price) VALUES (?, ?)",
                       ('みかん', 80))
            db.commit()

        # 4. データ読み込み確認
        print("\n【ステップ4】データ読み込み確認")
        with manager.use_db('users') as db:
            rows = db.execute("SELECT * FROM users").fetchall()
            print("  usersテーブル:")
            for row in rows:
                print(f"    ID:{row['id']} {row['name']} ({row['email']})")

        # 5. DB一覧表示
        print("\n【ステップ5】DB一覧")
        manager.list_dbs()

        # 6. 整合性検証
        print("\n【ステップ6】整合性検証（すり替え検知）")
        manager.verify_all()

        # 7. アクセスログ
        print("\n【ステップ7】アクセスログ")
        manager.show_logs(limit=10)

    print("=" * 60)
    print("  デモ完了")
    print("=" * 60)


# Pytoで直接実行した場合にデモを起動
if __name__ == '__main__':
    demo()
