import os
import json
import random
import argparse
import time
import sys
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')

names = [
    "蓝天", "白云", "翠峰", "金沙", "银月", "碧波", "红霞", "朝阳", "暮光", "星辰",
    "晨曦", "夕照", "彩虹", "紫陌", "绿茵", "黄埔", "碧海", "青松", "银杏", "橙园",
    "紫竹", "赤壁", "翡翠", "琥珀", "桃源", "松涛", "花溪", "石榴", "樱桃", "桂林",
    "雪山", "流水", "晴川", "霜叶", "冰川", "烟波", "雾岛", "雨城", "风帆", "雷峰",
    "火岭", "土丘", "铁桥", "钢城", "玉门", "珠港", "锦绣", "织金", "丝路", "棉花",
    "薰衣", "茉莉", "梅雨", "橡树", "柏林", "杨柳", "桐城", "梧桐", "柿园", "葡萄",
    "苹果", "樟树", "核桃", "雪梨", "芒果", "杏花", "梨园", "荔枝", "椰风", "竹林",
    "香山", "橄榄", "榆树", "杉木", "栗子", "桃花", "荷塘", "薄雾", "雨燕", "夜莺",
    "翠湖", "雪莲", "琉璃", "朱雀", "玄武", "青龙", "白虎", "黄鹤", "碧落", "金桥",
    "银川", "青田", "黄金", "紫霞", "碧空", "金丝", "银杏", "樱花", "梧桐", "青竹"
]
surnames = [
    "赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈", "褚", "卫", "蒋", "沈", "韩", "杨", "朱", "秦", "尤", "许",
    "何", "吕", "施", "张", "孔", "曹", "严", "华", "金", "魏", "陶", "姜", "戚", "谢", "邹", "喻", "柏", "水", "窦", "章",
    "云", "苏", "潘", "葛", "奚", "范", "彭", "郎", "鲁", "韦", "昌", "马", "苗", "凤", "花", "方", "俞", "任", "袁", "柳",
    "酆", "鲍", "史", "唐", "费", "廉", "岑", "薛", "雷", "贺", "倪", "汤", "滕", "殷", "罗", "毕", "郝", "邬", "安", "常",
    "乐", "于", "时", "傅", "皮", "卞", "齐", "康", "伍", "余", "元", "卜", "顾", "孟", "平", "黄", "和", "穆", "萧", "尹",
    "姚", "邵", "湛", "汪", "祁", "毛", "禹", "狄", "米", "贝", "明", "臧", "计", "伏", "成", "戴", "谈", "宋", "茅", "庞",
    "熊", "纪", "舒", "屈", "项", "祝", "董", "梁", "杜", "阮", "蓝", "闵", "席", "季", "麻", "强", "贾", "路", "娄", "危"
]

month_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

may_died = ['细菌性食物中毒', '甲型肝炎', '疟疾', '鼻咽恶性肿瘤', '食管恶性肿瘤', 
            '流行性脑髓脊膜炎', '肺炎', '先天性心脏病', '新生儿破伤风']


def generate_article(
    model_name, 
    disease_name,
    disease_detail,
    data_for_complete,
    is_surgery, 
    is_dead
):
    time.sleep(random.random() * 1.5)
    system_prompt = '你是一名经验丰富的主治医生，你有丰富的住院病历撰写经验，并且有极强的想象力。'
    user_prompt = f"""你正在为一位病人撰写病历。
你需要根据一个住院病历的模板文件，撰写一份住院病历的实例：
- 本次需要撰写的病种是：{disease_name}-{disease_detail}
- 注意：病人{'做了手术' if is_surgery else '未做手术'}，{'已死亡' if is_dead else '未死亡'}
- 直接以JSON形式回复，不需要其它句子。
- 每个字段都要填写，不是示例，比如上级医师查房记录、交（接）班记录、转科记录、阶段小结、医嘱、体温单、辅助检查报告单等。
- 病人的一些基本信息，如姓名、性别、年龄、住址、入院时间等已经填写完毕。
- 医院应该与病人住址在同一个城市。
模板如下：
"""
    user_prompt += json.dumps(data_for_complete, ensure_ascii=False, indent=1)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    while True:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        ).choices[0].message.content
        response = response[response.find("{") : response.rfind("}") + 1]
        try:
            response = json.loads(response)
            break
        except json.JSONDecodeError:
            print("JSONDecodeError")
            continue
    return response


def set_value(schema, disease_name, disease_detail):
    schema['住院病历']['基本信息']['姓名'] = random.choice(surnames) + "某某"
    schema['住院病历']['基本信息']['性别'] = random.choice(["男", "女"])
    if disease_name=='妊娠、分娩病及产褥期并发症':
        schema['住院病历']['基本信息']['性别'] = "女"
    if schema['住院病历']['基本信息']['性别'] == "男":
        del schema['住院病历']["婚育史及家族史"]["月经史"]

    if disease_detail['名称'] in may_died:
        is_dead = random.random() > 0.8
    else:
        is_dead = False
    is_surgery = random.random() > 0.8

    if not is_dead:
        del schema['住院病历']['入院后病程记录']['死亡相关']
    else:
        is_surgery = True
    if not is_surgery:
        del schema['住院病历']['入院后病程记录']['手术相关']
    schema['住院病历']['基本信息']['年龄'] = f"{random.randint(1, 100)}岁"
    if disease_name == '起源于围产期的情况':
        schema['住院病历']['基本信息']['年龄'] = f"出生{random.randint(1, 10)}个小时"
    schema['住院病历']['基本信息']['入院时间'] = f"{random.choice(month_list)}月{random.randint(1, 28)}日"
    city = random.choice(names)
    while True:
        street = random.choice(names)
        if street != city:
            break
    schema['住院病历']['基本信息']['住址'] = address = f"{city}市{street}街{random.randint(1, 100)}号"
    return schema, is_surgery, is_dead


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="new")
    parser.add_argument("--model_name", type=str, default="gpt-4o")
    parser.add_argument("--data_for_complete", type=str, required=True)
    parser.add_argument("--data_for_reference", type=str, default=None)
    parser.add_argument("--ref_idx", type=int, default=0)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()

    data = load_json_data(args.data_for_reference)
    model_name = args.model_name
    
    disease_type, disease_detail = list(data.items())[args.ref_idx]
    for disease_item in disease_detail:

        schema = load_json_data(args.data_for_complete)
        
        schema, is_surgery, is_dead = set_value(schema, disease_type, disease_item)
        response = generate_article(model_name, disease_type, disease_item, schema, is_surgery, is_dead)
        response['病种'] = {disease_type: disease_item}

        save_output(args.output_dir, response, disease_type, args.json_idx, disease_item['名称'], "json")


if __name__ == "__main__":
    main()
