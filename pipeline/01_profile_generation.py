from pipeline.utils import chat, save_json, load_json
import json
import argparse

def profile_gen(title, summary):
    prompt = f"""
Please generate the profile of the protagonist (MOST Central figure) in the novel '{title}' in the following format:
{{
  "Name": "Jay Gatsby",
  "Personality Traits": [
    "Charismatic",
    "Mysterious",
    "Obsessive",
    "Romantic",
    "Wealthy",
    "Idealistic"
  ],
  "Motivations and Goals": [
    "To reunite with his former lover, Daisy Buchanan",
    "To achieve a high social status and wealth",
    "To recapture the past and fulfill his ideal vision of life with Daisy"
  ],
  "Significant Background Events": [
    "Born James Gatz to a poor farming family in North Dakota",
    "Changed his name to Jay Gatsby and reinvented himself as a wealthy socialite",
    "Amassed his fortune through questionable means",
    "Became known for his lavish parties at his mansion in West Egg"
  ],
  "Relationships": {{
    "Daisy Buchanan": "Former lover, whom Gatsby is still deeply in love with",
    "Tom Buchanan": "Daisy's husband and Gatsby's rival",
    "Nick Carraway": "Narrator of the story and Gatsby's neighbor and friend",
    "Jordan Baker": "A professional golfer and friend of Daisy, whom Gatsby has a brief romantic interest in",
    "George Wilson": "A mechanic and owner of a garage, indirectly involved in Gatsby's downfall"
  }},
  "Additional Details": {{
    "Occupation": "Businessman with mysterious sources of wealth",
    "Social Status": "Wealthy and influential, but not born into old money",
    "Hobbies": "Throwing extravagant parties, collecting expensive art and cars",
    "Residence": "A grand mansion in West Egg, New York"
  }}
}}

Here is the supplementary material:

############# Novel Introduction and Plot Summary Start #############
{summary}
############# Novel Introduction and Plot Summary End #############

Return the profile in JSON format.
Use The real name of the protagonist instead of "The Narrator."
        """
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            content = chat("gpt-3.5", prompt)
            json_answer = json.loads(content)
            return json_answer
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}. Retrying...")
        except Exception as e:
            print(f"An error occurred: {e}. Retrying...")
        retries += 1
        print(f"Retrying ({retries}/{max_retries})...")
    return None

def profile_gen_for_one(file_path):
    print(f"Starting profile generation for: {file_path}")
    item = load_json(file_path)
    if "profile" in item:
        print(f"Skipping: Profile already exists for {file_path}")
        return item
    title = item["new_name"]
    all_i = int(len(item["all_summary"]) / 2)
    summary = ""
    for i in range(all_i):
        summary += item["all_summary"][i]["chapter_content"]
    profile = profile_gen(title, summary)
    if profile:
        item["profile"] = profile
    save_json(file_path, item)
    print(f"Finished profile generation for: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON file.")
    parser.add_argument("file_path", help="Path to the JSON file.")
    args = parser.parse_args()

    profile_gen_for_one(args.file_path)

