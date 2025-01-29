import json
import os
from .llm.LLMManager import LLMManager
from tqdm import tqdm
import random
from venn import venn, pseudovenn
import matplotlib.pyplot as plt
import csv
import pandas as pd
from typing import Literal
import re

# plt.rcParams['font.family'] = 'Times New Roman'

def get_prompt_fl_1(method_src):
    prompt = f"""
source code:
{method_src}

There is a bug in the above code, please help me locate it.

Please output **only one integer**: the line number of the buggy code (The code starts from line 1). Do not provide any explanations or additional content.
"""
    return prompt

def get_prompt_fl_2(method_src, test_stack):
    prompt = f"""
source code:
{method_src}

stack trace:
{test_stack}

There is a bug in the above code, please help me locate it by considering the stack trace.

Please output **only one integer**: the line number of the buggy code (The code starts from line 1). Do not provide any explanations or additional content.
"""
    return prompt

def get_prompt_fl_3(method_src, test_stack, test_assert):
    prompt = f"""
source code:
{method_src}

stack trace:
{test_stack}

failure assertion code:
{test_assert}

There is a bug in the above code, please help me locate it by considering the stack trace information and failure assertion code.

Please output **only one integer**: the line number of the buggy code (The code starts from line 1). Do not provide any explanations or additional content.
"""
    return prompt

def get_prompt_fl_4(method_src):
    prompt = f"""
source code:
{method_src}

There is a bug in the above code, please help me locate it.

Output **only** the exact buggy statement, with no line numbers, explanations, or additional content. Your response should contain just the buggy code line. Do not include ```java or ``` markers in the response.
"""
    return prompt

def get_prompt_fl_5(method_src, test_stack):
    prompt = f"""
source code:
{method_src}

stack trace:
{test_stack}

There is a bug in the above code, please help me locate it by considering the stack trace.

Output **only** the exact buggy statement, with no line numbers, explanations, or additional content. Your response should contain just the buggy code line. Do not include ```java or ``` markers in the response.
"""
    return prompt

def get_prompt_fl_6(method_src, test_stack, test_assert):
    prompt = f"""
source code:
{method_src}

stack trace:
{test_stack}

failure assertion code:
{test_assert}

There is a bug in the above code, please help me locate it by considering the stack trace information and failure assertion code.

Output **only** the exact buggy statement, with no line numbers, explanations, or additional content. Your response should contain just the buggy code line. Do not include ```java or ``` markers in the response.
"""
    return prompt

def get_prompt_apr_1(method_src, buggy_lines_in_method):
    prompt = f"""
{method_src}

There is a bug in line {buggy_lines_in_method} of the code, please help me fix it.

Please return the **complete corrected method**. Do not skip or omit any part of the code. Do not include ```java or ``` markers in the response.
"""
    return prompt

def get_prompt_apr_2(method_src, buggy_statement):
    prompt = f"""
{method_src}

There is a bug in {buggy_statement} , please help me fix it. 

Please return the **complete corrected method**. Do not skip or omit any part of the code. Do not include ```java or ``` markers in the response.
"""
    return prompt

def get_prompt_apr_3(buggy_method_src_endswith_buggy_statement):
    prompt = f"""
{buggy_method_src_endswith_buggy_statement}

There is a bug in the last statement, please help me fix it.

Return the code **only from the method declaration to the fixed statement**, without completing or adding additional code. Do not modify anything beyond fixing the bug, and do not complete the `if` statement or other unfinished parts. Do not include ```java or ``` markers in the response.
"""
    return prompt

def get_prompt_apr_4(method_src, buggy_lines_in_method):
    prompt = f"""
{method_src}

There is a bug in line {buggy_lines_in_method} of the code, please help me fix it.

Please return the results in a strict JSON format as described below. Please follow these instructions carefully:
1. Your output must include each repaired line's number (`line_number`) and the corresponding fixed code statement (`fixed_statement`).
2. The output format must be a valid JSON array, where each element represents one repaired line, with the following structure:
   - `"line_number"`: The line number of the buggy code that was repaired (integer).
   - `"fixed_statement"`: The repaired statement for that specific line (string).

3. The result must strictly follow this format:
[
    {{
        "line_number": int,
        "fixed_statement": "string"
    }},
    {{
        "line_number": int,
        "fixed_statement": "string"
    }}
]
4. The repaired statement in "fixed_statement" must replace the corresponding line in the buggy code.
5. You must NOT include any additional explanation or description in your response. Only return the JSON array. Do not include ```json or ``` markers in the response.
"""
    return prompt

def get_prompt_apr_5(method_src, buggy_statement):
    prompt = f"""
{method_src}

There is a bug in {buggy_statement} , please help me fix it. 

Please return the results in a strict JSON format as described below. Please follow these instructions carefully:
1. Your output must include each repaired line's number (`line_number`) and the corresponding fixed code statement (`fixed_statement`).
2. The output format must be a valid JSON array, where each element represents one repaired line, with the following structure:
   - `"line_number"`: The line number of the buggy code that was repaired (integer).
   - `"fixed_statement"`: The repaired statement for that specific line (string).

3. The result must strictly follow this format:
[
    {{
        "line_number": int,
        "fixed_statement": "string"
    }},
    {{
        "line_number": int,
        "fixed_statement": "string"
    }}
]
4. The repaired statement in "fixed_statement" must replace the corresponding line in the buggy code.
5. You must NOT include any additional explanation or description in your response. Only return the JSON array. Do not include ```json or ``` markers in the response.
"""
    return prompt

def get_prompt_apr_6(buggy_method_src_endswith_buggy_statement):
    prompt = f"""
{buggy_method_src_endswith_buggy_statement}

There is a bug in the last statement, please help me fix it.

Please return the results in a strict JSON format as described below. Please follow these instructions carefully:
1. Your output must include each repaired line's number (`line_number`) and the corresponding fixed code statement (`fixed_statement`).
2. The output format must be a valid JSON array, where each element represents one repaired line, with the following structure:
   - `"line_number"`: The line number of the buggy code that was repaired (integer).
   - `"fixed_statement"`: The repaired statement for that specific line (string).

3. The result must strictly follow this format:
[
    {{
        "line_number": int,
        "fixed_statement": "string"
    }},
    {{
        "line_number": int,
        "fixed_statement": "string"
    }}
]
4. The repaired statement in "fixed_statement" must replace the corresponding line in the buggy code.
5. You must NOT include any additional explanation or description in your response. Only return the JSON array. Do not include ```json or ``` markers in the response.
"""
    return prompt

def get_prompt(method_src, test_stack, test_assert, buggy_lines_in_method, buggy_statement, buggy_method_src_endswith_buggy_statement):
    prompts = {}
    prompts["prompt_fl_1"] = get_prompt_fl_1(method_src)
    if test_stack != "None":
        prompts["prompt_fl_2"] = get_prompt_fl_2(method_src, test_stack)
    if test_stack != "None" and test_assert != "None":
        prompts["prompt_fl_3"] = get_prompt_fl_3(method_src, test_stack, test_assert)
    prompts["prompt_fl_4"] = get_prompt_fl_4(method_src)
    if test_stack != "None":
        prompts["prompt_fl_5"] = get_prompt_fl_5(method_src, test_stack)
    if test_stack != "None" and test_assert != "None":
        prompts["prompt_fl_6"] = get_prompt_fl_6(method_src, test_stack, test_assert)

    prompts["prompt_apr_1"] = get_prompt_apr_1(method_src, buggy_lines_in_method)
    prompts["prompt_apr_2"] = get_prompt_apr_2(method_src, buggy_statement)
    prompts["prompt_apr_3"] = get_prompt_apr_3(buggy_method_src_endswith_buggy_statement)
    prompts["prompt_apr_4"] = get_prompt_apr_4(method_src, buggy_lines_in_method)
    prompts["prompt_apr_5"] = get_prompt_apr_5(method_src, buggy_statement)
    prompts["prompt_apr_6"] = get_prompt_apr_6(buggy_method_src_endswith_buggy_statement)

    return prompts

def chk_get_prompt(buggy_method_src, test_stack, test_assert, buggy_lines_in_method, buggy_statements, buggy_method_src_endswith_buggy_statement):
    if buggy_method_src is None or test_stack is None or test_assert is None \
        or buggy_lines_in_method is None or buggy_statements is None \
        or buggy_method_src_endswith_buggy_statement is None:
        return None
                
    prompts = get_prompt(buggy_method_src, test_stack, test_assert, buggy_lines_in_method, buggy_statements, buggy_method_src_endswith_buggy_statement)
    return prompts

def output_prompts_txt(txt_file, prompts):
    with open(txt_file, 'w', encoding='utf-8') as file:
        for key, value in prompts.items():
            file.write(f"\n================== {key} ==================\n")
            file.write(value)

def output_json(json_file, data):
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def output_bug_info(txt_file, bug_info):
    with open(txt_file, 'w', encoding='utf-8') as file:
        for key, value in bug_info.items():
            file.write(f"\n================== {key} ==================\n")
            file.write(str(value))

def get_bug_info_content(bug_info):
    buggy_file = bug_info["buggy_file"]
    buggy_method = bug_info["buggy_method"]
    buggy_method_src = bug_info["buggy_method_src"]
    test_stack = bug_info["test_stack"]
    test_assert = bug_info["test_assert"]
    buggy_lines_in_method = bug_info["buggy_lines_in_method"]
    buggy_statements = bug_info["buggy_statements"]
    buggy_method_src_endswith_buggy_statement = bug_info["buggy_method_src_endswith_buggy_statement"]
    return buggy_file, buggy_method, buggy_method_src, test_stack, test_assert, buggy_lines_in_method, buggy_statements, buggy_method_src_endswith_buggy_statement

def get_id_by_tuple(t):
    return "_".join(map(str, t))

def get_tuple_by_id(id):
    return tuple(id.split("_"))

def get_id_list(id_tuple_list):
    id_list = []
    for t in id_tuple_list:
        id = get_id_by_tuple(t)
        id_list.append(id)
    return id_list

def get_prompts_list_json_file(output_dir, file_id):
    prompts_list_json_file = os.path.join(output_dir, f"{file_id}.prompts.json")
    return prompts_list_json_file

def get_bug_info_list_json_file(output_dir, file_id):
    bug_info_list_json_file = os.path.join(output_dir, f"{file_id}.bug_info.json")
    return bug_info_list_json_file

def get_query_results_list_json_file(output_dir, file_id):
    """
    list: [{prompt_id: {llm_id: query_result}}]
    """
    query_results_list_json_file = os.path.join(output_dir, f"{file_id}.query_results.json")
    return query_results_list_json_file

def get_check_results_fl_json_file(output_dir, file_id):
    check_results_fl_json_file = os.path.join(output_dir, f"{file_id}.check_results_fl.json")
    return check_results_fl_json_file

def get_check_results_apr_json_file(output_dir, file_id):
    check_results_apr_json_file = os.path.join(output_dir, f"{file_id}.check_results_apr.json")
    return check_results_apr_json_file

def query_all_llm(prompt):
    llm_manager = LLMManager()
    results = llm_manager.query_all_llm(prompt)
    return results

def replace_lines_in_file(file_path, start_line, end_line, replacement_text):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            lines = file.readlines()

        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            raise ValueError(f"Invalid line range [{start_line}, {end_line}] specified.")
        
        lines[start_line - 1] = replacement_text
        lines[start_line:end_line] = [""] * (end_line - start_line)

        with open(file_path, 'w', encoding='utf-8', errors='replace') as file:
            file.writelines(lines)
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return -1

def replace_lines_in_files(replace_dict):
    try:
        for file_path, info_list in replace_dict.items():
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                lines = file.readlines()
            for (start_line, end_line, res) in info_list:
                if start_line < 1 or end_line > len(lines) or start_line > end_line:
                    raise ValueError(f"Invalid line range [{start_line}, {end_line}] specified.")
                
                lines[start_line - 1] = res
                lines[start_line:end_line] = [""] * (end_line - start_line)

            with open(file_path, 'w', encoding='utf-8', errors='replace') as file:
                file.writelines(lines)
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return -1
    
def query_llm_for_file(work_dir, file_id):
    prompts_list_json_file = get_prompts_list_json_file(work_dir, file_id)
    
    query_results_list = []
    with open(prompts_list_json_file, 'r', encoding='utf-8') as file:
        prompts_list = json.load(file)
        for i, prompts in enumerate(prompts_list):
            query_results = {}
            for prompt_id, prompt in tqdm(prompts.items(), desc='Querying llm with prompt...', leave=False):
                try:
                    res = query_all_llm(prompt)
                except Exception as e:
                    print(f"Querying llm for {prompts_list_json_file} {prompt_id} error: {str(e)}")
                    return None
                query_results[prompt_id] = res
            query_results_list.append(query_results)
        query_results_list_json_file = get_query_results_list_json_file(work_dir, file_id)
        output_json(query_results_list_json_file, query_results_list)
        return query_results_list

def filter_for_query_llm(work_dir, id_list):
    filtered_id_list = []
    for id in id_list:
        prompts_list_json_file = get_prompts_list_json_file(work_dir, id)
        query_results_list_json_file = get_query_results_list_json_file(work_dir, id)
        if os.path.exists(prompts_list_json_file) \
           and not os.path.exists(query_results_list_json_file):
            filtered_id_list.append(id)
    return filtered_id_list

def query_llm(work_dir, id_list):
    print("Querying llm...")

    filtered_id_list = filter_for_query_llm(work_dir, id_list)
    
    # FIXME: for testing
    # id_list = random.sample(id_list, min(10, len(id_list)))

    max_consecutive_errors = 5
    cur_consecutive_errors = 0
    for id in tqdm(filtered_id_list, desc='Querying llm...'):
        query_results_list = query_llm_for_file(work_dir, id)
        if query_results_list is None:
            cur_consecutive_errors += 1
        else:
            cur_consecutive_errors = 0
        if cur_consecutive_errors >= max_consecutive_errors:
            assert False, f"Query llm: Consecutive errors exceed {max_consecutive_errors}."

def filter_for_fl_and_apr(work_dir, id_list):
    filtered_id_list = []
    for id in id_list:
        bug_info_list_json_file = get_bug_info_list_json_file(work_dir, id)
        query_results_list_json_file = get_query_results_list_json_file(work_dir, id)
        check_results_fl_json_file = get_check_results_fl_json_file(work_dir, id)
        check_results_apr_json_file = get_check_results_apr_json_file(work_dir, id)
        if os.path.exists(bug_info_list_json_file) \
           and os.path.exists(query_results_list_json_file) \
            and (not os.path.exists(check_results_fl_json_file) or not os.path.exists(check_results_apr_json_file)):
            filtered_id_list.append(id)
    return filtered_id_list
    
def check_query_results_fl_for_file(prompt_dir, file_id):
    bug_info_list_json_file = get_bug_info_list_json_file(prompt_dir, file_id)
    query_results_list_json_file = get_query_results_list_json_file(prompt_dir, file_id)
    
    with open(bug_info_list_json_file, 'r', encoding='utf-8') as file:
        bug_info_list = json.load(file)
    with open(query_results_list_json_file, 'r', encoding='utf-8') as file:
        query_results_list = json.load(file)
    
    check_results_list = []
    overall_status = {}
    for i, bug_info in enumerate(bug_info_list):
        buggy_lines_in_method = bug_info["buggy_lines_in_method"]
        query_results = query_results_list[i]
        check_results = {}
        for prompt_id, query_result in query_results.items():
            if not prompt_id.startswith("prompt_fl"):
                continue
            check_results[prompt_id] = {}
            for llm_id, res in query_result.items():
                status = ""
                if prompt_id in ['prompt_fl_1', 'prompt_fl_2', 'prompt_fl_3']:
                    try:
                        line_number = int(res)
                        if line_number not in buggy_lines_in_method:
                            status = "Incorrect"
                        else:
                            status = "Correct"
                    except:
                        status = "Failed"
                elif prompt_id in ['prompt_fl_4', 'prompt_fl_5', 'prompt_fl_6']:
                    try:
                        buggy_statement = str(res)
                        for s in bug_info['buggy_statements']:
                            if buggy_statement.strip() == s.strip():
                                status = "Correct"
                                break
                        if status == "Correct":
                            status = "Correct"
                        else:
                            status = "Incorrect"
                    except:
                        status = "Failed"
                else:
                    assert False, f"prompt_id invalid: {prompt_id}"
                check_results[prompt_id][llm_id] = status
        check_results_list.append(check_results)
    prompt_id_list = ['prompt_fl_1', 'prompt_fl_2', 'prompt_fl_3', 'prompt_fl_4', 'prompt_fl_5', 'prompt_fl_6']
    llm_id_list = LLMManager().get_llm_id_list()
    for prompt_id in prompt_id_list:
        overall_status[prompt_id] = {}
        for llm_id in llm_id_list:
            status_set = set()
            for i, bug_info in enumerate(bug_info_list):
                if prompt_id not in check_results_list[i]:
                    continue
                status = check_results_list[i][prompt_id][llm_id]
                status_set.add(status)
            if len(status_set) == 1 and "Correct" in status_set:
                overall_status[prompt_id][llm_id] = "Correct"
            elif "Failed" in status_set:
                overall_status[prompt_id][llm_id] = "Failed"
            elif "Incorrect" in status_set:
                overall_status[prompt_id][llm_id] = "Incorrect"
            else:
                overall_status[prompt_id][llm_id] = "Unknown"
    check_results_fl = {'overall_status': overall_status, 'check_results_list': check_results_list, }
    check_results_fl_json_file = get_check_results_fl_json_file(prompt_dir, file_id)
    output_json(check_results_fl_json_file, check_results_fl)
    return check_results_fl

def check_query_results_fl(work_dir, id_list):
    print("Checking fl...")

    filtered_id_list = filter_for_fl_and_apr(work_dir, id_list)

    for id in tqdm(filtered_id_list, desc='Checking fl...'):
        check_results_fl = check_query_results_fl_for_file(work_dir, id)
        if check_results_fl is None:
            continue

def get_manual_check_apr_status_file(work_dir, id, prompt_id, llm_id):
    manual_check_apr_status_file = os.path.join(work_dir, f"{id}.{prompt_id}.{llm_id}.apr_status.txt")
    return manual_check_apr_status_file

def prepare_manual_check(id, prompt_id, llm_id, work_dir):
    manual_check_apr_status_file = get_manual_check_apr_status_file(work_dir, id, prompt_id, llm_id)
    # prepare correct result
    d4j_framework = os.path.join(work_dir, "d4j_frameworks", id)
    d4j_patch = os.path.join(work_dir, "d4j_patches", id)
    
def prepare_llm_res_for_apr_manual_check(work_dir, id, prompt_id, llm_id):
    res = ""
    # prepare llm result
    query_results_list_json_file = get_query_results_list_json_file(work_dir, id)
    with open(query_results_list_json_file, 'r', encoding='utf-8') as file:
        query_results_list = json.load(file)
        res += f"Query results\n"
        for query_results in query_results_list:
            res = query_results[prompt_id][llm_id]
            res += f"======================================\n"
            res += f"{res}\n"
    return res

def collect_apr_status_for_manual_check(work_dir, id_list, output_file):
    apr_status_json = {}
    for id in id_list:
        check_results_apr_json_file = get_check_results_apr_json_file(work_dir, id)
        if not os.path.exists(check_results_apr_json_file):
            continue
        with open(check_results_apr_json_file, 'r', encoding='utf-8') as file:
            check_results_apr = json.load(file)
        overall_status_apr = check_results_apr['overall_status']
        for llm_id in LLMManager().get_llm_id_list():
            for prompt_id in ['prompt_apr_1', 'prompt_apr_2', 'prompt_apr_3', 'prompt_apr_4', 'prompt_apr_5', 'prompt_apr_6']:
                status = overall_status_apr[prompt_id][llm_id]
                standard_status = None
                if id not in apr_status_json:
                    apr_status_json[id] = {}
                if prompt_id not in apr_status_json[id]:
                    apr_status_json[id][prompt_id] = {}
                if status == "Pass all tests":
                    standard_status = "PassAllTests"
                elif status in ["Fail some tests", "Timeout", "Compile failed"]:
                    standard_status = "Incorrect"
                else:
                    standard_status = "Failed"

                apr_status_json[id][prompt_id][llm_id] = standard_status

    sorted_apr_status_json = {k: apr_status_json[k] for k in sorted(apr_status_json)}
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(sorted_apr_status_json, file, indent=4)

def stat_check_results_for_files(work_dir, id_list):
    fl_stat = {}
    apr_stat = {}
    prompt_id_list = ['prompt_fl_1', 'prompt_fl_2', 'prompt_fl_3', 'prompt_fl_4', 'prompt_fl_5', 'prompt_fl_6', 'prompt_apr_1', 'prompt_apr_2', 'prompt_apr_3', 'prompt_apr_4', 'prompt_apr_5', 'prompt_apr_6']
    llm_id_list = LLMManager().get_llm_id_list()
    for prompt_id in prompt_id_list:
        if prompt_id.startswith("prompt_fl"):
            fl_stat[prompt_id] = {}
            for llm_id in llm_id_list:
                fl_stat[prompt_id][llm_id] = {}
        else:
            apr_stat[prompt_id] = {}
            for llm_id in llm_id_list:
                apr_stat[prompt_id][llm_id] = {}
    
    for id in id_list:
        check_results_fl_json_file = get_check_results_fl_json_file(work_dir, id)
        check_results_apr_json_file = get_check_results_apr_json_file(work_dir, id)
        if not os.path.exists(check_results_fl_json_file) or not os.path.exists(check_results_apr_json_file):
            continue
        with open(check_results_fl_json_file, 'r', encoding='utf-8') as file:
            check_results_fl = json.load(file)
        with open(check_results_apr_json_file, 'r', encoding='utf-8') as file:
            check_results_apr = json.load(file)
        overall_status_fl = check_results_fl['overall_status']
        overall_status_apr = check_results_apr['overall_status']
        for prompt_id in overall_status_fl:
            for llm_id in overall_status_fl[prompt_id]:
                status = overall_status_fl[prompt_id][llm_id]
                if status not in fl_stat[prompt_id][llm_id]:
                    fl_stat[prompt_id][llm_id][status] = 0
                fl_stat[prompt_id][llm_id][status] += 1
        for prompt_id in overall_status_apr:
            for llm_id in overall_status_apr[prompt_id]:
                status = overall_status_apr[prompt_id][llm_id]
                if status not in apr_stat[prompt_id][llm_id]:
                    apr_stat[prompt_id][llm_id][status] = 0
                apr_stat[prompt_id][llm_id][status] += 1
    return fl_stat, apr_stat

def get_localized_bugs(work_dir, id_list):
    localized_bugs = {}
    for llm_id in LLMManager().get_llm_id_list():
        localized_bugs[llm_id] = set()
    for id in id_list:
        check_results_fl_json_file = get_check_results_fl_json_file(work_dir, id)
        if not os.path.exists(check_results_fl_json_file):
            continue
        with open(check_results_fl_json_file, 'r', encoding='utf-8') as file:
            check_results_fl = json.load(file)
        overall_status_fl = check_results_fl['overall_status']
        for llm_id in LLMManager().get_llm_id_list():
            for prompt_id in overall_status_fl:
                status = overall_status_fl[prompt_id][llm_id]
                if status == "Correct":
                    localized_bugs[llm_id].add(id)
    return localized_bugs

def get_fixed_bugs(manual_check_file):
    fixed_bugs = {}
    for llm_id in LLMManager().get_llm_id_list():
        fixed_bugs[llm_id] = set()
    with open(manual_check_file, 'r', encoding='utf-8') as file:
        manual_check = json.load(file)
    for id in manual_check:
        for prompt_id in manual_check[id]:
            for llm_id in manual_check[id][prompt_id]:
                status = manual_check[id][prompt_id][llm_id]
                if status == "Correct":
                    fixed_bugs[llm_id].add(id)
    return fixed_bugs
    # for id in id_list:
    #     check_results_apr_json_file = get_check_results_apr_json_file(work_dir, id)
    #     if not os.path.exists(check_results_apr_json_file):
    #         continue
    #     with open(check_results_apr_json_file, 'r', encoding='utf-8') as file:
    #         check_results_apr = json.load(file)
    #     overall_status_apr = check_results_apr['overall_status']
    #     for llm_id in LLMManager().get_llm_id_list():
    #         for prompt_id in overall_status_apr:
    #             status = overall_status_apr[prompt_id][llm_id]
    #             if status == "Pass all tests":
    #                 fixed_bugs[llm_id].add(id)
    # return fixed_bugs

def get_localized_bugs_by_llm_prompt(work_dir, id_list):
    localized_bugs_by_llm_prompt = {}
    for llm_id in LLMManager().get_llm_id_list():
        localized_bugs_by_llm_prompt[llm_id] = {}
        for prompt_id in ['prompt_fl_1', 'prompt_fl_2', 'prompt_fl_3', 'prompt_fl_4', 'prompt_fl_5', 'prompt_fl_6']:
            localized_bugs_by_llm_prompt[llm_id][prompt_id] = set()
    for id in id_list:
        check_results_fl_json_file = get_check_results_fl_json_file(work_dir, id)
        if not os.path.exists(check_results_fl_json_file):
            continue
        with open(check_results_fl_json_file, 'r', encoding='utf-8') as file:
            check_results_fl = json.load(file)
        overall_status_fl = check_results_fl['overall_status']
        for llm_id in LLMManager().get_llm_id_list():
            for prompt_id in ['prompt_fl_1', 'prompt_fl_2', 'prompt_fl_3', 'prompt_fl_4', 'prompt_fl_5', 'prompt_fl_6']:
                status = overall_status_fl[prompt_id][llm_id]
                if status == "Correct":
                    localized_bugs_by_llm_prompt[llm_id][prompt_id].add(id)
    return localized_bugs_by_llm_prompt

def get_fixed_bugs_by_llm_prompt(manual_check_file):
    fixed_bugs_by_llm_prompt = {}
    for llm_id in LLMManager().get_llm_id_list():
        fixed_bugs_by_llm_prompt[llm_id] = {}
        for prompt_id in ['prompt_apr_1', 'prompt_apr_2', 'prompt_apr_3', 'prompt_apr_4', 'prompt_apr_5', 'prompt_apr_6']:
            fixed_bugs_by_llm_prompt[llm_id][prompt_id] = set()
    with open(manual_check_file, 'r', encoding='utf-8') as file:
        manual_check = json.load(file)
    for id in manual_check:
        for prompt_id in manual_check[id]:
            for llm_id in manual_check[id][prompt_id]:
                status = manual_check[id][prompt_id][llm_id]
                if status == "Correct":
                    fixed_bugs_by_llm_prompt[llm_id][prompt_id].add(id)
    return fixed_bugs_by_llm_prompt
    # for id in id_list:
    #     check_results_apr_json_file = get_check_results_apr_json_file(work_dir, id)
    #     if not os.path.exists(check_results_apr_json_file):
    #         continue
    #     with open(check_results_apr_json_file, 'r', encoding='utf-8') as file:
    #         check_results_apr = json.load(file)
    #     overall_status_apr = check_results_apr['overall_status']
    #     for llm_id in LLMManager().get_llm_id_list():
    #         for prompt_id in ['prompt_apr_1', 'prompt_apr_2', 'prompt_apr_3', 'prompt_apr_4', 'prompt_apr_5', 'prompt_apr_6']:
    #             status = overall_status_apr[prompt_id][llm_id]
    #             if status == "Pass all tests":
    #                 fixed_bugs_by_llm_prompt[llm_id][prompt_id].add(id)
    # return fixed_bugs_by_llm_prompt

def replace_prompt_id(prompt_id):
    match = re.match(r"prompt_(\w+)_(\d+)", prompt_id)
    if match:
        type_code = match.group(1).upper()
        number = match.group(2)
        new_prompt_id = f"{type_code} Prompt{number}"
        return new_prompt_id
    assert False, f"Invalid prompt_id: {prompt_id}"

def replace_keys_in_dict_venn6(original_dict):
    new_dict = {}
    for key, value in original_dict.items():
        new_key = replace_prompt_id(key)
        new_dict[new_key] = value
    return new_dict

def replace_llm_id(llm_id):
    new_llm_id = None
    if llm_id == "ernie-3.5-128k":
        new_llm_id = "Ernie-3.5"
    elif llm_id == "qwen-turbo":
        new_llm_id = "Qwen-turbo"
    elif llm_id == "doubao-pro-4k":
        new_llm_id = "Doubao-pro"
    elif llm_id == "gpt-4o-mini":
        new_llm_id = "GPT-4o-M"
    elif llm_id == "deepseek-chat":
        new_llm_id = "Deepseek-V3"
    else:
        assert False, f"Invalid llm_id: {llm_id}"
    return new_llm_id
def replace_keys_in_dict_venn3(original_dict):
    new_dict = {}
    for key, value in original_dict.items():
        new_key = replace_llm_id(key)
        new_dict[new_key] = value
    return new_dict

def create_venn_svg(sets_dict, title, output_file):
    if len(sets_dict) == 6:
        # pseudovenn(sets_dict)
        # print(sets_dict)
        sets_dict = replace_keys_in_dict_venn6(sets_dict)
        # pseudovenn(sets_dict, legend_loc=2, fontsize=16, alpha=.6)
        pseudovenn(sets_dict, legend_loc=(-0.1,0.7), fontsize=16, alpha=.6)
    else:
        sets_dict = replace_keys_in_dict_venn3(sets_dict)
        venn(sets_dict, legend_loc=2,fontsize=16,alpha=.6)
    plt.tight_layout()
    plt.savefig(output_file, format='svg')
    # exit(-1)

def write_tsv(file_path, header, rows):
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)

def get_fl_status_list():
    return ["Correct", "Incorrect", "Failed", "Unknown"]

def get_apr_status_list():
    # return ["Pass all tests", "Fail some tests", "Timeout", "Compile failed", "Failed"]
    return ["Correct", "Incorrect", "Failed"]

def get_result_classification_fl(work_dir, id_list):
    result_classification = {}

    for id in id_list:
        check_results_fl_json_file = get_check_results_fl_json_file(work_dir, id)
        if not os.path.exists(check_results_fl_json_file):
            continue
        with open(check_results_fl_json_file, 'r', encoding='utf-8') as file:
            check_results_fl = json.load(file)
        overall_status_fl = check_results_fl['overall_status']

        for prompt_id in overall_status_fl:
            for llm_id in overall_status_fl[prompt_id]:
                status = overall_status_fl[prompt_id][llm_id]

                if prompt_id not in result_classification:
                    result_classification[prompt_id] = {}
                if llm_id not in result_classification[prompt_id]:
                    result_classification[prompt_id][llm_id] = {}
                if status not in result_classification[prompt_id][llm_id]:
                    result_classification[prompt_id][llm_id][status] = []
                
                result_classification[prompt_id][llm_id][status].append(id)
    return result_classification

def get_result_classification_apr(manual_check_file):
    result_classification = {}
    with open(manual_check_file, 'r', encoding='utf-8') as file:
        manual_check = json.load(file)
    for id in manual_check:
        for prompt_id in manual_check[id]:
            for llm_id in manual_check[id][prompt_id]:
                status = manual_check[id][prompt_id][llm_id]
                if prompt_id not in result_classification:
                    result_classification[prompt_id] = {}
                if llm_id not in result_classification[prompt_id]:
                    result_classification[prompt_id][llm_id] = {}
                if status not in result_classification[prompt_id][llm_id]:
                    result_classification[prompt_id][llm_id][status] = []
                result_classification[prompt_id][llm_id][status].append(id)
    return result_classification

    # for id in id_list:
    #     check_results_apr_json_file = get_check_results_apr_json_file(work_dir, id)
    #     if not os.path.exists(check_results_apr_json_file):
    #         continue
    #     with open(check_results_apr_json_file, 'r', encoding='utf-8') as file:
    #         check_results_apr = json.load(file)
    #     overall_status_apr = check_results_apr['overall_status']

    #     for prompt_id in overall_status_apr:
    #         for llm_id in overall_status_apr[prompt_id]:
    #             status = overall_status_apr[prompt_id][llm_id]

    #             if prompt_id not in result_classification:
    #                 result_classification[prompt_id] = {}
    #             if llm_id not in result_classification[prompt_id]:
    #                 result_classification[prompt_id][llm_id] = {}
    #             if status not in result_classification[prompt_id][llm_id]:
    #                 result_classification[prompt_id][llm_id][status] = []
                
    #             result_classification[prompt_id][llm_id][status].append(id)
    # return result_classification

def merge_result_classification(result_classification_list):
    merged_result_classification = {}
    for result_classification in result_classification_list:
        for prompt_id in result_classification.keys():
            for llm_id in result_classification[prompt_id].keys():
                for status in result_classification[prompt_id][llm_id].keys():
                    if prompt_id not in merged_result_classification:
                        merged_result_classification[prompt_id] = {}
                    if llm_id not in merged_result_classification[prompt_id]:
                        merged_result_classification[prompt_id][llm_id] = {}
                    if status not in merged_result_classification[prompt_id][llm_id]:
                        merged_result_classification[prompt_id][llm_id][status] = []
                    merged_result_classification[prompt_id][llm_id][status].extend(result_classification[prompt_id][llm_id][status])
    return merged_result_classification



def write_result_classification_fl_tsv(result_classification, output_file):
    status_list = get_fl_status_list()
    header = ["prompt_id", "llm_id"]
    header.extend(status_list)
    header.append("total")
    rows = []
    for prompt_id in result_classification.keys():
        for llm_id in result_classification[prompt_id].keys():
            row = [prompt_id, llm_id]
            total = 0
            for status in get_fl_status_list():
                count = None
                if status not in result_classification[prompt_id][llm_id]:
                    count = 0
                else:
                    count = len(result_classification[prompt_id][llm_id][status])
                total += count
                row.append(count)
            row.append(total)
            rows.append(row)
    write_tsv(output_file, header, rows)

def write_result_classification_apr_tsv(result_classification, output_file):
    status_list = get_apr_status_list()
    header = ["prompt_id", "llm_id"]
    header.extend(status_list)
    header.append("total")
    rows = []
    for prompt_id in result_classification.keys():
        for llm_id in result_classification[prompt_id].keys():
            row = [prompt_id, llm_id]
            total = 0
            for status in get_apr_status_list():
                count = None
                if status not in result_classification[prompt_id][llm_id]:
                    count = 0
                else:
                    count = len(result_classification[prompt_id][llm_id][status])
                total += count
                row.append(count)
            row.append(total)
            rows.append(row)
    write_tsv(output_file, header, rows)

# def generate_pie_charts_from_tsv(tsv_file, output_file, task:Literal["fl", "apr"]):
#     # Read the TSV file into a DataFrame
#     data = pd.read_csv(tsv_file, sep='\t')

#     # Group data by 'prompt_id'
#     grouped_data = data.groupby('prompt_id')

#     # Create a single figure to hold all pie charts
#     fig, axes = plt.subplots(nrows=len(grouped_data), ncols=grouped_data.size().max(), figsize=(20, len(grouped_data) * 6))

#     # Iterate through each group to generate pie charts
#     for row_index, (prompt_id, group) in enumerate(grouped_data):
#         for col_index, (_, row) in enumerate(group.iterrows()):
#             if task == "fl":
#                 labels = ['Correct', 'Incorrect', 'Failed', 'Unknown']
#                 values = [row['Correct'], row['Incorrect'], row['Failed'], row['Unknown']]
#             else:
#                 labels = ['Pass all tests', 'Fail some tests', 'Compile failed', 'Failed']
#                 values = [row['Pass all tests'], row['Fail some tests'], row['Compile failed'], row['Failed']]
            
#             # Skip rows where all values are zero
#             if sum(values) == 0:
#                 continue

#             # Filter out zero values and corresponding labels
#             filtered_labels = [label for label, value in zip(labels, values) if value > 0]
#             filtered_values = [value for value in values if value > 0]

#             # Create the pie chart in the corresponding subplot
#             ax = axes[row_index, col_index] if len(grouped_data) > 1 else axes
#             wedges, texts, autotexts = ax.pie(filtered_values, labels=filtered_labels, autopct='%1.1f%%', startangle=90)
#             ax.set_title(f"{row['prompt_id']} - {row['llm_id']}")
#             ax.legend(wedges, filtered_labels, loc="upper right", bbox_to_anchor=(1.1, 1.05), prop={'size': 8})
            
#             # Adjust layout to prevent text overlap
#             plt.tight_layout(pad=3.0)

#     # Save the entire figure as an SVG file for better clarity
#     fig.savefig(output_file, format='svg')
#     plt.close(fig)

def write_localized_bugs_by_different_prompts_tsv(work_dir, id_list, output_file):
    result_classification = get_result_classification_fl(work_dir, id_list)
    status_list = get_fl_status_list()
    header = ["prompt"]
    llm_id_list = LLMManager().get_llm_id_list()
    header.extend(llm_id_list)
    rows = []
    for prompt_id in result_classification.keys():
        row = [prompt_id]
        for llm_id in llm_id_list:
            correct = 0
            if "Correct" in result_classification[prompt_id][llm_id]:
                correct = len(result_classification[prompt_id][llm_id]["Correct"])
            row.append(correct)
        rows.append(row)
    
    write_tsv(output_file, header, rows)

def write_fixed_bugs_by_different_prompts_tsv(manual_check_file, output_file):
    result_classification = get_result_classification_apr(manual_check_file)
    status_list = get_apr_status_list()
    header = ["prompt"]
    llm_id_list = LLMManager().get_llm_id_list()
    header.extend(llm_id_list)
    rows = []
    for prompt_id in result_classification.keys():
        row = [prompt_id]
        for llm_id in llm_id_list:
            correct = 0
            if "Correct" in result_classification[prompt_id][llm_id]:
                correct = len(result_classification[prompt_id][llm_id]["Correct"])
            row.append(correct)
        rows.append(row)
    
    write_tsv(output_file, header, rows)

def create_venn_of_uniquely_located_bugs_by_different_prompts(work_dir, id_list, output_file):
    result_classification = get_result_classification_fl(work_dir, id_list)
    status_list = get_fl_status_list()
    llm_id_list = LLMManager().get_llm_id_list()
    for llm_id in llm_id_list:
        sets_dict = {}
        for prompt_id in result_classification.keys():
            sets_dict[prompt_id] = set()
            if "Correct" in result_classification[prompt_id][llm_id]:
                sets_dict[prompt_id] = set(result_classification[prompt_id][llm_id]["Correct"])
        title = f"Uniquely located bugs by {llm_id}"
        output_file = f"{output_file}_{llm_id}.svg"
        create_venn_svg(sets_dict, title, output_file)

def create_venn_of_uniquely_results_by_different_prompts(result_classification, output_file_prefix, key_word: Literal["fl", "apr"]):
    # print(result_classification)
    status_list = get_apr_status_list()
    llm_id_list = LLMManager().get_llm_id_list()
    for llm_id in llm_id_list:
        sets_dict = {}
        for prompt_id in result_classification.keys():
            sets_dict[prompt_id] = set()
            check_status = "Correct"
            if check_status in result_classification[prompt_id][llm_id]:
                sets_dict[prompt_id] = set(result_classification[prompt_id][llm_id][check_status])
        title = f"Uniquely {key_word} bugs by {llm_id}"
        output_file = f"{output_file_prefix}_{llm_id}.svg"
        print(output_file)
        for prompt_id in sets_dict.keys():
            print(prompt_id, len(sets_dict[prompt_id]))
        create_venn_svg(sets_dict, title, output_file)

def get_d4j_bug_type_classification(bug_type):
    if bug_type.startswith("condBlock"):
        return "Conditional Block"
    elif bug_type.startswith("exp"):
        return "Expression Fix"
    elif bug_type.startswith("wraps") or bug_type.startswith("unwrap"):
        return "Wraps-with"
    elif bug_type == "singleLine":
        return "Single Line"
    elif bug_type.startswith("wrong"):
        return "Wrong Reference"
    elif bug_type.startswith("missNullCheck"):
        return "Missing Null-Check"
    elif bug_type == "copyPaste":
        return "Copy/Paste"
    elif bug_type == "constChange":
        return "Constant Change"
    elif bug_type == "codeMove":
        return "Code Moving"
    else:
        return "Others"

def get_all_d4j_bug_types():
    return ["Conditional Block", "Expression Fix", "Wraps-with", "Single Line", "Wrong Reference", 
    "Missing Null-Check", "Copy/Paste", "Constant Change", "Code Moving", "Others"]


def get_d4j_bug_type():
    bugs_json = "defects4j-bugs.json"
    file_path = os.path.join(os.path.dirname(__file__), bugs_json)
    bug_type_dict = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        bugs = json.load(file)
        for bug in bugs:
            project_id = bug["project"]
            bug_id = bug["bugId"]
            bug_type = bug["repairPatterns"][0]
            bug_type = get_d4j_bug_type_classification(bug_type)
            id = get_id_by_tuple((project_id, bug_id))
            bug_type_dict[id] = bug_type
    return bug_type_dict

def get_bug_type_percentage_in_bugs(bug_list):
    bug_type_dict = get_d4j_bug_type()
    bug_type_count = {}
    for bt in get_all_d4j_bug_types():
        bug_type_count[bt] = 0
    filtered_bug_list = []
    for bug in bug_list:
        if bug not in bug_type_dict:
            continue
        filtered_bug_list.append(bug)
        bug_type = bug_type_dict[bug]
        bug_type_count[bug_type] += 1
    total = len(filtered_bug_list)
    bug_type_percentage = {}
    for bt in get_all_d4j_bug_types():
        if total == 0:
            bug_type_percentage[bt] = 0
        else:
            bug_type_percentage[bt] = bug_type_count[bt] / total
    return bug_type_percentage

def get_bug_type_percentage_in_bugs_by_llm_prompt(bugs_by_llm_prompt):
    bug_type_percentage_by_llm_prompt = {}
    for llm_id in LLMManager().get_llm_id_list():
        for prompt_id in bugs_by_llm_prompt[llm_id]:
            bug_list = bugs_by_llm_prompt[llm_id][prompt_id]
            bug_type_percentage = get_bug_type_percentage_in_bugs(bug_list)
            bug_type_percentage_by_llm_prompt[(llm_id, prompt_id)] = bug_type_percentage
    return bug_type_percentage_by_llm_prompt

def get_bug_type_percentage_in_localized_bugs(work_dir, id_list):
    localized_bugs_by_llm_prompt = get_localized_bugs_by_llm_prompt(work_dir, id_list)
    bug_type_percentage_by_llm_prompt = get_bug_type_percentage_in_bugs_by_llm_prompt(localized_bugs_by_llm_prompt)
    return bug_type_percentage_by_llm_prompt

def get_bug_type_percentage_in_fixed_bugs(manual_check_file):
    fixed_bugs_by_llm_prompt = get_fixed_bugs_by_llm_prompt(manual_check_file)
    bug_type_percentage_by_llm_prompt = get_bug_type_percentage_in_bugs_by_llm_prompt(fixed_bugs_by_llm_prompt)
    return bug_type_percentage_by_llm_prompt

def write_bug_type_percentage_in_bugs_tsv(bug_type_percentage, output_file):
    header = ["llm_id", "prompt"]
    bug_types = get_all_d4j_bug_types()
    header.extend(bug_types)
    rows = []
    for (llm_id, prompt_id) in bug_type_percentage.keys():
        row = [replace_llm_id(llm_id), replace_prompt_id(prompt_id)]
        bug_type_percentage_dict = bug_type_percentage[(llm_id, prompt_id)]
        for bt in bug_types:
            row.append(bug_type_percentage_dict[bt])
        
        rows.append(row)
    write_tsv(output_file, header, rows)



    