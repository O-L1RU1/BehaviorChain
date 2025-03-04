import re
from collections import Counter
import math
import argparse
from pipeline.utils import load_json,save_json


# Function to extract names 
def extract_entity_names(profile):
    entity_name = profile["Name"]  
    return entity_name

# Function to split strings 
def split_string(string):
    segments = re.split(r'(?<=[.?!])', string)
    segments = [seg for seg in segments if seg.strip()]
    return segments

# Function to count entity occurrences in sentences
def count_entity_sentences(string, entity_representative_name):
    segments = split_string(string)
    count = sum(entity_representative_name in segment for segment in segments)
    return count, segments

# Function to find the section with the most entity occurrences
def find_most_entity_section(contents_between_headings, entity_representative_name):
    counts = [count_entity_sentences(content, entity_representative_name)[0] for content in contents_between_headings]
    length = len(counts)
    start_index = length - length // 2  # Adjusted start index
    last_third_counts = counts[start_index:]
    sums = [(i + start_index, last_third_counts[i]) for i in range(len(last_third_counts))]

    # Determine number of chapters based on threshold
    if max(sums, key=lambda x: x[1])[1] > 25:  # Threshold remains for logic
        chapter_count = 1
    else:
        chapter_count = 2

    max_index, _ = max(sums, key=lambda x: x[1])
    return max_index, chapter_count

# Function to divide content by entity occurrences
def divide_content_by_entity_occurrences(content, n, entity_representative_name):
    entity_count, segments = count_entity_sentences(content, entity_representative_name)
    print(entity_count)
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    sentences_per_part = entity_count / n
    sentences_per_part = math.floor(sentences_per_part)

    # Minimum sentences per part
    if sentences_per_part == 0:
        sentences_per_part = 1

    # Maximum sentences per part (adjusted for generic entity)
    if entity_representative_name != "I":
        if sentences_per_part > 2:
            sentences_per_part = 2
    else:
        if sentences_per_part > 5:
            sentences_per_part = 5

    print("Target occurrences per part:", sentences_per_part)

    parts = []
    current_part = []
    current_count = 0

    for segment in segments:
        current_part.append(segment)
        current_count += entity_representative_name in segment

        if current_count >= sentences_per_part:
            parts.append(''.join(current_part))
            current_part = []
            current_count = 0

    if current_part:
        parts.append(''.join(current_part))

    return parts

# Main function for processing content
def process_content(contents_between_headings, entity_name):
    entity_first_name = entity_name.split()[0]
    entity_last_name = entity_name.split()[-1]

    cut_1_2 = int(len(contents_between_headings) / 2)

    first_name_count = [count_entity_sentences(content, entity_first_name)[0] for content in contents_between_headings]
    first_name_count = first_name_count[cut_1_2:]

    last_name_count = [count_entity_sentences(content, entity_last_name)[0] for content in contents_between_headings]
    last_name_count = last_name_count[cut_1_2:]

    i_count = [content.count("I") for content in contents_between_headings]
    i_count = i_count[cut_1_2:]

    first_name_count_max_value = max(first_name_count)
    last_name_count_max_value = max(last_name_count)

    first_name_count_sum = sum(first_name_count)
    last_name_count_sum = sum(last_name_count)

    if first_name_count_sum > last_name_count_sum:
        entity_representative_name = entity_first_name
    else:
        entity_representative_name = entity_last_name

    if first_name_count_max_value < 15 and last_name_count_max_value < 15:
        entity_representative_name = "I"

    print(f"Occurrences of first name: {first_name_count}")
    print(f"Occurrences of last name: {last_name_count}")
    print("Occurrences of 'I':", i_count)
    print("Representative entity name:", entity_representative_name)

    result = find_most_entity_section(contents_between_headings, entity_representative_name)
    max_index, chapter_count = result

    if chapter_count == 1:
        content = contents_between_headings[max_index]
    else:
        if max_index + 1 < len(contents_between_headings):
            content = contents_between_headings[max_index] + '\n\n' + contents_between_headings[max_index + 1]
        else:
            content = contents_between_headings[max_index]

    print("Number of chapters:", chapter_count)
    parts = divide_content_by_entity_occurrences(content, 15, entity_representative_name)
    print("Number of parts after division:", len(parts))

    if entity_representative_name == "I":
        entity_representative_name = entity_name  # Keep original entity name if "I" was used

    return parts, entity_representative_name, max_index

def devide_and_select(file_path):
    print(f"Starting divide and select for: {file_path}")
    item = load_json(file_path)
    profile = item["profile"]
    character = profile["Name"]
    chapters = item["chapters"]
    result = process_content(chapters, character)
    parts, representative_name, max_index = result
    item["parts"] = parts
    item["representative_name"] = representative_name
    item["max_index"] = max_index
    save_json(file_path, item)
    print(f"Finished divide and select for: {file_path}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON file.")
    parser.add_argument("file_path", help="Path to the JSON file.")
    args = parser.parse_args()

    devide_and_select(args.file_path)