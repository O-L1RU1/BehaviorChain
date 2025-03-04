import json
import re
import os
import time
import argparse
from tqdm import tqdm
from pipeline.utils import chat,load_json, save_json,get_last_number


def get_the_first_key_behavior(prompt):
    max_retries = 5
    retries = 0
    while retries < max_retries:
        answer = chat('claude-3-5-sonnet-20240620', prompt)
        pattern = r'{.*?\}'
        matches = re.findall(pattern, answer, re.DOTALL)
        if matches:
            content = matches[0]
            try:
                json_answer = json.loads(content)
                return json_answer
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                retries += 1
                time.sleep(60)
                continue
        else:
            print("No matches found. Retrying...")
            retries += 1
            time.sleep(60)

def get_key_behaviors(file_path):
    item=json.load(open(file_path))
    title = item["new_name"]
    if os.path.exists(f'./data_gen/examples_{title}.json'):
        print("title exists")
        return
    profile = item["profile"]
    character = profile["Name"]
    parts = item["parts"]
    if len(parts) < 10:
        return
    if len(parts) > 25:
        len_parts = 25
    else:
        len_parts = len(parts)

    examples = []
    prompt = f"""
You are an expert in Narrative Analysis and Character Behavior Extract.
Please extract the MOST KEY behavior of {character} FROM <Paragraphs>. 
The behavior should have a significant impact on the development of the storyline.  reflect character characteristics or emotions.
Ensure that the KEY behavior is objective statements and state the behavior clearly and do not use any vague expressions. 
DO NOT add subjective interpretations and inference about the character's behaviors. ONLY describe the KEY behavior itself. DO NOT mention the result in the KEY behavior.
Ensure use your own words instead of quoting the original text. 
DO NOT repeat or imitate <Previous Key Behavior>. 

Please use your own words instead of quoting the original.
The KEY behavior should have a significant impact on the development of the storyline, the characterization of the characters, and the expression of the theme.
Ensure that the key behavior is objective statements and be careful to state the behavior clearly and do not use any vague expressions. 
DO NOT add subjective interpretations and inference about the character's behaviors. Only describe the behavior itself. 
The format of your response should be {{"key_behavior": ""}}. 

<Paragraphs BEGIN>
{parts[0]}
<Paragraphs END>
If the behavior of {character} cannot be extracted, output "" ONLY.
        """
    
    json_answer=get_the_first_key_behavior(prompt)
    json_answer["original"] = parts[0]
    examples.append(json_answer)
    marge_part = parts[:1]
    examples = examples[:1]

#生成接下来的行为
    for i in range(1, len_parts):
        if len(examples) > 20 or i < 10 and i - len(examples) > 5 or i - len(examples) >= 10:
            break
        prompt = f"""
You are an expert in Narrative Analysis and Character Behavior Extract.
Below, I will provide you with <Previous Paragraphs>, <Previous Key Behavior> extracted from <Previous Paragraphs> and  <Current Paragraphs>. 

Please summary the scene change and plot development detailly and naturally after the <Previous Key Behavior> according to the <Previous Paragraphs> and <Current Paragraphs> I give you. The summary should start with "{examples[-1]['key_behavior']} After that, ".

After the summary, you should extract the MOST KEY behavior of {character} FROM <Current Paragraphs>, describe in more than 10 words.
The behavior should be a non-meaningless behavior taken spontaneously by {character}.
The behavior should have a significant impact on the development of the storyline.  reflect character characteristics or emotions.
Ensure that the behavior is objective statements and state the behavior clearly and do not use any vague expressions. 
DO NOT add subjective interpretations and inference about the character's behaviors. ONLY describe the behavior itself. DO NOT mention the result in the behavior.
Ensure use your own words instead of quoting the original text. 
DO NOT repeat or imitate <Previous Key Behavior>. 

Please provide a REVISED summary of the scene change and plot development that occurred before the behavior you extracted from <Current Paragraphs>, making sure not to reveal any information about the behavior. Delete the behavior and subsequent plots, and keep only the plots before the behavior.
The REVISED summary should end with "After this or in response to this, what behavior did {character} take?"

<Previous Paragraphs BEGIN>
{marge_part[-1]}
<Previous Paragraphs END>

<Previous Key Behavior BEGIN>
{examples[-1]['key_behavior']}
<Previous Key Behavior END>

<Current Paragraphs BEGIN>
{parts[i]}
<Current Paragraphs END>

The format of your response should be {{"summary": "","key_behavior":"","new_summary":""}}. 
Ensure that the behavior you extract is taken by {character} at this moment, rather than behavior of others or past behavior (in <Paragraphs>, {character}probable in the first person).
If the behavior of {character} cannot be extracted, output "None" ONLY.
""" 
        max_retries = 2
        retries = 0
        label_none = 0
        while retries < max_retries:
            retries += 1
            pattern = r'{.*?\}'
            answer = chat('claude-3-5-sonnet-20240620', prompt)
            if "None" in answer or "none" in answer or "NONE" in answer:
                marge_part[-1] += "\n" + parts[i]
                label_none = 1
                break
            else:
                matches = re.findall(pattern, answer, re.DOTALL)
            if matches:
                content = matches[0]
                try:
                    json_answer = json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    continue
                break
            else:
                print("No matches found. Retrying...")
                time.sleep(60)
        if label_none == 1:
            continue

        sentence1 = json_answer['key_behavior']
        sentence2 = examples[-1]['key_behavior']
        prompt_sim = f"""
Please determine whether the following two behaviors refer to the same behavior:
Behavior 1: {sentence1}
Behavior 2: {sentence2}
If there is a strong possibility that the two behaviors refer to the same behavior, please output 1; otherwise, output 0, Make sure you give me 0/1.
        """
        label = 0
        sims = 0
        for i_3 in range(3):
            print(f"----------simility check begin {i_3}----------")
            if sims==0:
                gpt_sim=chat('gpt-3.5',prompt_sim)
                sim = get_last_number(gpt_sim)
                if sim==2:
                    continue
                sims+=(1-sim)
            print(f"----------simility check end {i_3}----------")
            if not (sims==0):
                label=1
                break

        if label == 0:
            label_none = 0
            max_retries = 2
            retry = 0
            while retry < max_retries:
                retry += 1
                pattern = r'{.*?\}'
                answer = chat('claude-3-5-sonnet-20240620', prompt)
                if "None" in answer or "none" in answer or "NONE" in answer:
                    marge_part[-1] += "\n" + parts[i]
                    label_none = 1
                    break
                matches = re.findall(pattern, answer, re.DOTALL)
                if matches:
                    content = matches[0]
                    try:
                        json_answer = json.loads(content)
                        break
                    except json.JSONDecodeError as e:
                        print(f"JSON Decode Error: {e}")
                        continue
                    except Exception as e:
                        print(f"Error: {e}")
                        continue
            if label_none == 1:
                continue
            sentence1 = json_answer['key_behavior']
            sentence2 = examples[-1]['key_behavior']
            prompt_sim = f"""
Please determine whether the following two behaviors refer to the same behavior:
Behavior 1: {sentence1}
Behavior 2: {sentence2}
If there is a strong possibility that the two behaviors refer to the same behavior, please output 1; otherwise, output 0, Make sure you give me 0/1.
        """
            for i_3 in range(3):
                print(f"----------simility check begin {i_3}----------")
                if sims==0:
                    gpt_sim=chat('gpt-3.5',prompt_sim)
                    sim = get_last_number(gpt_sim)
                    if sim==2:
                        continue
                    sims+=(1-sim)
                print(f"----------simility check end {i_3}----------")
                if not (sims==0):
                    label=1
                    break

        if label == 0:
            marge_part[-1] += "\n" + parts[i]
            continue
        json_answer["original"] = parts[i]
        marge_part.append(parts[i])
        examples.append(json_answer)
    if not os.path.exists(f'./data_gen'):
        os.mkdir(f'./data_gen')
    save_json(f'./data_gen/examples_{title}.json', examples)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON file.")
    parser.add_argument("file_path", help="Path to the JSON file.")
    args = parser.parse_args()

    get_key_behaviors(args.file_path)