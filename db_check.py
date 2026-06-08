# -*- coding: utf-8 -*-
# db_check.py
# Pyto用 db_manager 動作確認スクリプト

exec(open('db_manager.py', encoding='utf-8').read())

# --- デモ実行 ---
demo()

# --- 個別使用例 ---
# with MasterDBManager('master.db') as manager:
#
#     # DB登録
#     manager.register_db('users')
#
#     # データ追加
#     with manager.use_db('users') as db:
#         db.execute(
#             'CREATE TABLE IF NOT EXISTS users '
#             '(id INTEGER PRIMARY KEY, name TEXT, email TEXT)'
#         )
#         db.execute(
#             'INSERT INTO users (name, email) VALUES (?, ?)',
#             ('田中太郎', 'tanaka@example.com')
#         )
#         db.commit()
#
#     # データ確認
#     with manager.use_db('users') as db:
#         rows = db.execute('SELECT * FROM users').fetchall()
#         for row in rows:
#             print(row['id'], row['name'], row['email'])
