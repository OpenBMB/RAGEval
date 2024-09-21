import sys
import os
import json
from openai import OpenAI
import random
import argparse
import time
import pathlib
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

def generate_article(
    model_name,
    data_for_complete,
    crime_name,
    crime_detail,
):
    time.sleep(random.random() * 1.5)
    system_prompt = '你是一名经验丰富的法院书记员，你有丰富的法律文书撰写经验，并且有极强的想象力。'
    user_prompt = f"""你需要写一份详实的法律文书范文。
你需要根据一个法律文书的JSON模板，编写一份法律文书的实例：
- 本次需要编写的罪名是：{crime_name}
- “被告人”字段，被告人的姓名、性别、出生日期等均已填写，你仅需要填写其民族、职业等信息。
- “辩护人”字段，辩护人的姓名已填写，你仅需要填写其所属律所。
- 在“案件经过”字段中，请为每个关键事件提供确切日期和详细描述。
- “犯罪事实”字段，请创造一个涉及{crime_name}的场景，包括具体的行为、时间、地点和涉及金额。
- “犯罪事实”中的“详细情况”字段是一个列表，应该有3至4起事件，每起事件有“时间段”，“行为”和“证据材料”3个要素。
- 犯人的具体行为应该非常详细，你要认真补充案件的经过和细节，可能涉及到的金额、时间、地点、品牌等信息应该看起来非常真实。
- 支持判罚的证据材料需要非常详细，可以列出多个证据材料，包括书面证据、物证、证人证言等。
- “法律程序”字段，包括审判的日期、审判结果和具体的量刑（如果适用缓刑的，也需要告知缓刑的刑期）。
{crime_detail}
"""
    user_prompt += json.dumps(data_for_complete, ensure_ascii=False, indent=1)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    while True:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            ).choices[0].message.content
            response = response[response.find("{") : response.rfind("}") + 1]
            response = json.loads(response)
            break
        except Exception as e:
            print(f"Error occurred: {e}. Retrying...")
            time.sleep(1)
    return response
    

def set_value(data):
    city = random.choice(names)
    while True:
        street = random.choice(names)
        if street != city:
            break
    address = f"{city}市{street}街{random.randint(1, 100)}号"
    while True:
        district = random.choice(names)
        if district != city and district != street:
            break
    court = f"{city}市{district}区人民法院"
    procuratorate = f"{city}市{district}区人民检察院"
    def get_name():
        return random.choice(surnames) + random.choice(["某某", "某"])
    data["法院和检察院"]["法院"] = court
    data["法院和检察院"]["检察院"] = procuratorate
    data["被告人"]["姓名"] = get_name()
    data["被告人"]["性别"] = random.choice(["男", "女"])
    data["被告人"]["出生日期"] = f"{random.randint(1960, 2000)}年{random.randint(1, 12)}月{random.randint(1, 28)}日"
    data["被告人"]["居住地"] = address
    data["辩护人"]["姓名"] = get_name()
    data["审判长"] = get_name()
    data["审判员"] = get_name()
    data["书记员"] = get_name()
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="single")
    parser.add_argument("--model_name", type=str, default='gpt-4o')
    parser.add_argument("--data_for_complete", type=str, default=None)
    parser.add_argument("--crime_names", type=str, default=None)
    parser.add_argument("--crime_name_idx", type=int, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()

    json_idx = args.json_idx
    model_name = args.model_name

    data = load_json_data(args.data_for_complete)

    data = set_value(data)


    crime_dict_list = load_json_data(args.crime_names)
    crime_dict = crime_dict_list[args.crime_name_idx]
    crime_name, crime_detail = crime_dict['名称'], crime_dict['详情']
    response = generate_article(model_name, data, crime_name, crime_detail)
    save_output(args.output_dir, response, crime_name, json_idx, None, "json")

if __name__ == "__main__":
    main()
