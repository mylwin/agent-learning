"""
分布式训练示例

本脚本演示如何使用Accelerate进行分布式训练。
训练代码本身无需修改,只需通过accelerate launch启动即可。

使用方法:
1. 单GPU训练:
   python 07_distributed_training.py

2. 多GPU DDP训练:
   accelerate launch --config_file accelerate_configs/multi_gpu_ddp.yaml 07_distributed_training.py

3. DeepSpeed ZeRO-2训练:
   accelerate launch --config_file accelerate_configs/deepspeed_zero2.yaml 07_distributed_training.py

4. DeepSpeed ZeRO-3训练:
   accelerate launch --config_file accelerate_configs/deepspeed_zero3.yaml 07_distributed_training.py
"""

import sys as _run_sys
from pathlib import Path as _RunPath
_run_sys.path.insert(0, str(_RunPath(__file__).resolve().parents[1]))
from run_paths import result_path, memory_config

import sys
import os

# 添加HelloAgents到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "HelloAgents"))

from hello_agents.tools import RLTrainingTool
import json

def main():
    print("="*80)
    print("分布式训练示例")
    print("="*80)
    
    # 检测分布式环境
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    
    if world_size > 1:
        print(f"\n🚀 分布式训练模式")
        print(f"   - 总进程数: {world_size}")
        print(f"   - 当前进程: {local_rank}")
        print(f"   - 分布式后端: {os.environ.get('ACCELERATE_DISTRIBUTED_TYPE', 'MULTI_GPU')}")
    else:
        print(f"\n💻 单GPU训练模式")
    
    print("="*80)
    
    # 创建训练工具
    rl_tool = RLTrainingTool()
    
    # 训练配置
    # 注意: batch_size是每个GPU的batch size
    # 总batch size = batch_size × num_gpus × gradient_accumulation_steps
    config = {
        "action": "train",
        "algorithm": "grpo",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": result_path("chapter11", "models", "grpo_distributed"),
        "max_samples": 200,  # 使用200个样本
        "num_epochs": 2,
        "batch_size": 2,  # 每个GPU的batch size
        "use_lora": True,
        "use_wandb": False,
        "use_tensorboard": True,
    }
    
    # 只在主进程打印配置
    if local_rank == 0:
        print("\n训练配置:")
        print(f"  - 模型: {config['model_name']}")
        print(f"  - 样本数: {config['max_samples']}")
        print(f"  - Epoch数: {config['num_epochs']}")
        print(f"  - 每GPU batch size: {config['batch_size']}")
        if world_size > 1:
            total_batch = config['batch_size'] * world_size
            print(f"  - 总batch size: {total_batch}")
        print("="*80)
    
    # 开始训练
    # 训练代码完全不需要修改!
    # Accelerate会自动处理分布式训练的所有细节
    result = rl_tool.run(config)
    
    # 只在主进程打印结果
    if local_rank == 0:
        result_data = json.loads(result)
        print("\n" + "="*80)
        print("训练完成!")
        print("="*80)
        print(f"状态: {result_data['status']}")
        print(f"模型路径: {result_data['output_dir']}")
        print("="*80)
        
        # 打印性能提示
        if world_size > 1:
            print(f"\n💡 性能提示:")
            print(f"   使用了 {world_size} 个GPU进行训练")
            print(f"   理论加速比: ~{world_size * 0.85:.1f}x")
            print(f"   (实际加速比取决于通信开销和数据加载)")

if __name__ == "__main__":
    main()

