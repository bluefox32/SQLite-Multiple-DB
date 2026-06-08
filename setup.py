#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Compression Manager - Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# README を読み込む
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="sqlite-compression-manager",
    version="1.0.0",
    description="Lightweight virtualization layer for multi-DB SQLite compression management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SQLite Compression Manager Team",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/sqlite-compression-manager",
    license="MIT",
    
    # パッケージ設定
    py_modules=["db_manager", "db_manager_compiler_ir"],
    python_requires=">=3.7",
    
    # 依存関係
    install_requires=[
        # コア依存関係は標準ライブラリのみ
    ],
    
    # オプション依存関係
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "pylint>=2.17.4",
        ],
        "docs": [
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "compression": [
            "lz4>=4.0.2",  # 高速圧縮の代替案
        ],
    },
    
    # キーワード
    keywords=[
        "sqlite",
        "compression",
        "database",
        "virtualization",
        "p2p",
        "distributed",
    ],
    
    # 分類
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # プロジェクト URL
    project_urls={
        "Bug Reports": "https://github.com/yourusername/sqlite-compression-manager/issues",
        "Documentation": "https://github.com/yourusername/sqlite-compression-manager/blob/main/README.md",
        "Source Code": "https://github.com/yourusername/sqlite-compression-manager",
    },
    
    # エントリポイント
    entry_points={
        "console_scripts": [
            "db-manager=db_manager:main",
        ],
    },
)
