#!/usr/bin/env python3
"""测试周报生成功能"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from services.report_service import generate_weekly_report, save_report_to_file

def main():
    print("测试周报生成功能...")
    
    try:
        # 生成周报
        report = generate_weekly_report()
        
        if report:
            print("OK: 周报生成成功！")
            print("\n" + "="*60)
            print("周报内容预览：")
            print("="*60)
            # 打印前800个字符预览
            print(report[:800] + "..." if len(report) > 800 else report)
            print("\n" + "="*60)
            
            # 保存到文件
            filename = save_report_to_file(report)
            print(f"File saved: {filename}")
            
            # 检查文件大小
            import os
            file_size = os.path.getsize(filename)
            print(f"Size: {file_size} bytes")
            
        else:
            print("ERROR: 周报生成失败：返回空内容")
            
    except Exception as e:
        print(f"ERROR: 周报生成失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
