import os
from pipeline.utils import load_json, save_json
import argparse

def get_aggregation(file_path):
    print(f"Starting aggregation for: {file_path}")

    item = load_json(file_path)
    title = item["new_name"]
    path = f'./data_gen/examples_{title}_meaningful.json'
    examples = load_json(path)
    summary = item["all_summary"]
    chapters_len = len(item.get("chapters", []))  # Get chapter length, default to 0 if missing
    summary_len = len(summary)  # Get summary length

    data = {
        "title": title,
        "author": item["author"],
        "profile": item["profile"],
        "representative_name": item["representative_name"],
        "max_index": item["max_index"],
        "chapters_len": chapters_len,
        "summary_len": summary_len,
        "summary": summary,
        "examples": examples
    }

    save_path = "./data_gen_question"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    save_json(f'{save_path}/finally_examples_{title}.json', data)

    print(f"Finished aggregation for: {file_path}")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON file.")
    parser.add_argument("file_path", help="Path to the JSON file.")
    args = parser.parse_args()
    get_aggregation(args.file_path)