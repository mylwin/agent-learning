# my_calculator_tool.py
import ast
import math
import operator

from hello_agents import ToolRegistry


def my_calculate(expression: str) -> str:
    """简单的数学计算函数"""
    if not expression.strip():
        return "计算表达式不能为空"

    # 支持的基本运算
    operators = {
        ast.Add: operator.add,  # +
        ast.Sub: operator.sub,  # -
        ast.Mult: operator.mul,  # *
        ast.Div: operator.truediv,  # /
    }

    # 支持的基本函数
    functions = {
        "sqrt": math.sqrt,
        "pi": math.pi,
    }

    try:
        # parse(): 将字符串解析为抽象语法树
        # "eval": 解释模式为“表达式模式”
        node = ast.parse(expression, mode="eval")
        result = _eval_node(node.body, operators, functions)
        return str(result)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        return "计算失败，请检查表达式格式"


def _eval_node(node, operators, functions):
    """简化的表达式求值"""
    # 如果是数字节点，返回值
    if isinstance(node, ast.Constant):
        return node.value
    # 如果是二元/一元运算符，递归解析左右 operand
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left, operators, functions)
        right = _eval_node(node.right, operators, functions)
        op = operators.get(type(node.op))
        return op(left, right)
    # 如果是函数调用，递归解析参数
    elif isinstance(node, ast.Call):
        # 如果函数名不是 Name 类型，则返回 None
        if not isinstance(node.func, ast.Name):
            return None
        func_name = node.func.id
        # 如果函数名在函数列表中，则调用函数
        if func_name in functions:
            args = [_eval_node(arg, operators, functions) for arg in node.args]
            return functions[func_name](*args)
    # 如果函数名在函数列表中，则返回函数
    elif isinstance(node, ast.Name) and node.id in functions:
        return functions[node.id]


def create_calculator_registry():
    """创建包含计算器的工具注册表"""
    registry = ToolRegistry()

    # 注册计算器函数
    registry.register_function(
        name="my_calculator",
        description="简单的数学计算工具，支持基本运算(+,-,*,/)和sqrt函数",
        func=my_calculate,
    )

    return registry
