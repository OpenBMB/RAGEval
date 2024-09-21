import os
import pathlib
import json


def load_json_data(filepath):
    """Load JSON data from a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_output(output_dir, response, type_name, json_idx, file_name=None, file_ext="json"):
    output_path = pathlib.Path(output_dir) / type_name / str(json_idx)
    os.makedirs(
        output_path,
        exist_ok=True
    )
    with open(
        output_path / f"{str(json_idx) if file_name is None else file_name}.{file_ext}",
        "w",
        encoding="utf-8"
    ) as f:
        if file_ext == 'txt':
            f.write(response)
        else:
            json.dump(response, f, ensure_ascii=False, indent=1)