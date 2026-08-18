#!/usr/bin/env python
"""
Mock 数据初始化脚本
用于初始化和填充 Mock 数据库
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_data.seed import MockDataSeeder


def main():
    """主函数"""
    print("开始初始化 Mock 数据...")
    
    try:
        seeder = MockDataSeeder()
        seeder.run()
        print("Mock 数据初始化成功！")
        print(f"数据库路径: {seeder.db_path}")
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()