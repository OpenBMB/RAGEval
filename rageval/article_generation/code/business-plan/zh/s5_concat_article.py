import sys
import os
import json
import argparse
import pathlib
import time
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

from dotenv import load_dotenv

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

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


def concat_article(file_path, output_dir, industry, json_idx):
    """将生成的各部分合并为完整文章。"""
    try:
        data = load_json_data(file_path)
        article = data.get("生成的文章", "")

        # 保存为txt
        save_output(
            output_dir,
            article,
            industry,
            str(json_idx),
            file_path.stem,
            "txt"
        )

        return True
    except Exception as e:
        print(f"处理 {file_path} 时出错: {e}")
        return False


def process_industry(industry, file_dir_path, json_idx, output_dir):
    """处理单个行业的所有文章。"""
    job_input_path = file_dir_path / industry / str(json_idx)
    
    results = []
    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name
            results.append(concat_article(file_path, output_dir, industry, json_idx))
    
    return all(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_dir_path', type=str, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument('--json_idx', type=int, default=0)
    args = parser.parse_args()
    
    file_dir_path = pathlib.Path(args.file_dir_path)
    output_dir = pathlib.Path(args.output_dir)
    json_idx = args.json_idx

    # 使用 ProcessPoolExecutor 进行并行处理
    with ProcessPoolExecutor(max_workers=20) as executor:
        results = list(
            tqdm(
                executor.map(
                    process_industry,
                    industry_list,
                    [file_dir_path] * len(industry_list),
                    [json_idx] * len(industry_list),
                    [output_dir] * len(industry_list),
                ),
                total=len(industry_list),
            )
        )

    if all(results):
        print("所有商业计划书已成功合并并保存。")
    else:
        print("部分商业计划书处理失败。请查看上面的错误信息。")


if __name__ == "__main__":
    main() 