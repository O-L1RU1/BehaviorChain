import json
from pipeline.utils import chat, load_json, save_json
import argparse

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_and_modify_prompt(example):
    new_summary = example.get('new_summary', "")
    key_behavior = example.get('key_behavior', "")

    if len(new_summary) == 0 or len(key_behavior) == 0:
        return example

    character = key_behavior.split(" ")[0]  # Extract character name

    # Extract the relevant portion of the summary
    start_idx = 0
    end_idx = len(new_summary)

    if "After that," in new_summary:
        start_idx = new_summary.index("After that,") + len("After that,")
        relevant_part = new_summary[start_idx:].strip()
    elif len(new_summary.split('.')) == 2:
        example["summary_refined"] = example["new_summary"]
        return example
    else:
        relevant_part = ".".join(new_summary.split('.')[1:])

    # Construct the prompt
    prompt = (
        f"""
<Context Begin>
{relevant_part}
<Context End>

<Behavior Begin>
{key_behavior}
<Behavior End>

Your task is to refine the <Context> according to the following requirements:

1. If the <Context> explicitly or implicitly suggests the active behaviors of the character in the <Behavior> or discloses the result/reactions of others caused by <Behavior>, delete these from <Context>. Any references to the character's emotions, feelings, psychological states, or internal conflicts should be eliminated from <Context>.

2. If <Behavior> includes the character's reaction/response to event/situation/others behavior, then that event/situation/others behavior should to be described intactly and directly in the end of <Context>.

3. If the <Behavior> includes any elements such as contextual conditions or encounters rather than purely active behavior of the character, integrate these elements into the <Context>. Pay attention to the clauses in <Behavior> as it often contain contextual information, but do not include it in <Context> if it happens after the character's behavior. 

4. Output the refined <Context> directly without other note.
"""
    )

    print("#######################")
    print(prompt)

    max_retries = 3
    retry_count = 0
    summary = ""
    while retry_count < max_retries:
        try:
            summary = chat("claude-3-5-sonnet-20241022", prompt)  # Call the chat function
            print("Original Response:", summary)

            if len(summary) > 10:  # Basic check to avoid empty/very short responses
                print("Parsing Successful:", summary)
                break  # Exit the retry loop if successful
        except Exception as e: # Catching a broader exception
            print(f"Error: {e}")
            
        retry_count += 1
        print(f"Retry {retry_count}...")

    summary = summary.replace("<Context>", "").replace("<Context Begin>", "").replace("<Context End>", "").replace("</Context>", "")

    if "After that," in new_summary:
        summary_refined = (
            new_summary[:start_idx] + " " + summary + " " + f"After this or in response to this, what behavior did {character} take?"
        ).strip()
    else:
        summary_refined = (
            ".".join(new_summary.split('.')[:1]) + " " + summary + " " + f"After this or in response to this, what behavior did {character} take?"
        ).strip()

    example["summary_refined"] = summary_refined

    return example


def get_context_refined(file_path):
    print(f"Starting context refinement for: {file_path}")
    item = load_json(file_path)
    title = item["new_name"]
    meaningful_path = f'/Users/jyxc-dz-0100483/Downloads/work/human_behavior_demo/data_gen/examples_{title}_meaningful.json'
    examples = load_json(meaningful_path)

    if "summary_refined" in examples[0]:
        print(f"summary_refined already exists for {title}")
        print(f"Finished summary refinement for: {file_path} (skipped)")
        return
    updated_examples = []
    for example in examples:
        updated_examples.append(extract_and_modify_prompt(example))
    save_json(meaningful_path, updated_examples)
    print(f"Finished context refinement for: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON file.")
    parser.add_argument("file_path", help="Path to the JSON file.")
    args = parser.parse_args()
    get_context_refined(args.file_path)