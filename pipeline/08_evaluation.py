import random
import tqdm
import argparse
import requests
import time
from loguru import logger
import tiktoken

from pipeline.utils import load_json,save_json


url = "https://xxxxxxx/v1/chat/completions"
api_key = "Bearer ak-xxxxxxx"

enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(enc.encode(text))

def truncate_message(text, max_tokens):
    tokens = enc.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[-max_tokens:]
    return enc.decode(tokens)

max_tokens = 16300

available_proxy_models = ["gpt-3.5","gpt-4o","gpt-4-0613", "gpt-4-1106-preview", "gpt-4o-mini-2024-07-18", "gpt-4o-2024-11-20",
        "claude-3-5-sonnet-20241022", "glm-4-plus", "abab7-preview-chat", "chatgpt-4o-latest",
        "Doubao-pro-32k", "ERNIE-Bot-4", "hunyuan-pro", "yi-lightning","qwen-plus-latest","qwen-max-latest","deepseek-chat","qwen-plus-2024-11-27","qwen-plus-latest","claude-3-5-haiku-20241022","deepseek-r1","deepseek-v3"]

class ChatAgent:
    def __init__(self, model_name, ip=None, port=None):
        if model_name in available_proxy_models:
            self.url = url
        else:
            self.url = f"http://{ip}:{port}/v1/chat/completions"
        self.header = {
                'Content-Type': 'application/json',
                "Authorization": api_key
            }
        self.model_name = model_name

    def chat(self, prompt: str, retry=5):
        if retry == 0:
            return "sorry,i cant'answer"
        data = {
        "model": self.model_name,
        # "stream": True,
        "messages": [{"role": "user", "content": prompt}],  
        # "max_tokens": 30,
    }
        response = requests.post(self.url, headers=self.header, json=data)

        if response.status_code != 200:
            logger.warning(response.text)
            time.sleep(10*(6-retry))
            return self.chat(prompt, retry-1)

        res = response.json()
        response=res['choices'][0]['message']['content']
        print(response)
        return response



def moved_prompt(profile, prompt_to_model):
    """
    Replaces character names in the prompt with randomly generated names.

    Args:
        profile (dict): A dictionary containing character relationships.
        prompt_to_model (str): The prompt string to be modified.

    Returns:
        str: The modified prompt with replaced names.
    """
    names = list(profile['Relationships'].keys())
    character = profile['Name']
    names.append(character)

    # Create empty sets for first, last, and second names
    first_names = set()
    last_names = set()
    second_names = set()

    # Iterate through each name in the list
    for name in names:
        # Split the name into individual words
        words = name.split()
        if len(words) == 2:
            first_names.add(words[0])
            last_names.add(words[1])
        elif len(words) == 1:
            first_names.add(words[0])
        elif len(words) > 2:
            first_names.add(words[0])
            second_names.add(words[1])
            last_names.add(words[-1])
        else:
            print(f"Warning: Name '{name}' does not have exactly two words.")

    # Create new sets for new first, last, and second names
    new_first_names = set()
    new_last_names = set()
    new_second_names = set()

    # Generate new first, last, and second names
    new_first_names_list = [
        'Alex', 'Sam', 'Taylor', 'Jordan', 'Casey', 'Morgan', 'Riley', 'Jamie', 'Drew', 'Jesse',
        'Skyler', 'Quinn', 'Blake', 'Kerry', 'Adrian',
        'Cameron', 'Devon', 'Finley', 'Harley', 'Marley',
        'Peyton', 'Reese', 'Sidney', 'Terry', 'Tracy',
        'Charlie', 'Dallas', 'Emery', 'Hayden', 'Jody',
        'Kendall', 'Leslie', 'Mackenzie', 'Pat', 'Regan',
        'Shannon', 'Stevie', 'Toby', 'Valerie', 'Wesley'
    ]
    new_second_names_list = new_first_names_list[:]  # Create a copy to avoid modifying the original
    new_last_names_list = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

    # Randomly assign new first, second, and last names
    first_name_mapping = {}
    second_name_mapping = {}
    last_name_mapping = {}

    # Map first names
    for first_name in first_names:
        if new_first_names_list:
            new_first_name = random.choice(new_first_names_list)
            new_first_names_list.remove(new_first_name)
            first_name_mapping[first_name] = new_first_name
            new_first_names.add(new_first_name)

    # Map second names
    for second_name in second_names:
        if new_second_names_list:
            new_second_name = random.choice(new_second_names_list)
            new_second_names_list.remove(new_second_name)
            second_name_mapping[second_name] = new_second_name
            new_second_names.add(new_second_name)

    # Map last names
    for last_name in last_names:
        if new_last_names_list:
            new_last_name = random.choice(new_last_names_list)
            new_last_names_list.remove(new_last_name)
            last_name_mapping[last_name] = new_last_name
            new_last_names.add(new_last_name)

    # Replace old names with new names in the prompt
    for old_name, new_name in first_name_mapping.items():
        prompt_to_model = prompt_to_model.replace(old_name, new_name)

    for old_name, new_name in second_name_mapping.items():
        prompt_to_model = prompt_to_model.replace(old_name, new_name)

    for old_name, new_name in last_name_mapping.items():
        prompt_to_model = prompt_to_model.replace(old_name, new_name)

    return prompt_to_model




def run_evaluation_multi_choice(model, file_path, model_name): #Added type parameter
 
    item1 = load_json(file_path)
    examples = item1["examples"]

    # Skip evaluation if the model has already generated answers
    if model_name in examples[-1] and examples[-1][f"{model_name}"] not in ["sorry,i cant'answer", ""]:
        print("Answers already generated.")
        return

    summary_l = ""
    summary = item1["summary"]
    max_index = item1["max_index"]

    # Handle potential discrepancy in chapter and summary counts
    chapter_summary_diff = item1["chapters_len"] - item1["summary_len"]
    for item in summary[:max_index - chapter_summary_diff]:
        chapter_content = item["chapter_content"]
        # Remove the first "Summary" and preceding content
        summary_index = chapter_content.find("Summary")
        if summary_index != -1:
            chapter_content = chapter_content[summary_index + 7:].strip()
        summary_l += chapter_content + "\n"

    profile = item1['profile']
    character = profile['Name']

    prompt = f"""
<Profile BEGIN>
{profile}
<Profile END>

<Previously on the fiction BEGIN>
{summary_l}
<Previously on the fiction END>
    """

    for item in tqdm.tqdm(item1["examples"][1:]):
        summary_s = item['summary_refined']
        prompt += summary_s + "\n"

        options_out_of_order = item["options_out_of_order"]
        options = f"""
Please choose the option you think is most appropriate from a), b), c), d) and reply with only the option code.

a) {options_out_of_order["a"]}
b) {options_out_of_order["b"]}
c) {options_out_of_order["c"]}
d) {options_out_of_order["d"]}
        """


        prompt_to_model = prompt + options
        prompt_to_model = moved_prompt(profile, prompt_to_model)

        # Remove specific prompt segment
        prompt = prompt.replace(f'After this or in response to this, what behavior did {character} take?', '')

        answer = model.chat(truncate_message(prompt_to_model, max_tokens))
        item[f"{model_name}_multi_choice"] = answer

    # Save the updated examples
    save_json(item1, file_path)




def run_evaluation_generation(model, file_path, model_name): #Added type parameter
 
    item1 = load_json(file_path)
    examples = item1["examples"]

    # Skip evaluation if the model has already generated answers
    if model_name in examples[-1] and examples[-1][f"{model_name}"] not in ["sorry,i cant'answer", ""]:
        print("Answers already generated.")
        return

    summary_l = ""
    summary = item1["summary"]
    max_index = item1["max_index"]

    # Handle potential discrepancy in chapter and summary counts
    chapter_summary_diff = item1["chapters_len"] - item1["summary_len"]
    for item in summary[:max_index - chapter_summary_diff]:
        chapter_content = item["chapter_content"]
        # Remove the first "Summary" and preceding content
        summary_index = chapter_content.find("Summary")
        if summary_index != -1:
            chapter_content = chapter_content[summary_index + 7:].strip()
        summary_l += chapter_content + "\n"

    profile = item1['profile']
    character = profile['Name']

    prompt = f"""
<Profile BEGIN>
{profile}
<Profile END>

<Previously on the fiction BEGIN>
{summary_l}
<Previously on the fiction END>
    """

    for item in tqdm.tqdm(item1["examples"][1:]):
        summary_s = item['summary_refined']
        prompt += summary_s + "\n"
        prompt_to_model=prompt
        prompt_to_model = moved_prompt(profile, prompt_to_model)

        # Remove specific prompt segment
        prompt = prompt.replace(f'After this or in response to this, what behavior did {character} take?', '')

        answer = model.chat(truncate_message(prompt_to_model, max_tokens))
        item[f"{model_name}_generation"]=answer

    save_json(item1, file_path)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save counts to a file.")
    parser.add_argument("--file_path", type=str, required=True, help="model for evaluation")
    parser.add_argument("--model_name", type=str, required=True, help="model for evaluation")
    parser.add_argument("--task_type", type=str, required=True)
    parser.add_argument("--ip", type=str, default=None, help="model IP address")
    parser.add_argument("--port", type=str, default=None, help="model Port number")

    args = parser.parse_args()
   

    
    model = ChatAgent(args.model_name,args.ip, args.port)
    if args.task_type == "multi_choice":
        run_evaluation_multi_choice(model, args.file_path, args.model_name)
    elif args.task_type == "generation":
        run_evaluation_generation(model, args.file_path, args.model_name)