#!/usr/bin/env python3
"""
测试文件示例
"""

import unittest
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import main

class TestMain(unittest.TestCase):
    """测试主程序"""
    
    def test_main_function_exists(self):
        """测试主函数是否存在"""
        self.assertTrue(callable(main))
    
    def test_main_runs_without_error(self):
        """测试主函数是否能正常运行"""
        try:
            main()
        except Exception as e:
            self.fail(f"main() 函数运行时出错: {e}")

if __name__ == "__main__":
    unittest.main()
