# -*- coding: utf-8 -*-
"""
SQLite Compression Manager - Basic Usage Example
"""

from db_manager import MasterDBManager


def example_basic_operations():
    """基本的な使い方の例"""
    print("=" * 70)
    print("Example 1: Basic Operations")
    print("=" * 70)
    
    with MasterDBManager('example.db') as manager:
        # Step 1: DB登録
        print("\n[Step 1] DBを登録・圧縮")
        manager.register_db('users')
        manager.register_db('settings')
        
        # Step 2: データを追加
        print("\n[Step 2] usersテーブルにデータ追加")
        with manager.use_db('users') as db:
            db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TEXT
                )
            ''')
            
            # 複数のユーザーを追加
            users_data = [
                ('Alice', 'alice@example.com', '2026-01-01'),
                ('Bob', 'bob@example.com', '2026-01-02'),
                ('Charlie', 'charlie@example.com', '2026-01-03'),
            ]
            
            for name, email, created_at in users_data:
                db.execute(
                    'INSERT INTO users (name, email, created_at) VALUES (?, ?, ?)',
                    (name, email, created_at)
                )
            db.commit()
            print(f"  ✓ {len(users_data)} ユーザーを追加")
        
        # Step 3: データを読み取り
        print("\n[Step 3] データを読み取り")
        with manager.use_db('users') as db:
            rows = db.execute('SELECT * FROM users ORDER BY id').fetchall()
            for row in rows:
                print(f"  ID:{row['id']} {row['name']} ({row['email']})")
        
        # Step 4: DB統計
        print("\n[Step 4] DB統計")
        manager.list_dbs()


def example_multi_database():
    """複数DBを扱う例"""
    print("\n" + "=" * 70)
    print("Example 2: Multi-Database Management")
    print("=" * 70)
    
    with MasterDBManager('example_multi.db') as manager:
        
        # 複数のDBを登録
        db_names = ['users', 'products', 'orders', 'logs']
        print(f"\n[Step 1] {len(db_names)}個のDB を登録")
        for db_name in db_names:
            manager.register_db(db_name)
            print(f"  ✓ {db_name}")
        
        # 各DBにデータを追加
        print(f"\n[Step 2] 各DBにテーブル・データを追加")
        
        # users
        with manager.use_db('users') as db:
            db.execute('''CREATE TABLE IF NOT EXISTS users
                         (id INTEGER PRIMARY KEY, name TEXT)''')
            db.execute("INSERT INTO users (name) VALUES (?)", ('User1',))
            db.commit()
        
        # products
        with manager.use_db('products') as db:
            db.execute('''CREATE TABLE IF NOT EXISTS products
                         (id INTEGER PRIMARY KEY, name TEXT, price REAL)''')
            db.execute("INSERT INTO products (name, price) VALUES (?, ?)",
                       ('Product1', 99.99))
            db.commit()
        
        # orders
        with manager.use_db('orders') as db:
            db.execute('''CREATE TABLE IF NOT EXISTS orders
                         (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER)''')
            db.execute("INSERT INTO orders (user_id, product_id) VALUES (?, ?)",
                       (1, 1))
            db.commit()
        
        # logs
        with manager.use_db('logs') as db:
            db.execute('''CREATE TABLE IF NOT EXISTS logs
                         (id INTEGER PRIMARY KEY, message TEXT, level TEXT)''')
            db.execute("INSERT INTO logs (message, level) VALUES (?, ?)",
                       ('System started', 'INFO'))
            db.commit()
        
        print("  ✓ 全DB にテーブル・データ追加完了")
        
        # 統計表示
        print(f"\n[Step 3] 統計情報")
        manager.list_dbs()


def example_integrity_check():
    """整合性検証の例"""
    print("\n" + "=" * 70)
    print("Example 3: Integrity Verification")
    print("=" * 70)
    
    with MasterDBManager('example_integrity.db') as manager:
        
        print("\n[Step 1] テストデータを作成")
        manager.register_db('test_data')
        
        with manager.use_db('test_data') as db:
            db.execute('''CREATE TABLE IF NOT EXISTS data
                         (id INTEGER PRIMARY KEY, value TEXT)''')
            for i in range(100):
                db.execute("INSERT INTO data (value) VALUES (?)",
                           (f'value_{i}',))
            db.commit()
        
        print("  ✓ テストデータ作成完了")
        
        print("\n[Step 2] 整合性検証（改ざん検知）")
        result = manager.verify_all()
        if result:
            print("  ✓ 全DB正常")
        else:
            print("  ✗ 改ざんが検知されました！")
        
        print("\n[Step 3] アクセスログ確認")
        manager.show_logs(limit=10)


def example_context_manager():
    """コンテキストマネージャの使用例"""
    print("\n" + "=" * 70)
    print("Example 4: Context Manager (Resource Safety)")
    print("=" * 70)
    
    with MasterDBManager('example_context.db') as manager:
        
        print("\n[Step 1] DB登録")
        manager.register_db('safe_data')
        
        print("\n[Step 2] with文で安全にDB操作")
        with manager.use_db('safe_data') as db:
            db.execute('''CREATE TABLE IF NOT EXISTS data
                         (id INTEGER PRIMARY KEY, content TEXT)''')
            db.execute("INSERT INTO data (content) VALUES (?)",
                       ('Safe insertion with context manager',))
            db.commit()
            print("  ✓ with文内でDB操作完了")
        # ← ここで自動的に save_db() と close() が呼ばれる
        
        print("\n[Step 3] データ確認")
        with manager.use_db('safe_data') as db:
            rows = db.execute('SELECT * FROM data').fetchall()
            for row in rows:
                print(f"  Data: {row['content']}")
        
        print("\n  ✅ リソースが安全にクリーンアップされました")


def example_error_handling():
    """エラーハンドリングの例"""
    print("\n" + "=" * 70)
    print("Example 5: Error Handling")
    print("=" * 70)
    
    from db_manager import DBNotFoundError, SecurityError
    
    with MasterDBManager('example_errors.db') as manager:
        
        # 存在しないDB
        print("\n[Error 1] 存在しないDBへのアクセス")
        try:
            with manager.use_db('nonexistent') as db:
                pass
        except DBNotFoundError as e:
            print(f"  ✓ エラーをキャッチ: {e}")
        
        # 正常なDB操作
        print("\n[Success] 正常なDB操作")
        manager.register_db('error_test')
        with manager.use_db('error_test') as db:
            db.execute('''CREATE TABLE IF NOT EXISTS test
                         (id INTEGER PRIMARY KEY, value TEXT)''')
            db.commit()
            print("  ✓ DB操作成功")


def main():
    """全ての例を実行"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "SQLite Compression Manager - Examples" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝")
    
    example_basic_operations()
    example_multi_database()
    example_integrity_check()
    example_context_manager()
    example_error_handling()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
