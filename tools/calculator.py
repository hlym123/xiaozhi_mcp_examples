from mcp.server.fastmcp import FastMCP
import sys
import random
import math
import logging
from typing import Dict, Union, List
import re

logger = logging.getLogger('Calculator')

# 安全计算白名单
SAFE_ENV = {
    'math': math,
    'random': random,
    '__builtins__': {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'len': len
    }
}

def register_calculator_tools(mcp: FastMCP):
    """注册所有计算工具到MCP服务"""
    
    # 基础计算器（增强安全版）
    @mcp.tool()
    def calculator(expression: str) -> Dict[str, Union[bool, float, str]]:
        """
        安全计算数学表达式（支持math和random模块）
        
        参数:
            expression: 合法的Python数学表达式，如 "math.sqrt(2) + random.random()"
        
        返回:
            {
                "success": 是否成功,
                "result": 计算结果,
                "error": 错误信息(失败时)
            }
        
        示例:
            "2 * math.pi * 3" => {"success": True, "result": 18.84955592153876}
        """
        try:
            # 安全检查
            if not re.match(r'^[\d\s+\-*/().<>=,!%&|^~@:\[\]{}_a-zA-Z]+$', expression):
                raise ValueError("包含非法字符")
                
            # 安全计算
            result = eval(expression, {'__builtins__': None}, SAFE_ENV)
            
            logger.info(f"计算: {expression} = {result}")
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.warning(f"计算失败: {expression} | 错误: {str(e)}")
            return {"success": False, "error": str(e)}

    # 科学计算扩展
    @mcp.tool()
    def scientific_calc(operation: str, args: List[float]) -> Dict:
        """
        高级科学计算（避免eval安全问题）
        
        支持操作:
            - "sin", "cos", "tan", "log", "sqrt", "pow"
        
        示例:
            {"operation": "pow", "args": [2, 3]} => {"success": True, "result": 8}
        """
        print("高级科学计算")
        OPERATIONS = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'sqrt': math.sqrt,
            'pow': math.pow
        }
        
        try:
            func = OPERATIONS[operation.lower()]
            result = func(*args)
            return {"success": True, "result": result}
        except KeyError:
            return {"success": False, "error": f"不支持的操作: {operation}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 统计计算工具
    @mcp.tool()
    def statistics(data: List[float], operation: str = 'mean') -> Dict:
        """
        统计计算工具
        
        支持操作:
            - "mean": 平均值
            - "median": 中位数
            - "stdev": 标准差
            - "variance": 方差
        
        示例:
            {"data": [1,2,3,4], "operation": "mean"} => {"success": True, "result": 2.5}
        """
        print("统计计算")
        try:
            if operation == 'mean':
                result = sum(data) / len(data)
            elif operation == 'median':
                sorted_data = sorted(data)
                n = len(sorted_data)
                result = (sorted_data[n//2] + sorted_data[(n-1)//2]) / 2
            elif operation == 'stdev':
                mean = sum(data) / len(data)
                result = math.sqrt(sum((x - mean)**2 for x in data) / len(data))
            elif operation == 'variance':
                mean = sum(data) / len(data)
                result = sum((x - mean)**2 for x in data) / len(data)
            else:
                raise ValueError("未知统计操作")
                
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 单位转换工具
    @mcp.tool()
    def unit_converter(value: float, from_unit: str, to_unit: str) -> Dict:
        """
        单位转换工具
        
        支持单位:
            - 长度: m, cm, mm, km, in, ft
            - 重量: kg, g, lb, oz
            - 温度: C, F, K
        
        示例:
            {"value": 100, "from_unit": "cm", "to_unit": "m"} => {"success": True, "result": 1}
        """
        print("单位转换")
        CONVERSIONS = {
            'length': {
                'm': 1,
                'cm': 0.01,
                'mm': 0.001,
                'km': 1000,
                'in': 0.0254,
                'ft': 0.3048
            },
            'weight': {
                'kg': 1,
                'g': 0.001,
                'lb': 0.453592,
                'oz': 0.0283495
            },
            'temperature': {
                'C->F': lambda x: x * 9/5 + 32,
                'F->C': lambda x: (x - 32) * 5/9,
                'C->K': lambda x: x + 273.15,
                'K->C': lambda x: x - 273.15
            }
        }
        
        try:
            # 温度转换特殊处理
            if {from_unit, to_unit} <= {'C', 'F', 'K'}:
                if from_unit == to_unit:
                    result = value
                else:
                    key = f"{from_unit}->{to_unit}"
                    result = CONVERSIONS['temperature'][key](value)
            else:
                # 普通单位转换
                category = 'length' if from_unit in CONVERSIONS['length'] else 'weight'
                result = value * CONVERSIONS[category][from_unit] / CONVERSIONS[category][to_unit]
                
            return {"success": True, "result": round(result, 6)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 随机数生成器
    @mcp.tool()
    def random_number_generator(
        min_val: float = 0,
        max_val: float = 1,
        is_integer: bool = False,
        count: int = 1
    ) -> Dict:
        """
        随机数生成工具
        
        参数:
            - min_val: 最小值
            - max_val: 最大值
            - is_integer: 是否生成整数
            - count: 生成数量
        
        示例:
            {"min_val": 1, "max_val": 10, "is_integer": True, "count": 3}
            => {"success": True, "result": [4, 7, 2]}
        """
        print("随机数生成")
        try:
            if count == 1:
                result = random.randint(min_val, max_val) if is_integer else random.uniform(min_val, max_val)
            else:
                result = [
                    random.randint(min_val, max_val) if is_integer 
                    else random.uniform(min_val, max_val)
                    for _ in range(count)
                ]
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}