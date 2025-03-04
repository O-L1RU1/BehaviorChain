import requests
import json

url = "https://xxxxxxx/v1/chat/completions"
api_key = "Bearer ak-xxxxxxx"
headers = {
    "Content-Type": "application/json",
    "Authorization": api_key
}


def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)
def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_last_number(text):
    match = re.search(r'\d+$', text.strip())
    if match:
        return int(match.group())
    else:
        return 2





def chat(model, prompt):
    data = {
        "model": model,
        "stream": True,
        "temperature": 1.0,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, json=data, headers=headers, stream=True)

    words = []
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')

                if decoded_line == "data: [DONE]":
                    continue

                try:
                    decoded_line = json.loads(decoded_line[6:])

                    if 'choices' in decoded_line and len(decoded_line['choices']) > 0:
                        delta = decoded_line['choices'][0].get('delta', {})

                        if 'content' in delta:
                            words.append(delta['content'])
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                except Exception as e:
                    print(f"Response Processing Error: {e}")
    else:
        print(f"Request Failed, Status Code: {response.status_code}")

    result = "".join(words)
    print(result)
    return result