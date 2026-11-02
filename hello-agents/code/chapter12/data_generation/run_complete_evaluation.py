"""
完整评估流程

运行完整的数据生成和评估流程：
1. 生成AIME题目
2. LLM Judge评估
3. Win Rate评估
4. 生成综合报告

运行方法：
python data_generation/run_complete_evaluation.py 30 3.0

参数：
- 30: 生成题目数量
- 3.0: 每次生成之间的延迟（秒）

说明：
- 使用AIME 2025年真题作为参考
- 数据集来源：math-ai/aime25（JSONL格式）
"""

import sys as _run_sys
from pathlib import Path as _RunPath
_run_sys.path.insert(0, str(_RunPath(__file__).resolve().parents[2]))
from run_paths import result_path, memory_config

import json
import os
import sys
from datetime import datetime
from aime_generator import AIMEGenerator
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import LLMJudgeTool, WinRateTool


def run_complete_evaluation(
    num_problems: int = 30,
    delay_seconds: float = 3.0
):
    """
    运行完整评估流程

    Args:
        num_problems: 生成题目数量
        delay_seconds: 每次生成之间的延迟（秒），避免API速率限制
    """
    print("\n" + "="*80)
    print("🚀 AIME数据生成与评估完整流程")
    print("="*80)
    print(f"\n配置信息:")
    print(f"  - 生成题目数量: {num_problems}")
    print(f"  - API延迟: {delay_seconds}秒/题")
    print(f"  - 生成参考数据: TianHongZXY/aime-1983-2025（900+道题）")
    print(f"  - 评估参考: AIME 2025真题")

    # ========== 步骤1: 生成AIME题目 ==========
    print("\n" + "="*80)
    print("📝 步骤1: 生成AIME题目")
    print("="*80)

    generator = AIMEGenerator(delay_seconds=delay_seconds)
    generated_data_path = generator.generate_and_save(
        num_problems=num_problems,
        output_dir=result_path("chapter12", "data_generation", "generated_data")
    )

    print(f"\n✅ 步骤1完成！生成数据保存在: {generated_data_path}")

    # ========== 步骤2: 评估 ==========
    # 创建评估结果目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evaluation_dir = result_path("chapter12", "data_generation", "evaluation_results", timestamp)
    os.makedirs(evaluation_dir, exist_ok=True)
    os.makedirs(os.path.join(evaluation_dir, "llm_judge"), exist_ok=True)
    os.makedirs(os.path.join(evaluation_dir, "win_rate"), exist_ok=True)

    # 创建LLM
    llm = HelloAgentsLLM()

    # ========== 步骤2.1: LLM Judge评估 ==========
    print(f"\n🎯 步骤2.1: LLM Judge评估 (vs AIME 2025)")

    llm_judge_result = None
    try:
        llm_judge_tool = LLMJudgeTool(llm=llm)

        llm_judge_result_json = llm_judge_tool.run({
            "generated_data_path": generated_data_path,
            "reference_year": 2025,
            "max_samples": num_problems,
            "output_dir": os.path.join(evaluation_dir, "llm_judge"),
            "judge_model": "gpt-4o"
        })

        llm_judge_result = json.loads(llm_judge_result_json)
        print(f"\n✅ LLM Judge评估完成！")
        print(f"   平均总分: {llm_judge_result['metrics']['average_total_score']:.2f}/5.0")
        print(f"   通过率: {llm_judge_result['metrics']['pass_rate']:.2%}")
    except Exception as e:
        print(f"\n❌ LLM Judge评估失败: {e}")
        import traceback
        traceback.print_exc()

    # ========== 步骤2.2: Win Rate评估 ==========
    print(f"\n🏆 步骤2.2: Win Rate评估 (vs AIME 2025)")

    win_rate_result = None
    try:
        win_rate_tool = WinRateTool(llm=llm)

        win_rate_result_json = win_rate_tool.run({
            "generated_data_path": generated_data_path,
            "reference_year": 2025,
            "num_comparisons": min(num_problems, 20),  # 最多20次对比
            "output_dir": os.path.join(evaluation_dir, "win_rate"),
            "judge_model": "gpt-4o"
        })

        win_rate_result = json.loads(win_rate_result_json)
        print(f"\n✅ Win Rate评估完成！")
        print(f"   Win Rate: {win_rate_result['metrics']['win_rate']:.2%}")
    except Exception as e:
        print(f"\n❌ Win Rate评估失败: {e}")
        import traceback
        traceback.print_exc()

    # ========== 步骤3: 生成综合报告 ==========
    comprehensive_report_path = None
    if llm_judge_result or win_rate_result:
        print("\n" + "="*80)
        print("📊 步骤3: 生成综合报告")
        print("="*80)

        comprehensive_report_path = os.path.join(evaluation_dir, "comprehensive_report.md")

        # 生成综合报告
        report = generate_comprehensive_report(
            generated_data_path,
            llm_judge_result,
            win_rate_result
        )

        with open(comprehensive_report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ 综合报告已保存: {comprehensive_report_path}")

    # ========== 完成 ==========
    print("\n" + "="*80)
    print("🎉 完整评估流程完成！")
    print("="*80)
    print(f"\n📁 输出文件:")
    print(f"   - 生成数据: {generated_data_path}")
    print(f"   - 评估结果目录: {evaluation_dir}")

    if llm_judge_result:
        print(f"   - LLM Judge报告: {llm_judge_result.get('report_file', 'N/A')}")
    if win_rate_result:
        print(f"   - Win Rate报告: {win_rate_result.get('report_file', 'N/A')}")

    if comprehensive_report_path:
        print(f"   - 综合报告: {comprehensive_report_path}")

    print(f"\n💡 下一步:")
    if comprehensive_report_path:
        print(f"   1. 查看综合报告: {comprehensive_report_path}")
    print(f"   2. 运行人工验证: python data_generation/human_verification_ui.py {generated_data_path}")

    return {
        "generated_data_path": generated_data_path,
        "llm_judge_result": llm_judge_result,
        "win_rate_result": win_rate_result,
        "comprehensive_report_path": comprehensive_report_path
    }


def generate_comprehensive_report(
    generated_data_path: str,
    llm_judge_result: dict,
    win_rate_result: dict
) -> str:
    """生成综合评估报告"""

    # 加载生成数据
    with open(generated_data_path, 'r', encoding='utf-8') as f:
        generated_data = json.load(f)

    report = f"""# AIME数据生成与评估综合报告

## 1. 基本信息

- **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **生成题目数量**: {len(generated_data)}
- **参考AIME年份**: 2025
- **生成数据路径**: {generated_data_path}

## 2. 数据生成统计

### 主题分布

"""

    # 统计主题分布
    topic_counts = {}
    for item in generated_data:
        topic = item.get('topic', 'Unknown')
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    report += "| 主题 | 数量 | 占比 |\n"
    report += "|------|------|------|\n"
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(generated_data) * 100
        report += f"| {topic} | {count} | {percentage:.1f}% |\n"

    # LLM Judge结果
    if llm_judge_result:
        report += "\n## 3. LLM Judge评估结果\n\n"
        report += f"""**总体评分**:
- 平均总分: {llm_judge_result['metrics']['average_total_score']:.2f}/5.0
- 通过率: {llm_judge_result['metrics']['pass_rate']:.2%}
- 优秀率: {llm_judge_result['metrics']['excellent_rate']:.2%}

**各维度评分**:

| 维度 | 平均分 |
|------|--------|
| 正确性 | {llm_judge_result['metrics']['dimension_averages']['correctness']:.2f}/5.0 |
| 清晰度 | {llm_judge_result['metrics']['dimension_averages']['clarity']:.2f}/5.0 |
| 难度匹配 | {llm_judge_result['metrics']['dimension_averages']['difficulty_match']:.2f}/5.0 |
| 完整性 | {llm_judge_result['metrics']['dimension_averages']['completeness']:.2f}/5.0 |

"""

    # Win Rate结果
    if win_rate_result:
        report += "\n## 4. Win Rate评估结果\n\n"
        report += f"""**胜率统计**:
- Win Rate: {win_rate_result['metrics']['win_rate']:.2%}
- Loss Rate: {win_rate_result['metrics']['loss_rate']:.2%}
- Tie Rate: {win_rate_result['metrics']['tie_rate']:.2%}

**对比次数**:
- 总对比次数: {win_rate_result['metrics']['total_comparisons']} 次
- 胜出次数: {win_rate_result['metrics']['wins']} 次
- 失败次数: {win_rate_result['metrics']['losses']} 次
- 平局次数: {win_rate_result['metrics']['ties']} 次

"""

    # 综合结论
    report += "\n## 5. 综合结论\n\n"

    if llm_judge_result and win_rate_result:
        overall_avg_score = llm_judge_result['metrics']['average_total_score']
        overall_win_rate = win_rate_result['metrics']['win_rate']

        if overall_avg_score >= 4.5 and overall_win_rate >= 0.48:
            report += "✅ **结论**: 生成数据质量**优秀**，达到或超过AIME真题水平。\n"
        elif overall_avg_score >= 4.0 and overall_win_rate >= 0.45:
            report += "✅ **结论**: 生成数据质量**良好**，接近AIME真题水平。\n"
        else:
            report += "⚠️ **结论**: 生成数据质量**需要改进**，与AIME真题仍有差距。\n"

        report += f"\n**整体指标**:\n"
        report += f"- LLM Judge得分: {overall_avg_score:.2f}/5.0\n"
        report += f"- Win Rate: {overall_win_rate:.2%}\n"

    # 改进建议
    report += "\n## 6. 改进建议\n\n"

    if llm_judge_result:
        avg_score = llm_judge_result['metrics']['average_total_score']
        if avg_score >= 4.5:
            report += "- ✅ 继续保持当前的生成策略\n"
            report += "- ✅ 可以考虑增加生成数量\n"
        elif avg_score >= 4.0:
            report += "- 🔄 优化题目生成的提示词\n"
            report += "- 🔄 增加质量过滤步骤\n"
        else:
            report += "- ⚠️ 需要重新设计生成提示词\n"
            report += "- ⚠️ 考虑使用更强的生成模型\n"
            report += "- ⚠️ 增加人工审核环节\n"

    # 下一步行动
    report += "\n## 7. 下一步行动\n\n"
    report += "1. **人工验证**: 运行人工验证界面，对生成的题目进行人工审核\n"
    report += f"   ```bash\n   python data_generation/human_verification_ui.py {generated_data_path}\n   ```\n\n"
    report += "2. **质量筛选**: 根据评估结果筛选高质量题目\n\n"
    report += "3. **迭代优化**: 根据评估反馈优化生成策略\n"

    report += f"\n---\n\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    return report


def main():
    if len(sys.argv) < 2:
        print("用法: python run_complete_evaluation.py <num_problems> [delay_seconds]")
        print("\n说明:")
        print("  - 使用AIME 2025年真题作为参考")
        print("  - 数据集来源: math-ai/aime25（JSONL格式）")
        print("\n示例:")
        print("python run_complete_evaluation.py 30 3.0")
        sys.exit(1)

    # 解析命令行参数
    num_problems = int(sys.argv[1])
    delay_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0

    # 运行完整评估
    run_complete_evaluation(
        num_problems=num_problems,
        delay_seconds=delay_seconds
    )


if __name__ == "__main__":
    main()

