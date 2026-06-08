# -*- coding: utf-8 -*-
"""
db_manager.py - Compiler Verification Format
独自コンパイラ用の検証可能な中間表現
"""

import ast
import json
from pathlib import Path


class CompilerIR:
    """コンパイラ向け中間表現生成"""
    
    def __init__(self, source_path):
        with open(source_path, 'r', encoding='utf-8') as f:
            self.source = f.read()
        self.tree = ast.parse(self.source)
    
    def extract_type_annotations(self):
        """型情報の抽出"""
        types = {
            'function_signatures': [],
            'class_definitions': [],
            'variable_types': []
        }
        
        for node in ast.walk(self.tree):
            # 関数署名
            if isinstance(node, ast.FunctionDef):
                args_info = []
                for arg in node.args.args:
                    arg_type = 'Any'  # 型アノテーション無い場合
                    if arg.annotation:
                        arg_type = ast.unparse(arg.annotation)
                    args_info.append({
                        'name': arg.arg,
                        'type': arg_type
                    })
                
                return_type = 'Any'
                if node.returns:
                    return_type = ast.unparse(node.returns)
                
                types['function_signatures'].append({
                    'name': node.name,
                    'args': args_info,
                    'return': return_type,
                    'lineno': node.lineno
                })
            
            # クラス定義
            if isinstance(node, ast.ClassDef):
                types['class_definitions'].append({
                    'name': node.name,
                    'bases': [ast.unparse(base) for base in node.bases],
                    'lineno': node.lineno
                })
        
        return types
    
    def extract_control_flow(self):
        """制御フローの抽出"""
        control_flow = {
            'loops': [],
            'conditionals': [],
            'exception_handlers': [],
            'critical_sections': []
        }
        
        for node in ast.walk(self.tree):
            # ループ
            if isinstance(node, (ast.For, ast.While)):
                control_flow['loops'].append({
                    'type': node.__class__.__name__,
                    'lineno': node.lineno
                })
            
            # 条件分岐
            if isinstance(node, ast.If):
                control_flow['conditionals'].append({
                    'lineno': node.lineno,
                    'has_else': len(node.orelse) > 0
                })
            
            # 例外処理
            if isinstance(node, ast.Try):
                control_flow['exception_handlers'].append({
                    'lineno': node.lineno,
                    'handlers': len(node.handlers),
                    'has_finally': len(node.finalbody) > 0
                })
        
        return control_flow
    
    def extract_memory_operations(self):
        """メモリ操作の抽出（圧縮・DB操作）"""
        operations = {
            'file_io': [],
            'compression': [],
            'database': [],
            'hashing': []
        }
        
        source_lines = self.source.split('\n')
        
        for i, node in enumerate(ast.walk(self.tree)):
            if isinstance(node, ast.Call):
                func_name = ast.unparse(node.func) if isinstance(node.func, ast.Name) else ast.unparse(node.func)
                
                if 'open' in func_name:
                    operations['file_io'].append({
                        'operation': 'open',
                        'lineno': node.lineno
                    })
                
                if 'compress' in func_name or 'decompress' in func_name:
                    operations['compression'].append({
                        'operation': func_name,
                        'lineno': node.lineno
                    })
                
                if 'execute' in func_name or 'connect' in func_name:
                    operations['database'].append({
                        'operation': func_name,
                        'lineno': node.lineno
                    })
                
                if 'sha256' in func_name or 'hash' in func_name:
                    operations['hashing'].append({
                        'operation': func_name,
                        'lineno': node.lineno
                    })
        
        return operations
    
    def extract_security_boundaries(self):
        """セキュリティ境界の抽出"""
        boundaries = {
            'checksum_validation': [],
            'exception_handling': [],
            'resource_cleanup': [],
            'input_validation': []
        }
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.If):
                condition = ast.unparse(node.test)
                if 'checksum' in condition or 'hash' in condition:
                    boundaries['checksum_validation'].append({
                        'lineno': node.lineno,
                        'condition': condition[:60]
                    })
            
            if isinstance(node, ast.Try):
                boundaries['exception_handling'].append({
                    'lineno': node.lineno,
                    'handler_count': len(node.handlers)
                })
            
            if isinstance(node, ast.With):
                boundaries['resource_cleanup'].append({
                    'lineno': node.lineno,
                    'context': ast.unparse(node.items[0].context_expr) if node.items else 'unknown'
                })
        
        return boundaries
    
    def generate_verification_rules(self):
        """コンパイラ検証ルール生成"""
        rules = {
            'data_flow_rules': [
                {
                    'id': 'rule_001',
                    'name': 'Checksum Must Always Verify',
                    'description': 'SHA256 checksum検証が常に実行されること',
                    'check': 'if checksum_verify in security_boundaries',
                    'severity': 'CRITICAL'
                },
                {
                    'id': 'rule_002',
                    'name': 'File Handle Always Close',
                    'description': 'ファイルハンドルが必ずクローズされること',
                    'check': 'if resource_cleanup count == file_io count',
                    'severity': 'HIGH'
                },
                {
                    'id': 'rule_003',
                    'name': 'Exception Handling Complete',
                    'description': '全ファイルI/Oが例外処理に包まれること',
                    'check': 'if exception_handlers > 0',
                    'severity': 'HIGH'
                },
                {
                    'id': 'rule_004',
                    'name': 'No Memory Leak on Compression',
                    'description': '圧縮・展開時のメモリリークがないこと',
                    'check': 'memory_safety_check()',
                    'severity': 'CRITICAL'
                },
                {
                    'id': 'rule_005',
                    'name': 'Transaction Atomicity',
                    'description': 'DB操作の原子性が保証されること',
                    'check': 'atomic_operation_check()',
                    'severity': 'HIGH'
                },
                {
                    'id': 'rule_006',
                    'name': 'No SQL Injection',
                    'description': 'プリペアドステートメントのみを使用',
                    'check': 'prepared_statement_only()',
                    'severity': 'CRITICAL'
                }
            ],
            'optimization_rules': [
                {
                    'id': 'opt_001',
                    'name': 'Compress in Parallel',
                    'description': 'マルチスレッド圧縮でパフォーマンス向上',
                    'potential_gain': '30-40%'
                },
                {
                    'id': 'opt_002',
                    'name': 'Incremental Backup',
                    'description': '差分バックアップで転送量削減',
                    'potential_gain': '50-70%'
                },
                {
                    'id': 'opt_003',
                    'name': 'Lazy Decompression',
                    'description': '必要な部分だけを展開',
                    'potential_gain': '20-30%'
                }
            ]
        }
        return rules
    
    def generate_ir_json(self):
        """完全なIR（中間表現）をJSON形式で出力"""
        ir = {
            'metadata': {
                'file': 'db_manager.py',
                'source_hash': self._hash_source(),
                'lines': len(self.source.split('\n')),
                'format': 'compiler_ir_v1.0'
            },
            'structure': {
                'types': self.extract_type_annotations(),
                'control_flow': self.extract_control_flow(),
                'memory_operations': self.extract_memory_operations(),
                'security_boundaries': self.extract_security_boundaries()
            },
            'verification': {
                'rules': self.generate_verification_rules(),
                'expected_checks': [
                    'CHECKSUM_VALIDATION',
                    'MEMORY_SAFETY',
                    'FILE_INTEGRITY',
                    'TRANSACTION_SAFETY',
                    'RESOURCE_CLEANUP'
                ]
            }
        }
        return ir
    
    def _hash_source(self):
        import hashlib
        return hashlib.sha256(self.source.encode()).hexdigest()


def main():
    print("=" * 70)
    print("db_manager.py - Compiler Intermediate Representation")
    print("=" * 70)
    
    compiler = CompilerIR('/mnt/user-data/outputs/db_manager.py')
    
    # 型情報
    print("\n[TYPE ANNOTATIONS]")
    types = compiler.extract_type_annotations()
    print(f"  Functions: {len(types['function_signatures'])}")
    print(f"  Classes: {len(types['class_definitions'])}")
    for cls in types['class_definitions']:
        print(f"    - {cls['name']} (line {cls['lineno']})")
    
    # 制御フロー
    print("\n[CONTROL FLOW]")
    cf = compiler.extract_control_flow()
    print(f"  Loops: {len(cf['loops'])}")
    print(f"  Conditionals: {len(cf['conditionals'])}")
    print(f"  Exception handlers: {len(cf['exception_handlers'])}")
    
    # メモリ操作
    print("\n[MEMORY OPERATIONS]")
    mem = compiler.extract_memory_operations()
    print(f"  File I/O: {len(mem['file_io'])} operations")
    print(f"  Compression: {len(mem['compression'])} operations")
    print(f"  Database: {len(mem['database'])} operations")
    print(f"  Hashing: {len(mem['hashing'])} operations")
    
    # セキュリティ境界
    print("\n[SECURITY BOUNDARIES]")
    sec = compiler.extract_security_boundaries()
    print(f"  Checksum validations: {len(sec['checksum_validation'])}")
    print(f"  Exception handlers: {len(sec['exception_handling'])}")
    print(f"  Resource cleanup points: {len(sec['resource_cleanup'])}")
    
    # 検証ルール
    print("\n[VERIFICATION RULES]")
    rules = compiler.generate_verification_rules()
    print(f"  Data flow rules: {len(rules['data_flow_rules'])}")
    print(f"  Optimization rules: {len(rules['optimization_rules'])}")
    for rule in rules['data_flow_rules'][:3]:
        print(f"    [{rule['id']}] {rule['name']} - {rule['severity']}")
    
    # 完全なIRをJSON出力
    print("\n[GENERATING COMPILER IR...]")
    ir = compiler.generate_ir_json()
    
    ir_file = '/mnt/user-data/outputs/db_manager_ir.json'
    with open(ir_file, 'w', encoding='utf-8') as f:
        json.dump(ir, f, indent=2, ensure_ascii=False)
    print(f"  ✓ IR exported to: {ir_file}")
    
    # コンパイラ向け検証ルール
    print("\n[COMPILER VERIFICATION CHECKLIST]")
    for rule in rules['data_flow_rules']:
        print(f"  [ ] {rule['id']}: {rule['name']} ({rule['severity']})")
    
    print("\n" + "=" * 70)
    print("Ready for custom compiler verification")
    print("=" * 70)


if __name__ == '__main__':
    main()
