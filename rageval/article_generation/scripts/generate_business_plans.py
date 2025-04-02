#!/usr/bin/env python3
import os
import json
import time
import random
import argparse
from openai import OpenAI
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

# 加载环境变量
load_dotenv()

# 设置OpenAI API密钥和基础URL
openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL', '')

# 行业列表
INDUSTRIES = {
    "en": [
        "Technology",
        "Healthcare",
        "Education",
        "Agriculture",
        "Financial Services",
        "Software Development",
        "Food & Beverage",
        "Fitness",
        "Consulting",
        "E-commerce",
        "Fashion",
        "Retail",
        "Professional Services",
        "Real Estate",
        "Construction",
        "Manufacturing",
        "Renewable Energy",
        "Transportation",
        "Media & Entertainment",
        "Tourism"
    ],
    "zh": [
        "科技",
        "医疗健康",
        "教育",
        "农业",
        "金融服务",
        "软件开发",
        "餐饮",
        "健身",
        "咨询",
        "电子商务",
        "时尚",
        "零售",
        "专业服务",
        "房地产",
        "建筑",
        "制造业",
        "可再生能源",
        "交通运输",
        "媒体与娱乐",
        "旅游"
    ]
}

# 示例商业计划书（英文）
EXAMPLE_BUSINESS_PLAN = """
I&B Investments Business Plan Summary
Executive Summary
I&B Investments is a new limited liability company formed under Utah law, focused on developing family entertainment centers (FECs) in Weber County, Utah. The company aims to provide quality family entertainment to local communities by establishing modern, comprehensive entertainment facilities.

The first proposed site is a ten-acre parcel in Weber County, with a second site planned within five years. According to the U.S. Census Bureau, personal consumption for amusement and recreation increased by $31.5 billion from 1990 to 1998, with an industry gross of $56.2 billion.

With strong management and aggressive marketing, we project consistent annual growth of at least 5%. Our first center is expected to generate several million dollars in gross sales in its first year of operations.

Key Objectives:

Achieve 10% market share in our first year
Increase gross margins within the second year
Grow market share by 10% minimum for each of the first five years
Currently, there are no quality FECs within a 50-mile radius of our target location.

Company Summary
The company's first FEC, named Wasatch Family Fun Center, will be located in Weber County facing the Wasatch Front Mountains. The facility will be designed as the most modern family entertainment center in the Northern Wasatch area.

Start-up Requirements:

Total funding required: $5,507,500
Start-up expenses: $229,575
Start-up assets: $5,277,925
The proposed property has excellent visibility with interstate access. Traffic counts show an average of 30,685 cars daily exiting and entering the interstate at this junction, with 56,490 cars passing on the interstate.

Services
Our FEC will provide customers with a wholesome environment for family entertainment including:

Indoor facilities for year-round operation
Go-carts, miniature golf, climbing walls
Batting cages, bumper boats
Gaming & redemption center
Souvenir/gift shop
Food and beverages
Private party rooms for birthdays and corporate events
The center will be designed to capture the ambiance of the Olde West with a casual atmosphere enhanced by landscaping depicting the Wasatch Mountains.

Market Analysis
Research indicates the prime market for an FEC is in urban areas near upper to middle-income neighborhoods. A typical FEC has a market radius of 7-10 miles, potentially extending to 15-20 miles with highway access.

Within a 15-mile radius of our site:

Population exceeds 500,000
Median age is 27
Average household size is 3.5 persons
Average household adjusted gross income is $39,250
Our target markets include:

Age 15 to 24: 90,450 people (growing at 6.5% annually)
Age 25 to 34: 66,800 people (growing at 2% annually)
Age 35 to 54 with children: 125,250 people (growing at 9% annually)
Weber County's adjusted gross income is $37,500, making it one of Utah's top three counties for personal income.

Strategy and Implementation
Our competitive edge comes from:

First to market in the area
Year-round indoor facilities
Wide variety of activities
Seasoned management team
Strong community ties
Family-oriented environment
Average per person expenditure is projected at $8.50 per visit, with projected annual revenue of $3.56 million in Year 1, growing to $6.39 million by Year 5.

Key milestones include:

Property purchase by October 2002
Construction starting late 2002
Grand Opening by Mother's Day weekend 2003
Construction on Phase 2 starting in 2005
Management Summary
Our management team includes:

Mark D. Bergman, Managing Partner
Joseph L. Hull, Operations Manager & Public Relations
Darren Strebel, Manager of Promotions and Media
Rod Schaffer, Treasurer/Comptroller
Laura Strebel, Retail Space Agent and Gift Shop Manager
We've also retained specialized consultants including Harold Skripsky, a family entertainment industry expert, and Randy Sant, a Redevelopment Agency specialist.

Financial Plan
Break-even monthly revenue: $51,010
Monthly fixed costs: $34,725

Projected Profit & Loss:

Year 1: $3.56M sales, $738K net profit (20.7% margin)
Year 3: $5.80M sales, $1.14M net profit (19.7% margin)
Year 5: $6.39M sales, $1.22M net profit (19.1% margin)
Investment Analysis:

Net Present Value: $15.89M
Internal Rate of Return: 178%
The company expects to achieve positive cash flow from the first month of operation, with steady growth throughout the five-year projection period.

Through focused implementation of this plan, I&B Investments is positioned to become the premier family entertainment destination in Northern Utah, capturing significant market share and providing strong returns for investors.
"""

# 示例商业计划书（中文）
EXAMPLE_BUSINESS_PLAN_ZH = """
I&B投资公司商业计划书摘要
执行摘要
I&B投资公司是一家根据犹他州法律新成立的有限责任公司，专注于在犹他州韦伯县开发家庭娱乐中心（FEC）。公司旨在通过建立现代化、综合性的娱乐设施，为当地社区提供优质的家庭娱乐服务。

第一个拟建地点是韦伯县的一块十英亩土地，计划在五年内开发第二个地点。根据美国人口普查局的数据，从1990年到1998年，娱乐和休闲的个人消费增加了315亿美元，行业总收入达到562亿美元。

凭借强大的管理和积极的营销，我们预计年增长率至少为5%。我们的第一个中心预计在运营第一年就能产生数百万美元的毛销售额。

主要目标：

第一年实现10%的市场份额
第二年提高毛利率
前五年每年市场份额增长至少10%
目前，在我们目标地点50英里半径范围内没有优质的家庭娱乐中心。

公司概述
公司的第一个家庭娱乐中心名为Wasatch家庭娱乐中心，将位于韦伯县，面向Wasatch Front山脉。该设施将被设计为Wasatch北部地区最现代化的家庭娱乐中心。

启动要求：

所需总资金：5,507,500美元
启动费用：229,575美元
启动资产：5,277,925美元
拟建物业具有极佳的可见度，可直达州际公路。交通统计显示，平均每天有30,685辆汽车在该路口进出州际公路，另有56,490辆汽车在州际公路上通过。

服务内容
我们的家庭娱乐中心将为客户提供健康的家庭娱乐环境，包括：

全年运营的室内设施
卡丁车、迷你高尔夫、攀岩墙
棒球练习场、碰碰船
游戏和积分兑换中心
纪念品/礼品店
食品和饮料
生日派对和企业活动的私人派对室
该中心将设计成Olde West风格，通过描绘Wasatch山脉的景观设计增强休闲氛围。

市场分析
研究表明，家庭娱乐中心的主要市场位于中高收入社区附近的城区。典型的家庭娱乐中心市场半径为7-10英里，如果有高速公路通道，可延伸至15-20英里。

在我们地点15英里半径范围内：

人口超过50万
中位年龄为27岁
平均家庭规模为3.5人
平均家庭调整后总收入为39,250美元
我们的目标市场包括：

15-24岁：90,450人（年增长6.5%）
25-34岁：66,800人（年增长2%）
35-54岁有子女：125,250人（年增长9%）
韦伯县的调整后总收入为37,500美元，是犹他州个人收入最高的三个县之一。

战略与实施
我们的竞争优势来自：

该地区首家
全年室内设施
多样化的活动
经验丰富的管理团队
强大的社区联系
以家庭为导向的环境
预计每人每次访问的平均支出为8.50美元，第一年预计年收入为356万美元，到第五年增长至639万美元。

关键里程碑包括：

2002年10月前完成物业购买
2002年底开始建设
2003年母亲节周末盛大开业
2005年开始第二期建设
管理团队概述
我们的管理团队包括：

Mark D. Bergman，管理合伙人
Joseph L. Hull，运营经理兼公共关系
Darren Strebel，促销和媒体经理
Rod Schaffer，财务主管/审计员
Laura Strebel，零售空间代理和礼品店经理
我们还聘请了专业顾问，包括家庭娱乐行业专家Harold Skripsky和重建机构专家Randy Sant。

财务计划
月度收支平衡点：51,010美元
月度固定成本：34,725美元

预计损益：

第1年：销售额356万美元，净利润73.8万美元（利润率20.7%）
第3年：销售额580万美元，净利润114万美元（利润率19.7%）
第5年：销售额639万美元，净利润122万美元（利润率19.1%）
投资分析：

净现值：1,589万美元
内部收益率：178%
公司预计从运营第一个月开始就能实现正现金流，并在五年预测期内保持稳定增长。

通过本计划的重点实施，I&B投资公司有望成为犹他州北部首屈一指的家庭娱乐目的地，占据重要的市场份额，并为投资者提供丰厚的回报。
"""

def generate_business_plan(
    industry: str,
    language: str,
    is_zero_shot: bool = True,
    example: Optional[str] = None,
    model_name: str = "gpt-3.5-turbo"
) -> str:
    """
    生成商业计划书
    
    Args:
        industry: 行业名称
        language: 语言 ('en' 或 'zh')
        is_zero_shot: 是否为zero-shot生成
        example: one-shot示例文本
        model_name: 使用的模型名称
    
    Returns:
        生成的商业计划书
    """
    # 构建提示词
    if language == "en":
        if is_zero_shot:
            prompt = f"Generate a comprehensive business plan for a {industry} company："
        else:
            prompt = f"""Reference the following example business plan to generate a new business plan for a {industry} company:

{example}

Please generate a business plan following the same structure and level of detail as the example, but for a {industry} company."""
    else:
        if is_zero_shot:
            prompt = f"为{industry}行业生成一份全面的商业计划书：\n"
        else:
            prompt = f"""参考以下示例商业计划书，为{industry}行业生成一份新的商业计划书：

{example}

请按照示例的结构和详细程度，为{industry}行业生成一份商业计划书。"""

    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 创建OpenAI客户端
            if base_url:
                client = OpenAI(api_key=openai_api_key, base_url=base_url)
            else:
                client = OpenAI(api_key=openai_api_key)
            
            # 调用API
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional business consultant with extensive experience in creating business plans. Please generate detailed and practical business plans based on the requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            content = response.choices[0].message.content.strip()
            if content:
                return content
                
        except Exception as e:
            print(f"生成商业计划书时出错 (尝试 {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            time.sleep(random.random() * 1.5)  # 随机延迟
    
    print(f"在{max_retries}次尝试后仍未能生成商业计划书")
    return ""

def save_business_plan(
    content: str,
    industry: str,
    language: str,
    is_zero_shot: bool,
    output_dir: str
):
    """
    保存生成的商业计划书
    
    Args:
        content: 商业计划书内容
        industry: 行业名称
        language: 语言
        is_zero_shot: 是否为zero-shot生成
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = "zero_shot" if is_zero_shot else "one_shot"
    filename = f"{industry}_{mode}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # 保存文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"已保存商业计划书到: {filepath}")

def process_industry(
    industry: str,
    language: str,
    is_zero_shot: bool,
    model_name: str,
    output_dir: str
):
    """处理单个行业的商业计划书生成"""
    time.sleep(random.random() * 1.5)  # 随机延迟
    
    print(f"正在处理{language}的{industry}行业...")
    
    # 根据语言选择示例
    example = EXAMPLE_BUSINESS_PLAN_ZH if language == "zh" else EXAMPLE_BUSINESS_PLAN
    
    # 生成商业计划书
    content = generate_business_plan(
        industry=industry,
        language=language,
        is_zero_shot=is_zero_shot,
        example=example if not is_zero_shot else None,
        model_name=model_name
    )
    
    if content:
        # 保存商业计划书
        save_business_plan(
            content=content,
            industry=industry,
            language=language,
            is_zero_shot=is_zero_shot,
            output_dir=output_dir
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='gpt-3.5-turbo')
    parser.add_argument('--output_dir', type=str, default='output/business-plan')
    args = parser.parse_args()
    
    # 为每种语言和模式生成商业计划书
    for language in ["zh"]:#["en", "zh"]:
        for is_zero_shot in [False]:#[True, False]:
            mode = "zero_shot" if is_zero_shot else "one_shot"
            output_dir = os.path.join(args.output_dir, language, mode)
            
            print(f"\n开始生成{language}的{mode}商业计划书...")
            
            # 使用ProcessPoolExecutor进行并行处理
            with ProcessPoolExecutor(max_workers=20) as executor:
                list(
                    tqdm(
                        executor.map(
                            process_industry,
                            INDUSTRIES[language],
                            [language] * len(INDUSTRIES[language]),
                            [is_zero_shot] * len(INDUSTRIES[language]),
                            [args.model_name] * len(INDUSTRIES[language]),
                            [output_dir] * len(INDUSTRIES[language]),
                        ),
                        total=len(INDUSTRIES[language]),
                    )
                )
    
    print("\n所有商业计划书生成完成！")

if __name__ == "__main__":
    main() 