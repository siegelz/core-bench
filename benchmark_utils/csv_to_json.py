import pandas as pd
import json
import argparse

def load_and_process_csv(file_path, split=None, capsule_ids=None):
    df = pd.read_csv(file_path)

    # Filter rows where "Include in  Benchmark" is "Y"
    df_filtered = df[df['Include in  Benchmark'] == 'Y']

    # Filter rows where "Ready For Review?" is "Y"
    df_filtered = df_filtered[df_filtered['Ready For Review?'] == 'Y']

    # Filter rows where "Split" is the specified split
    if split is not None:
        df_filtered = df_filtered[df_filtered['Split'] == split]

    # Extract capsule_id from the link
    df_filtered['capsule_id'] = df_filtered['link'].apply(lambda x: f"capsule-{x.split('/')[-3]}")

    # Filter rows where "capsule_id" is in the specified capsule_ids
    if capsule_ids is not None:
        capsule_ids = [f"capsule-{capsule_id}" for capsule_id in capsule_ids]
        df_filtered = df_filtered[df_filtered['capsule_id'].isin(capsule_ids)]

    # Select and rename the relevant columns
    df_filtered = df_filtered[['field', 'language', 'title', 'capsule_id', 'Task Prompt', 'Result (1)', 'Result (2)', 'Result (3)']]
    df_filtered.rename(columns={'title': 'capsule_title', 'Task Prompt': 'task_prompt'}, inplace=True)

    # Validate and fix JSON strings in the results columns
    def validate_and_fix_json(entry):
        try:
            # Attempt to load the JSON string
            parsed_json = json.loads(entry)
            return parsed_json
        except json.JSONDecodeError:
            # If there's an error, return a "SYNTAX ERROR" message
            return "SYNTAX ERROR"

    # Apply validation and fixing to the results columns
    def validate_results(row):
        # +2 to account for the header row and to get the correct row number
        row_number = row.name + 2
        has_error = False

        try:
            row['Result (1)'] = validate_and_fix_json(row['Result (1)'])
            if row['Result (1)'] == "SYNTAX ERROR":
                has_error = True

            row['Result (2)'] = validate_and_fix_json(row['Result (2)'])
            if row['Result (2)'] == "SYNTAX ERROR":
                has_error = True

            row['Result (3)'] = validate_and_fix_json(row['Result (3)'])
            if row['Result (3)'] == "SYNTAX ERROR":
                has_error = True
        except Exception as e:
            has_error = True

        if has_error:
            print(f"SYNTAX ERROR at row {row_number}")
            return None

        return row

    df_filtered = df_filtered.apply(validate_results, axis=1)
    df_filtered = df_filtered.dropna()

    # Create the results list with correctly parsed JSON entries or "SYNTAX ERROR"
    def parse_results(row):
        return [
            row['Result (1)'],
            row['Result (2)'],
            row['Result (3)']
        ]

    df_filtered['results'] = df_filtered.apply(parse_results, axis=1)

    # Select the final columns
    df_final = df_filtered[['field', 'language', 'capsule_title', 'capsule_id', 'task_prompt', 'results']]

    # Convert the final dataframe to a list of dictionaries
    json_list = df_final.to_dict(orient='records')

    # Add the capsule_doi key with an empty value
    for item in json_list:
        item['capsule_doi'] = ''

    return json_list

def save_to_json(data, output_file_path):
    with open(output_file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Parse arguments
parser = argparse.ArgumentParser()

parser.add_argument('--input', help='Input CSV file path', default='capsules.csv')
parser.add_argument('--output', help='Output JSON file path', default='capsules.json')
parser.add_argument('--split', help='Which split to use', default=None, choices=[None, 'Train', 'Test', 'OOD'])
parser.add_argument('--capsule_ids', help='Which capsule IDs to include', default=None, nargs='+')

args = parser.parse_args()

# Specify the input and output file paths
input_file_path = args.input
output_file_path = args.output

# Load, process, and save the data
json_data = load_and_process_csv(input_file_path, args.split, args.capsule_ids)
save_to_json(json_data, output_file_path)

print(f"JSON output saved to {output_file_path}")
print(f"Number of capsules: {len(json_data)}")