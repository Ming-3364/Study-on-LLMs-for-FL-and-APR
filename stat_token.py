import tiktoken
import os
import json
from tqdm import tqdm

def get_token_for_prompt(prompt, model="gpt-4o-mini"):
    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = encoding.encode(prompt)
    token_count = len(tokens)
    return token_count

defects4j_output_dir = 'output/defects4j'
condefects_output_dir = 'output/condefects'

def get_token_for_dir(dir):
    total_tokens = 0
    prompt_files = []
    for root, _, files in os.walk(dir):
        prompt_files = [file for file in files if file.endswith(".prompts.json")]
        query_results_files = [file for file in files if file.endswith(".query_results.json")]
    for file in prompt_files:
        id = file.split('.prompts.json')[0]
        query_results_file = id + '.query_results.json'
        if query_results_file not in query_results_files:
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                prompt = json.load(f)
                total_tokens += get_token_for_prompt(json.dumps(prompt))
    return total_tokens

print(get_token_for_dir(defects4j_output_dir))
print(get_token_for_dir(condefects_output_dir))