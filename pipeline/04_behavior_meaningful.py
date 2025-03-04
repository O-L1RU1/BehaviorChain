import json
import re
import argparse
from pipeline.utils import chat, save_json, load_json

def is_behavior_meaningful(examples, character):
    """
    Determines if behaviors are meaningful and reflects character's characteristics or emotions.

    Args:
        examples (list): List of behavior examples.
        character (str): Character's name.

    Returns:
        list: Filtered list of meaningful behavior examples.
    """
    sentences = '\n'.join(f"{i}. {ex['key_behavior']}" for i, ex in enumerate(examples))

    prompt = f"""
Determine whether the following behaviors are trivial actions that do not reflect {character}'s characteristics or emotions.
Return only the indices of all behaviors that do not reflect the character's characteristics or emotions, without any additional numbers.
<behaviors begin>
{sentences}
<behaviors end>
    """

    def get_meaningless_indices():
        text = chat('chatgpt-4o-latest', prompt)
        return list(map(int, re.findall(r'\b\d+\b', text)))

    meaningless_numbers1 = get_meaningless_indices()
    meaningless_numbers2 = get_meaningless_indices()
    meaningless_numbers3 = get_meaningless_indices()

    meaningless_numbers = list(set(meaningless_numbers1) & set(meaningless_numbers2) & set(meaningless_numbers3))

    for i, ex in enumerate(examples):
        ex['meaningful'] = 0 if i in meaningless_numbers else 1

    first_meaningful_index = next((i for i, ex in enumerate(examples) if ex['meaningful'] == 1), len(examples))
    
    new_examples = [examples[first_meaningful_index -1]] if first_meaningful_index > 0 else []

    for i in range(first_meaningful_index, len(examples)):
        if examples[i]['meaningful'] == 1:
            new_examples.append(examples[i])
        elif i + 1 < len(examples):
            examples[i + 1]["new_summary"] = examples[i]["new_summary"].replace(
                f'After this or in response to this, what behavior did {character} take?', '') + examples[i + 1]["new_summary"]

    return new_examples




def get_meaningful(file_path):
    print(f"Starting meaningful behavior filtering for: {file_path}")
    item = load_json(file_path)

    title = item["new_name"]
    examples_path = f'./data_gen/examples_{title}.json'
    meaningful_path = f'./data_gen/examples_{item["new_name"]}_meaningful.json'
    with open(examples_path, 'r') as f:
        examples = json.load(f)
    profile = item["profile"]
    character = profile["Name"]
    examples = is_behavior_meaningful(examples, character)
    save_json(meaningful_path, examples)  # Corrected to save_json
    print(f"Finished meaningful behavior filtering for: {file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON file to filter meaningful behaviors.")
    parser.add_argument("file_path", help="Path to the JSON file.")
    args = parser.parse_args()
    get_meaningful(args.file_path)