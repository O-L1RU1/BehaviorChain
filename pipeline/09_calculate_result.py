import json
import os
from pathlib import Path
from tqdm import tqdm
import argparse
from pipeline.utils import load_json, save_json  # Assuming utils.py contains load_json and save_json

# Calculate normalized consecutive accuracy for a single example
def consecutive_accuracy_metric_normalized(results):
    """
    Calculates the normalized consecutive accuracy metric.
    Args:
        results (list): A list of 1s and 0s representing correct and incorrect predictions.
    Returns:
        tuple: A tuple containing the normalized consecutive accuracy and the maximum chain accuracy.
    """
    n = len(results)
    max_consecutive_length = n
    consecutive_count = 0
    total_consecutive = 0
    consecutive_count_max = 0
    for r in results:
        if r == 1:
            consecutive_count += 1
            total_consecutive += consecutive_count
            consecutive_count_max = max(consecutive_count_max, consecutive_count)
        else:
            consecutive_count = 0

    max_chain_accuracy = float(consecutive_count_max / float(n))
    cam_normalized = total_consecutive / ((n * (max_consecutive_length + 1)) / 2)
    return cam_normalized, max_chain_accuracy


def evaluate_model(model_name, data_dir):
    """
    Calculate the model's performance on the given dataset.

    Args:
        model_name (str): The name of the model to evaluate.
        data_dir (str): The directory containing the JSON files.
    """
    book = {}
    sums = 0
    lens = 0
    chain_accuracys = 0
    max_chain_accuracys = 0
    accs = 0
    count = 0
    file_paths = [Path(data_dir) / file for file in os.listdir(data_dir) if file.endswith(".json")]

    for file_path in tqdm(file_paths, desc=f"Evaluating {model_name}"):
        try:
            item1 = load_json(file_path) #Load json data using utils function
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error processing {file_path}: {e}")
            continue

        examples = item1["examples"]
        result_list = []
        count += 1

        for item in examples[1:]:
            answer = item.get(model_name, "0")
            char_before_last_paren = ""
            if answer:
                last_paren_index = answer.rfind(')')
                if last_paren_index != -1:
                    char_before_last_paren = answer[last_paren_index - 1]
                else:
                    char_before_last_paren = answer[0]

            result_list.append(1 if char_before_last_paren == item["right_option_index"] else 0)

        item1["avg_accuracy"] = sum(result_list) / len(result_list)
        sums += sum(result_list)
        lens += len(result_list)
        item1["chain_accuracy"], item1["max_chain_accuracy"] = consecutive_accuracy_metric_normalized(result_list)

        accs += item1["avg_accuracy"]
        chain_accuracys += item1["chain_accuracy"]
        max_chain_accuracys += item1["max_chain_accuracy"]

        name = file_path.stem.replace("finally_examples_", "")

        if name not in book:
            book[name] = [{"model": model_name, "avg_accuracy": item1["avg_accuracy"], "normalized_chain_ac": item1["chain_accuracy"], "max_chain_ac": item1["max_chain_accuracy"]}]
        else:
            book[name].append({"model": model_name, "avg_accuracy": item1["avg_accuracy"], "normalized_chain_ac": item1["chain_accuracy"], "max_chain_ac": item1["max_chain_accuracy"]})
        save_json(book, file_path) #save json data using utils function
    avg_acc = accs / count if count else 0
    chain_ac = chain_accuracys / count if count else 0
    max_chain_ac = max_chain_accuracys / count if count else 0

    print(f"model: {model_name}")
    print(f"avg_ac: {avg_acc}")
    print(f"normalized_chain_ac: {chain_ac}")
    print(f"max_chain_ac: {max_chain_ac}")
    print(f"count: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation script")
    parser.add_argument("--model_name", type=str, required=True, help="Model name")
    parser.add_argument("--data_dir", type=str, required=True, help="Data directory")
    args = parser.parse_args()
    evaluate_model(args.model_name, args.data_dir)