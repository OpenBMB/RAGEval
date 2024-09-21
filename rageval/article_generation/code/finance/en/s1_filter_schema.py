import os
import json
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=str)
    parser.add_argument("--output_dir", type=str)
    args = parser.parse_args()
    source_dir = args.source_dir
    output_dir = args.output_dir
    file_name_list = os.listdir(source_dir)
    for file_name in file_name_list:
        file_path = os.path.join(source_dir, file_name)
        print(file_name)
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        for item in data["报告内容"]:
            for event in item["重要事件"]:
                event.pop("可能涉及到的实体")
            for metric in item["可能涉及的指标"]:
                metric.pop("可能涉及到的实体", None)
                metric.pop("可能关联的事件", None)
                metric["值"] = "请补充"
        for item in data["额外信息"]:
            for content in item["内容"]:
                content.pop("可能涉及到的实体")
        with open(os.path.join(output_dir, file_name), "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
