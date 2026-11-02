"""
步骤1：仅生成AIME题目

运行方法：
python data_generation/step1_generate_only.py 30 3.0

参数：
- 30: 生成题目数量
- 3.0: 每次生成之间的延迟（秒）
"""

import sys as _run_sys
from pathlib import Path as _RunPath
_run_sys.path.insert(0, str(_RunPath(__file__).resolve().parents[2]))
from run_paths import result_path, memory_config

import sys
from aime_generator import AIMEGenerator


def main():
    # 解析命令行参数
    num_problems = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    delay_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
    
    print("\n" + "="*80)
    print("📝 步骤1: 生成AIME题目")
    print("="*80)
    print(f"\n配置信息:")
    print(f"  - 生成题目数量: {num_problems}")
    print(f"  - API延迟: {delay_seconds}秒/题")
    print(f"  - 生成参考数据: TianHongZXY/aime-1983-2025（900+道题）")
    
    # 创建生成器
    generator = AIMEGenerator(delay_seconds=delay_seconds)
    
    # 生成并保存
    generated_data_path = generator.generate_and_save(
        num_problems=num_problems,
        output_dir=result_path("chapter12", "data_generation", "generated_data")
    )
    
    print(f"\n✅ 步骤1完成！生成数据保存在: {generated_data_path}")
    print(f"\n下一步：运行评估")
    print(f"python data_generation/step2_evaluate_only.py {generated_data_path} 2024")


if __name__ == "__main__":
    main()

