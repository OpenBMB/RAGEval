import sys
import os
import json
from openai import OpenAI
import random
import argparse
import time
import pathlib
import re
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')

industry_list = [
    "科技",
    "餐饮",
    "电子商务",
    "医疗健康",
    "教育",
    "金融服务",
    "咨询",
    "房地产",
    "可再生能源",
    "制造业",
    "交通运输",
    "旅游",
    "媒体与娱乐",
    "时尚",
    "农业",
    "零售",
    "建筑",
    "健身",
    "软件开发",
    "专业服务"
]

year_list = [2022, 2023, 2024]
funding_stages = ["种子轮", "A轮", "B轮", "自筹资金", "天使投资"]


def clean_json_response(response_text):
    """清理响应文本，确保其是有效的JSON。"""
    print("\n===== 清理 JSON 响应 =====")
    print(f"响应长度: {len(response_text)} 个字符")
    print(f"前100个字符: {response_text[:100]}")
    print(f"后100个字符: {response_text[-100:]}")
    
    # 检查响应是否已经有 markdown 代码块格式 ```json ... ```
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        print("在 markdown 代码块中找到了 JSON")
        json_content = json_match.group(1)
    else:
        # 首先，查找JSON内容 - 提取最外层大括号之间的内容
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        print(f"JSON 边界: 开始={start_idx}, 结束={end_idx}")
        
        if start_idx >= 0 and end_idx > start_idx:
            json_content = response_text[start_idx:end_idx]
        else:
            print("警告: 无法找到带有大括号的 JSON 内容")
            json_content = ""
    
    # 如果没有找到JSON，返回空字典
    if not json_content:
        print("警告: JSON 内容为空，返回空对象")
        return "{}"
    
    print(f"原始 JSON 内容 (前200个字符): {json_content[:200]}...")
    
    # 保存原始JSON到文件用于调试
    debug_dir = "./debug"
    os.makedirs(debug_dir, exist_ok=True)
    with open(f"{debug_dir}/原始json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
        f.write(json_content)
    
    # 使用简化的清理方法
    
    # 1. 修复未加引号的属性名 - 这是常见问题
    json_content = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_content)
    
    # 2. 删除数组和对象中的尾随逗号 - 另一个常见问题
    json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
    
    # 3. 修复元素之间缺少逗号的情况
    json_content = re.sub(r'(["\d])\s*\n\s*"', r'\1,\n"', json_content)
    
    # 4. 将单引号转换为属性值的双引号
    # 但要更小心地处理这个问题，以避免文本内部撇号的问题
    
    # 首先，将用于属性的单引号标准化为双引号
    # 这将'property':替换为"property":
    json_content = re.sub(r"'(\w+)'\s*:", r'"\1":', json_content)
    
    # 5. 处理中文引号 - 使用简单的替换而不是复杂的正则表达式
    # 将中文引号替换为英文引号
    pairs = [
        ("「", "\""), ("」", "\""),
        ("『", "\""), ("』", "\""),
        (""", "\""), (""", "\"")
    ]
    for ch1, ch2 in pairs:
        json_content = json_content.replace(ch1, ch2)
    
    # 针对不完整JSON的特殊修复：检查JSON是否被截断并完成它
    # 这种情况发生在API返回部分响应时
    if not json_content.strip().endswith('}'):
        print("警告: JSON似乎被截断了（不以'}'结尾），尝试修复...")
        
        # 1. 计算开括号和闭括号的数量，看看缺少什么
        open_braces = json_content.count('{')
        close_braces = json_content.count('}')
        open_brackets = json_content.count('[')
        close_brackets = json_content.count(']')
        
        print(f"大括号平衡: {open_braces}个开括号 vs {close_braces}个闭括号")
        print(f"方括号平衡: {open_brackets}个开括号 vs {close_brackets}个闭括号")
        
        # 2. 添加缺少的闭括号和方括号
        missing_braces = open_braces - close_braces
        missing_brackets = open_brackets - close_brackets
        
        if missing_braces > 0 or missing_brackets > 0:
            print(f"添加{missing_braces}个闭大括号和{missing_brackets}个闭方括号")
            # 首先关闭任何打开的方括号
            json_content += ']' * missing_brackets
            # 然后关闭任何打开的大括号
            json_content += '}' * missing_braces
            
            # 保存修复的JSON
            with open(f"{debug_dir}/修复截断json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
                f.write(json_content)
    
    print(f"清理后的 JSON 内容 (前200个字符): {json_content[:200]}...")
    
    # 保存清理后的JSON到文件用于调试
    with open(f"{debug_dir}/清理后json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
        f.write(json_content)
    
    # 调试: 检查 JSON 是否现在有效
    try:
        json.loads(json_content)
        print("JSON 现在有效!")
    except json.JSONDecodeError as e:
        print(f"警告: 清理后的 JSON 仍然无效: {e}")
        print(f"错误位置: 字符 {e.pos}, 行 {e.lineno}, 列 {e.colno}")
        if e.pos < len(json_content):
            # 显示错误周围更多上下文
            start_pos = max(0, e.pos - 200)
            end_pos = min(len(json_content), e.pos + 200)
            context = json_content[start_pos:end_pos]
            error_pos_in_context = e.pos - start_pos
            marked_context = context[:error_pos_in_context] + " >>> 错误位置 <<< " + context[error_pos_in_context:]
            print(f"错误周围的上下文 (400个字符):\n{marked_context}")
            
            # 将有问题的部分保存到单独的文件中进行详细分析
            with open(f"{debug_dir}/错误上下文_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding="utf-8") as f:
                f.write(f"错误: {e}\n")
                f.write(f"位置: 字符 {e.pos}, 行 {e.lineno}, 列 {e.colno}\n\n")
                f.write("错误周围的上下文:\n")
                f.write(marked_context)
            
            # 检查错误是否提到分隔符，这通常是逗号问题
            if "delimiter" in str(e):
                print("这看起来像是缺少逗号或分隔符的问题，尝试修复...")
                # 提取错误位置
                error_line = e.lineno
                error_col = e.colno
                error_pos = e.pos
                
                # 在错误位置添加逗号并再次尝试
                fixed_content = json_content[:error_pos] + "," + json_content[error_pos:]
                with open(f"{debug_dir}/逗号修复_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                
                try:
                    json_object = json.loads(fixed_content)
                    print("通过添加逗号成功修复!")
                    json_content = fixed_content
                except json.JSONDecodeError as comma_error:
                    print(f"逗号修复不起作用: {comma_error}")
            
            # 尝试更激进但更简单的方法 - 只修复最基本的问题
            # 让JSON.parse处理其余部分，因为它可能更宽容
            try:
                # 直接转换为Python对象，然后转回JSON
                # 这可能适用于JSON几乎有效的情况
                from ast import literal_eval
                
                # 只有在看起来大部分像有效的Python dict语法时才尝试
                if json_content.strip().startswith('{') and json_content.strip().endswith('}'):
                    print("尝试直接Python对象转换...")
                    # 用空格替换文本中有问题的撇号，以避免解析错误
                    safer_content = re.sub(r'(\w)"(\w)', r'\1 \2', json_content)
                    safer_content = re.sub(r'(\w)\'(\w)', r'\1 \2', safer_content)
                    
                    # 保存更安全的内容供检查
                    with open(f"{debug_dir}/安全化内容_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
                        f.write(safer_content)
                    
                    # 尝试评估为Python字典并转换回JSON
                    try:
                        # 在最小清理后使用更直接的方法json.loads
                        minimal_clean = json_content
                        # 双引号所有看起来像JSON属性的单引号字符串
                        minimal_clean = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', minimal_clean)
                        # 将剩余的单引号转换为双引号
                        minimal_clean = minimal_clean.replace("'", '"')
                        
                        # 保存最小清理版本
                        with open(f"{debug_dir}/最小清理_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
                            f.write(minimal_clean)
                        
                        # 现在尝试解析
                        json_object = json.loads(minimal_clean)
                        json_content = json.dumps(json_object, ensure_ascii=False)
                        print("使用最小清理成功转换!")
                        
                        # 也保存成功的版本
                        with open(f"{debug_dir}/成功json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
                            f.write(json_content)
                    except Exception as parsing_error:
                        print(f"直接转换失败: {parsing_error}")
            except Exception as advanced_error:
                print(f"高级转换尝试失败: {advanced_error}")

    return json_content


def generate_business_plan(
    model_name="gpt-3.5-turbo",
    industry="科技",
    data_for_complete=None
):
    print(f"\n===== 为 {industry} 行业生成商业计划书 =====")
    time.sleep(random.random() * 1.5)
    
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
        print(f"使用自定义基础 URL: {base_url}")
    else:
        client = OpenAI(api_key=openai_api_key)
        print("使用默认 OpenAI 基础 URL")
    
    system_prompt = """你是一位专业的商业顾问，专门为企业家制定全面、详细且具有说服力的商业计划书。
你的任务是按照指定的模板生成一份详细的商业计划书。

极其重要的输出格式说明：
1. 仅返回有效的JSON对象，不要添加任何额外的文本或markdown格式
2. 不要使用```json代码块或任何其他包装
3. 确保所有属性名使用双引号（如"property":而不是'property':）
4. 不要在数组或对象中包含尾随逗号
5. 对于文本中的撇号（如"公司的"或"它的"），使用普通撇号(')，而不是转义引号
6. 保持JSON结构简单 - 不要嵌套过深
7. 不要在JSON对象前后包含任何解释性文本
8. 响应应该以{开始，以}结束 - 没有其他内容

正确格式的例子:
{
  "公司名称": "科技解决方案有限公司",
  "行业": "科技",
  "执行摘要": {
    "使命宣言": "我们公司的使命是创新。"
  }
}"""
    
    user_prompt = """下面是一个结构化的模板，请你根据这个模板创建一份非常详细和全面的商业计划书。

- 公司所属行业：{industry}
- 这个模板提供了商业计划书的结构。请用真实、具体且详细的内容填充所有字段。
- 创建一个引人注目的公司名称、商业理念和使命宣言。
- 包含详细的市场分析，包括行业趋势和目标市场细分。
- 提供具体的产品/服务，清晰描述其特点和优势。
- 制定全面的营销策略。
- 包含详细的运营计划和财务预测。
- 财务预测应包括真实的收入模式、资金需求和预计损益。
- 包含全面的风险评估和减轻策略。
- 所有内容都要极其详细、具体且真实。

严格的JSON格式要求:
1. 你的整个回复必须只是一个有效的JSON对象，不包含其他任何内容
2. 所有属性名都必须用双引号括起来
3. 对象或数组中不要包含尾随逗号
4. 在文本中保持简单的撇号，不使用转义引号
5. 不要包含任何解释性文本、注释或markdown格式
6. 不要将你的回复包装在```json或任何其他格式中

请严格按照以下JSON模板结构:

""".format(industry=industry)
    
    data_json = json.dumps(data_for_complete, ensure_ascii=False, indent=1)
    user_prompt += data_json
    
    print(f"模板数据长度: {len(data_json)} 个字符")
    print(f"总提示长度: {len(system_prompt) + len(user_prompt)} 个字符")

    # 不进行重试，只进行一次尝试以便于调试
    print("\n进行单次API调用（不重试）...")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,  # 降低温度以获得更精确的格式
            response_format={"type": "json_object"}  # 使用JSON响应格式（如果支持）
        ).choices[0].message.content
        
        print(f"收到响应，长度: {len(response)} 个字符")
        
        # 清理JSON响应以处理常见的格式问题
        clean_json = clean_json_response(response)
        
        try:
            print("尝试解析 JSON...")
            parsed_response = json.loads(clean_json)
            print("成功解析 JSON 响应!")
            
            # 在响应中添加行业字段
            parsed_response["行业"] = industry
            print(f"添加行业字段: {industry}")
            
            # 打印有关解析响应的一些基本信息
            print(f"响应包含 {len(parsed_response.keys())} 个顶级键")
            if "公司名称" in parsed_response:
                print(f"公司名称: {parsed_response['公司名称']}")
            
            return parsed_response
            
        except json.JSONDecodeError as je:
            print(f"清理后的 JSON 解析错误: {je}")
            print(f"错误位置: 行 {je.lineno}, 列 {je.colno}, 位置 {je.pos}")
            if je.pos < len(clean_json):
                error_context = clean_json[max(0, je.pos-30):min(len(clean_json), je.pos+30)]
                print(f"错误周围的上下文: ...{error_context}...")
            
            # 由于不重试，返回最小响应
            minimal_response = {
                "公司名称": f"{industry}示例公司",
                "行业": industry,
                "执行摘要": {
                    "使命宣言": "在" + industry + "领域创造价值。"
                }
            }
            print(f"由于JSON错误返回最小响应: {json.dumps(minimal_response, indent=2, ensure_ascii=False)}")
            return minimal_response
            
    except Exception as e:
        print(f"API或其他错误: {e}")
        print(f"错误类型: {type(e).__name__}")
        
        # 由于不重试，返回最小响应
        minimal_response = {
            "公司名称": f"{industry}示例公司",
            "行业": industry,
            "执行摘要": {
                "使命宣言": "在" + industry + "领域创造价值。"
            }
        }
        print(f"由于API错误返回最小响应: {json.dumps(minimal_response, indent=2, ensure_ascii=False)}")
        return minimal_response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default='gpt-3.5-turbo')
    parser.add_argument("--industry", type=str, default="科技")
    parser.add_argument("--data_for_complete", type=str, required=True)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()
    
    print("\n===== 商业计划书生成器 =====")
    print(f"模型: {args.model_name}")
    print(f"行业: {args.industry}")
    print(f"数据文件: {args.data_for_complete}")
    print(f"输出目录: {args.output_dir}")
    
    try:
        model_name = args.model_name
        print(f"正在从 {args.data_for_complete} 加载模板数据...")
        data_for_complete = load_json_data(args.data_for_complete)
        print(f"模板数据加载成功，包含 {len(json.dumps(data_for_complete, ensure_ascii=False))} 个字符")
        
        field_name = args.data_for_complete.split("/")[-1].split(".")[0]
        print(f"字段名称: {field_name}")

        industry = args.industry
        print(f"正在为 {industry} 生成商业计划书...")
        response = generate_business_plan(
            model_name, industry, data_for_complete
        )
        
        output_dir = args.output_dir if args.output_dir else f"./output/business-plan/zh/config"
        print(f"正在保存输出到 {output_dir}...")
        save_output(output_dir, response, industry, args.json_idx, field_name, "json")
        print("商业计划书已成功生成并保存!")
        
    except Exception as e:
        print(f"\n===== 主函数中出现错误 =====")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        print(f"错误追踪:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main() 