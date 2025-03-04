import json
from pipeline.utils import chat, save_json, load_json
import argparse
import random

def generate_disturbance_run(examples):
    for i in range(1, len(examples)):
        behavior = examples[i]['key_behavior']

        if "disturbance" in examples[i]:
            print("Disturbance already exists")
            continue

        prompt = f"""
<Context Start>
{examples[i]['summary_refined']}
<Context End>

The original subsequent behavior was "{behavior}".
Estimate what personality trait does this reflect in brief words, and generate 3 behaviors that different personality traits would exhibit, answered in JSON format.
{{
"original_behavior_traits":"",
"difference": [
  {{
    "trait": "",
    "behavior": ""
  }},
  {{
    "trait": "",
    "behavior": ""
  }},
  {{
    "trait": "",
    "behavior": ""
  }}
]
}}
"""

        print(prompt)
        print("#############################################")

        for j in range(5):
            try:
                difference = chat('chatgpt-4o-latest', prompt)  
                cleaned_difference = difference.replace("```json", "").replace("```", "").strip()
                difference_json = json.loads(cleaned_difference)
                difference1 = difference_json["difference"][0]
                difference2 = difference_json["difference"][1]
                difference3 = difference_json["difference"][2]
                original = difference_json["original_behavior_traits"]

                examples[i]["disturbance"] = [
                    difference1,
                    difference2,
                    difference3,
                    "original_behavior_traits", original
                ]
                break
            except json.JSONDecodeError:
                print("JSON parsing error, retrying")
                continue
            except Exception as e: 
                print(f"An error occurred: {e}")
                continue

        print(difference)
    return examples

def scramble_options(examples):
    for item in examples[1:]:
        opt1 = item["key_behavior"]
        if "disturbance" not in item:
            print("No disturbance data found in example.")
            continue

        opt2 = item["disturbance"][0]["behavior"]
        opt3 = item["disturbance"][1]["behavior"]
        opt4 = item["disturbance"][2]["behavior"]

        options = [opt1, opt2, opt3, opt4]
        correct_option = opt1

        random.shuffle(options)

        options_out_of_order = {
            "a": options[0],
            "b": options[1],
            "c": options[2],
            "d": options[3]
        }

        correct_index = options.index(correct_option)

        item["right_option_index"] = chr(ord('a') + correct_index)  # More concise way to get letter index
        item["options_out_of_order"] = options_out_of_order
        return examples


def generate_disturbance(file_path):
    print(f"Starting disturbance generation for: {file_path}")
    item = load_json(file_path)
    title = item["new_name"]
    meaningful_path = f'/Users/jyxc-dz-0100483/Downloads/work/human_behavior_demo/data_gen/examples_{title}_meaningful.json'

    examples = load_json(meaningful_path)
    if "disturbance" in examples[-1]:
        print(f"Disturbance already exists for {title}. Skipping.")
        print(f"Finished disturbance generation for: {file_path} (skipped)")
        return
    examples = generate_disturbance_run(examples)
    examples=scramble_options(examples)
    save_json(meaningful_path, examples)
    print(f"Finished disturbance generation for: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON file.")
    parser.add_argument("file_path", help="Path to the JSON file.")
    args = parser.parse_args()
    generate_disturbance(args.file_path)