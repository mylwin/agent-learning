"""
示例4: SFT训练完整流程

演示如何使用RLTrainingTool进行SFT监督微调
"""

import sys as _run_sys
from pathlib import Path as _RunPath
_run_sys.path.insert(0, str(_RunPath(__file__).resolve().parents[1]))
from run_paths import result_path, memory_config

import sys
from pathlib import Path
import json

# 添加项目路径
project_root = Path(__file__).parent.parent / "HelloAgents"
sys.path.insert(0, str(project_root))

from hello_agents.tools import RLTrainingTool


# ============================================================================
# 示例1: 最简单的SFT训练
# ============================================================================

def minimal_sft_training():
    """
    最简单的SFT训练示例
    
    只需要调用RLTrainingTool即可
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": result_path("chapter11", "output", "sft_minimal"),
        "max_samples": 10,
        "num_epochs": 1,
    }
    
    print("最简单的SFT训练:")
    print(f"  模型: {config['model_name']}")
    print(f"  样本数: {config['max_samples']}")
    print(f"  训练轮数: {config['num_epochs']}")
    
    # 实际训练时取消注释
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n✅ 训练完成! 模型保存在: {result_dict['output_dir']}")
    
    return config


# ============================================================================
# 示例2: 标准SFT训练配置
# ============================================================================

def standard_sft_training():
    """
    标准的SFT训练配置
    
    包含:
    - LoRA参数高效微调
    - 合理的训练参数
    - 使用部分数据集
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        
        # 模型配置
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": result_path("chapter11", "output", "sft_standard"),
        
        # 数据配置
        "max_samples": 1000,  # 使用1000个样本
        
        # 训练配置
        "num_epochs": 3,
        "batch_size": 4,
        "learning_rate": 5e-5,
        
        # LoRA配置
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    }
    
    print("标准SFT训练配置:")
    print(f"  模型: {config['model_name']}")
    print(f"  样本数: {config['max_samples']}")
    print(f"  训练轮数: {config['num_epochs']}")
    print(f"  batch_size: {config['batch_size']}")
    print(f"  learning_rate: {config['learning_rate']}")
    print(f"  LoRA秩: {config['lora_r']}")
    
    # 实际训练时取消注释
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n✅ 训练完成!")
    # print(f"📁 模型保存在: {result_dict['output_dir']}")
    
    return config


# ============================================================================
# 示例3: 完整数据集训练
# ============================================================================

def full_dataset_training():
    """
    使用完整数据集进行训练
    
    max_samples=None 表示使用全部数据
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": result_path("chapter11", "output", "sft_full"),
        
        # 使用全部数据
        "max_samples": None,  # None = 使用全部数据
        
        "num_epochs": 3,
        "batch_size": 4,
        "learning_rate": 5e-5,
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    }
    
    print("完整数据集训练:")
    print(f"  模型: {config['model_name']}")
    print(f"  样本数: 全部 (max_samples=None)")
    print(f"  训练轮数: {config['num_epochs']}")
    print(f"  预计样本数: ~7500 (GSM8K训练集)")
    
    # 实际训练时取消注释
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n✅ 训练完成!")
    
    return config


# ============================================================================
# 示例4: 不同学习率的对比
# ============================================================================

def compare_learning_rates():
    """
    对比不同学习率的训练效果
    
    常用学习率:
    - 1e-5: 保守,适合微调已经很好的模型
    - 5e-5: 推荐,平衡学习速度和稳定性
    - 1e-4: 激进,适合快速实验
    """
    learning_rates = {
        "保守 (1e-5)": 1e-5,
        "推荐 (5e-5)": 5e-5,
        "激进 (1e-4)": 1e-4,
    }
    
    print("不同学习率的对比:")
    for name, lr in learning_rates.items():
        print(f"\n{name}:")
        print(f"  learning_rate: {lr}")
        print(f"  适用场景: ", end="")
        if lr == 1e-5:
            print("模型已经很好,只需微调")
        elif lr == 5e-5:
            print("标准训练,推荐使用")
        else:
            print("快速实验(可能不稳定)")
    
    # 训练示例
    print("\n训练示例 (推荐学习率):")
    tool = RLTrainingTool()
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "max_samples": 1000,
        "num_epochs": 3,
        "learning_rate": 5e-5,
        "use_lora": True,
    }
    print(f"  learning_rate: {config['learning_rate']}")
    
    # result = tool.run(config)
    
    return learning_rates


# ============================================================================
# 示例5: 显存优化配置
# ============================================================================

def memory_optimized_training():
    """
    显存优化配置
    
    适用于显存受限的情况:
    - 使用LoRA
    - 减小batch size
    - 使用较小的LoRA秩
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": result_path("chapter11", "output", "sft_memory_opt"),
        
        # 显存优化
        "max_samples": 1000,
        "num_epochs": 3,
        "batch_size": 1,  # 最小batch size
        "learning_rate": 5e-5,
        
        # LoRA配置
        "use_lora": True,
        "lora_r": 8,  # 使用较小的秩
        "lora_alpha": 16,
    }
    
    print("显存优化配置:")
    print(f"  batch_size: {config['batch_size']} (最小)")
    print(f"  lora_r: {config['lora_r']} (较小)")
    print(f"  use_lora: {config['use_lora']}")
    print(f"  预计显存占用: ~3-4GB")
    
    # 实际训练时取消注释
    # result = tool.run(config)
    
    return config


# ============================================================================
# 示例6: 实际训练示例
# ============================================================================

def practical_training_example():
    """
    实际训练示例 - 可以直接运行
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": result_path("chapter11", "output", "sft_practical"),
        
        # 使用较少样本进行快速测试
        "max_samples": 100,
        "num_epochs": 1,
        "batch_size": 4,
        "learning_rate": 5e-5,
        
        # 使用LoRA
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    }
    
    print("实际训练示例:")
    print(f"  模型: {config['model_name']}")
    print(f"  样本数: {config['max_samples']}")
    print(f"  训练轮数: {config['num_epochs']}")
    print(f"  输出目录: {config['output_dir']}")
    
    print("\n💡 提示: 取消下面的注释以开始训练")
    print("# result = tool.run(config)")
    print("# result_dict = json.loads(result)")
    print("# print(f'✅ 训练完成! 模型保存在: {result_dict[\"output_dir\"]}')")
    
    # 实际训练时取消注释
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n✅ 训练完成!")
    # print(f"📁 模型保存在: {result_dict['output_dir']}")
    
    return config


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("示例1: 最简单的SFT训练")
    print("="*80)
    minimal_sft_training()
    
    print("\n" + "="*80)
    print("示例2: 标准SFT训练配置")
    print("="*80)
    standard_sft_training()
    
    print("\n" + "="*80)
    print("示例3: 完整数据集训练")
    print("="*80)
    full_dataset_training()
    
    print("\n" + "="*80)
    print("示例4: 不同学习率的对比")
    print("="*80)
    compare_learning_rates()
    
    print("\n" + "="*80)
    print("示例5: 显存优化配置")
    print("="*80)
    memory_optimized_training()
    
    print("\n" + "="*80)
    print("示例6: 实际训练示例")
    print("="*80)
    practical_training_example()

