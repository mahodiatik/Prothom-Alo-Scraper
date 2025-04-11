import os
import json

def merge_json_files(folder_path, output_file):
    merged_data = []

    for filename in os.listdir('output'):
        if filename.endswith('.json'):
            file_path = os.path.join('output', filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        merged_data.append(data)
                except json.JSONDecodeError as e:
                    print(f"Skipping {filename}: Invalid JSON - {e}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4, ensure_ascii=False)  # <-- key change here
    print(f"Merged {len(merged_data)} items into '{output_file}'")

# Example usage:
merge_json_files('output', 'data.json')
