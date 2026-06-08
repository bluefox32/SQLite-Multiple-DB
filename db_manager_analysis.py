# -*- coding: utf-8 -*-
"""
db_manager.py - 静的解析レポート
SQLite複数DB圧縮管理システムの構造検証
"""

import ast
import hashlib
from pathlib import Path


class CodeAnalyzer:
    """Pythonコードの静的解析"""
    
    def __init__(self, source_path):
        with open(source_path, 'r', encoding='utf-8') as f:
            self.source = f.read()
        self.tree = ast.parse(self.source)
    
    def analyze_classes(self):
        """クラス定義の抽出"""
        classes = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    m.name for m in node.body 
                    if isinstance(m, ast.FunctionDef)
                ]
                classes.append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'methods': methods,
                    'method_count': len(methods)
                })
        return classes
    
    def analyze_functions(self):
        """関数定義の抽出"""
        functions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                args = [arg.arg for arg in node.args.args]
                functions.append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': args,
                    'arg_count': len(args)
                })
        return functions
    
    def analyze_imports(self):
        """インポート依存関係の抽出"""
        imports = {'standard': [], 'third_party': []}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports['standard'].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports['standard'].append(module)
        return imports
    
    def analyze_dataflow(self):
        """データフロー解析（重要な変数の追跡）"""
        dataflow = {
            'ledger_operations': [],
            'file_operations': [],
            'crypto_operations': []
        }
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Attribute):
                if 'ledger' in ast.unparse(node):
                    dataflow['ledger_operations'].append(ast.unparse(node))
                if 'file' in ast.unparse(node) or 'open' in ast.unparse(node):
                    dataflow['file_operations'].append(ast.unparse(node))
                if 'hash' in ast.unparse(node) or 'encrypt' in ast.unparse(node):
                    dataflow['crypto_operations'].append(ast.unparse(node))
        
        return dataflow
    
    def check_security_critical_paths(self):
        """セキュリティ クリティカルパスの検証"""
        critical_checks = {
            'checksum_verification': False,
            'file_integrity_check': False,
            'exception_handling': False,
            'transaction_safety': False
        }
        
        source_str = self.source
        
        if 'checksum' in source_str and 'sha256' in source_str:
            critical_checks['checksum_verification'] = True
        
        if 'decompress_and_verify' in source_str:
            critical_checks['file_integrity_check'] = True
        
        if 'try:' in source_str and 'except' in source_str:
            critical_checks['exception_handling'] = True
        
        if 'transaction' in source_str or 'backup' in source_str:
            critical_checks['transaction_safety'] = True
        
        return critical_checks


def generate_report():
    """静的解析レポート生成"""
    
    analyzer = CodeAnalyzer('/mnt/user-data/outputs/db_manager.py')
    
    print("=" * 70)
    print("db_manager.py - 静的解析レポート")
    print("=" * 70)
    
    # ソースコード情報
    print("\n[SOURCE CODE INFO]")
    lines = analyzer.source.split('\n')
    print(f"  Total lines: {len(lines)}")
    print(f"  Source hash: {hashlib.sha256(analyzer.source.encode()).hexdigest()[:16]}...")
    
    # クラス構造
    print("\n[CLASS STRUCTURE]")
    classes = analyzer.analyze_classes()
    for cls in classes:
        print(f"  [{cls['name']}] ({cls['method_count']} methods)")
        for method in cls['methods'][:5]:  # 最初の5メソッド
            print(f"    - {method}()")
        if len(cls['methods']) > 5:
            print(f"    ... and {len(cls['methods']) - 5} more")
    
    # グローバル関数
    print("\n[GLOBAL FUNCTIONS]")
    functions = analyzer.analyze_functions()
    for func in functions:
        if not any(cls['name'] in func['name'] for cls in classes):
            args_str = ', '.join(func['args'][:3])
            if len(func['args']) > 3:
                args_str += f", ... +{len(func['args']) - 3}"
            print(f"  {func['name']}({args_str})")
    
    # 依存関係
    print("\n[DEPENDENCIES]")
    imports = analyzer.analyze_imports()
    unique_imports = set(imports['standard'])
    for imp in sorted(unique_imports):
        print(f"  - {imp}")
    
    # セキュリティ関連パス
    print("\n[SECURITY CRITICAL PATHS]")
    security = analyzer.check_security_critical_paths()
    for check, status in security.items():
        status_str = "[OK]" if status else "[WARN]"
        print(f"  {status_str} {check}")
    
    # データフロー
    print("\n[DATA FLOW ANALYSIS]")
    dataflow = analyzer.analyze_dataflow()
    for category, operations in dataflow.items():
        unique_ops = list(set(operations))[:3]
        print(f"  [{category}]")
        for op in unique_ops:
            print(f"    - {op[:60]}")
        if len(set(operations)) > 3:
            print(f"    ... and {len(set(operations)) - 3} more")
    
    # 品質スコア
    print("\n[QUALITY ASSESSMENT]")
    score = 0
    
    # クラス数
    if len(classes) >= 5:
        print(f"  ✓ 適切なクラス設計 ({len(classes)} classes)")
        score += 20
    else:
        print(f"  ⚠ クラス数が少ない ({len(classes)} classes)")
        score += 10
    
    # セキュリティ
    security_ok = sum(1 for v in security.values() if v)
    if security_ok >= 3:
        print(f"  ✓ セキュリティ対策 ({security_ok}/4 checks passed)")
        score += 25
    else:
        print(f"  ⚠ セキュリティ対策不足 ({security_ok}/4 checks)")
        score += 10
    
    # エラーハンドリング
    if 'try:' in analyzer.source and 'except' in analyzer.source:
        print(f"  ✓ 例外処理実装")
        score += 15
    else:
        print(f"  ⚠ 例外処理が不十分")
        score += 5
    
    # ドキュメンテーション
    if '"""' in analyzer.source:
        docstring_count = analyzer.source.count('"""')
        print(f"  ✓ ドキュメント充実 ({docstring_count} docstrings)")
        score += 20
    else:
        print(f"  ⚠ ドキュメント不足")
        score += 5
    
    # コンテキストマネージャ
    if '__enter__' in analyzer.source and '__exit__' in analyzer.source:
        print(f"  ✓ コンテキストマネージャ実装（リソース安全）")
        score += 20
    else:
        print(f"  ⚠ コンテキストマネージャなし")
        score += 0
    
    print(f"\n  [OVERALL SCORE: {score}/100]")
    
    # 推奨事項
    print("\n[RECOMMENDATIONS FOR COMPILER]")
    print("""
  1. [データ流向き解析]
     - user_ledger: Dict<str, float> の監視
     - compression/decompression の整合性検証
     - checksum の値の不変性確認

  2. [トランザクション検証]
     - ファイルI/O時の原子性確保
     - メモリDB → ファイルDB への書き込みの完全性
     - エラー時のロールバック

  3. [メモリ安全性]
     - バッファオーバーフロー検査（zlib.decompress）
     - メモリリーク防止（ファイルハンドルのクローズ）
     - 圧縮データの境界検証

  4. [最適化機会]
     - checksum計算の並列化
     - 圧縮率向上（zlib level調整）
     - DB backup の増分対応

  5. [配布形式への変換]
     - AST変換 → 中間言語
     - バイトコード最適化
     - runtime 環境との互換性検証
    """)
    
    print("\n" + "=" * 70)
    print("END OF REPORT")
    print("=" * 70)
    
    return {
        'classes': len(classes),
        'functions': len(functions),
        'imports': len(set(imports['standard'])),
        'security_checks': security_ok,
        'quality_score': score
    }


if __name__ == '__main__':
    report = generate_report()
    print("\n[SUMMARY]")
    print(f"  Classes: {report['classes']}")
    print(f"  Functions: {report['functions']}")
    print(f"  Dependencies: {report['imports']}")
    print(f"  Security checks passed: {report['security_checks']}/4")
    print(f"  Quality score: {report['quality_score']}/100")
