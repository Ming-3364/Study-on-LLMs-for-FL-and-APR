import os
import re
import json
from util.parser.java_parser import JavaParser
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from typing import Literal
import csv

def get_defects4j_projects(defects4j_framework):
    projects = []
    projects_path = os.path.join(defects4j_framework, 'projects')
    for project in os.listdir(projects_path):
        project_dir = os.path.join(projects_path, project)
        patches_dir = os.path.join(project_dir, 'patches')
        if os.path.isdir(project_dir) and os.path.exists(patches_dir):
            projects.append(project)
    return sorted(projects)

def get_defects4j_bugs(defects4j_framework, project_id):
    bugs = []
    patches_dir = os.path.join(defects4j_framework, 'projects', project_id, 'patches')
    for patch_file in os.listdir(patches_dir):
        if patch_file.endswith('.src.patch'):
            bug_id = int(patch_file.split('.src.patch')[0])
            bugs.append(bug_id)
    return sorted(bugs)

def get_defects4j_bugs(defects4j_framework, project_id):
    bugs = []
    active_bugs = os.path.join(defects4j_framework, 'projects', project_id, 'active-bugs.csv')
    with open(active_bugs, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            bugs.append(int(row[0]))
    return sorted(bugs)

def get_defects4j_project_bug_ids(project_id, bug_id):
    return f"{project_id}-{bug_id}"

def get_work_dir(checkout_dir, project_id, bug_id, version: Literal["fixed", "buggy"]):
    return os.path.join(checkout_dir, project_id, f"{project_id}-{bug_id}-{version}")

def analyze_patch_modified_lines(patch_file_path):
    '''
    deleted: fixed, added: buggy
    '''
    modified_files_lines = {
        'deleted': {},
        'added': {}
    }
    with open(patch_file_path, 'r', errors='replace') as f:
        cur_old_file = None
        cur_new_file = None
        cur_old_line = None
        cur_new_line = None
        for line in f:

            file_match = re.match(r'--- (\S+)', line)
            if file_match:
                cur_old_file = file_match.group(1)
                if cur_old_file.startswith('a/'):
                    cur_old_file = cur_old_file[2:]
                modified_files_lines['deleted'][cur_old_file] = []
                continue

            file_match = re.match(r'\+\+\+ (\S+)', line)
            if file_match:
                cur_new_file = file_match.group(1)
                if cur_new_file.startswith('b/'):
                    cur_new_file = cur_new_file[2:]
                modified_files_lines['added'][cur_new_file] = []
                continue

            hunk_match = re.match(r'^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@', line)
            if hunk_match:
                cur_old_line = int(hunk_match.group(1))
                cur_new_line = int(hunk_match.group(3))
                continue

            if line.startswith('-') and not line.startswith('---'):
                modified_files_lines['deleted'][cur_old_file].append(cur_old_line)
                cur_old_line += 1

            elif line.startswith('+') and not line.startswith('+++'):
                modified_files_lines['added'][cur_new_file].append(cur_new_line)
                cur_new_line += 1

            elif line.startswith(' '):
                cur_old_line += 1
                cur_new_line += 1

    return modified_files_lines

def parse_patch_in_defects4j(defects4j_framework):
    file_path = os.path.join(defects4j_framework, 'all_modified_files_lines.json')
    if os.path.exists(file_path):
        print(f"Loading all modified files and lines in Defects4J from {file_path}...")
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            all_modified_files_lines = json.load(file)
            return all_modified_files_lines
    print(f"Parsing patches in Defects4J ({defects4j_framework})...")
    all_modified_files_lines = {}      # {project_bug_id: {file_path: [line_number]}}
    projects = get_defects4j_projects(defects4j_framework)
    projects_path = os.path.join(defects4j_framework, 'projects')
    for project_id in projects:
        bugs = get_defects4j_bugs(defects4j_framework, project_id)
        patches_dir = os.path.join(projects_path, project_id, 'patches')
        for bug_id in bugs:
            patch_file_path = os.path.join(patches_dir, f"{bug_id}.src.patch")
            if not os.path.exists(patch_file_path):
                print(f"\tPatch file not found: {patch_file_path}")
                continue
            modified_files_lines = analyze_patch_modified_lines(patch_file_path)
            project_bug_id = f"{project_id}-{bug_id}"
            all_modified_files_lines[project_bug_id] = modified_files_lines
    with open(file_path, 'w', encoding='utf-8', errors='replace') as file:
        json.dump(all_modified_files_lines, file, indent=4)
    return all_modified_files_lines

def get_modifed_methods_in_defects4j_project(modified_files_lines, project_id, bug_id, work_dir):
    print(f"\tGetting modified methods in {project_id}-{bug_id}...")
    modified_methods = {}
    for file_path, modified_lines in modified_files_lines.items():
        abs_file_path = os.path.join(work_dir, file_path)
        if not os.path.exists(abs_file_path):
            print(f"\t\tFile not found: {abs_file_path}")
            continue
        with open(abs_file_path, 'r', encoding='utf-8', errors='replace') as file:
            java_code = file.read()
        analyzer = JavaParser()

        method_buggy_line_dict = {}
        for line_number in modified_lines:
            method_json = analyzer.find_method_by_line(java_code, line_number)
            if method_json:
                method_id = f"{method_json['method_name']}_{method_json['start_line']}_{method_json['end_line']}"
                if file_path not in modified_methods:
                    modified_methods[file_path] = []
                if method_json in modified_methods[file_path]:
                    method_buggy_line_dict[method_id].append(line_number)
                    continue
                method_buggy_line_dict[method_id] = [line_number]
                modified_methods[file_path].append(method_json)
        if file_path in modified_methods:
            for i, method_json in enumerate(modified_methods[file_path]):
                method_id = f"{method_json['method_name']}_{method_json['start_line']}_{method_json['end_line']}"
                method_json['buggy_lines'] = sorted(method_buggy_line_dict[method_id])
                modified_methods[file_path][i] = method_json
            
    return modified_methods

# TODO: fix version problem, there seems don't need version arg, we extract buggy from buggy method from buggy version. 
def get_all_modified_methods_in_defects4j_project(all_modified_files_lines, defects4j_framework, checkout_dir, version: Literal["fixed", "buggy"]):
    assert version == 'buggy', "Just buggy version"
    file_path = os.path.join(defects4j_framework, f"all_modified_methods_{version}.json")
    if os.path.exists(file_path):
        print(f"Loading all modified methods in Defects4J from {file_path}...")
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            all_modified_methods = json.load(file)
            return all_modified_methods
    print(f"Generating all modified methods in Defects4J...")
    all_modified_methods = {}
    projects = get_defects4j_projects(defects4j_framework)
    projects_path = os.path.join(defects4j_framework, 'projects')
    for project_id in projects:
        bugs = get_defects4j_bugs(defects4j_framework, project_id)
        for bug_id in bugs:
            work_dir = get_work_dir(checkout_dir, project_id, bug_id, version)
            project_bug_id = f"{project_id}-{bug_id}"
            buggy_files_lines_dict = all_modified_files_lines[project_bug_id]['added']
            tot_len = 0
            for file, lines in buggy_files_lines_dict.items():
                tot_len += len(lines)
            if tot_len == 0:
                buggy_files_lines_dict = {}
                for file, lines in all_modified_files_lines[project_bug_id]['deleted'].items():
                    buggy_files_lines_dict[file] = []
                    for i, line in enumerate(lines):
                        if i < len(lines) - 1 and lines[i + 1] - line == 1:
                            continue
                        buggy_files_lines_dict[file].append(line)
            modified_methods = get_modifed_methods_in_defects4j_project(buggy_files_lines_dict, project_id, bug_id, work_dir)
            all_modified_methods[project_bug_id] = modified_methods
    with open(file_path, 'w', encoding='utf-8', errors='replace') as file:
            json.dump(all_modified_methods, file, indent=4)
    return all_modified_methods

def run_command(command, timeout=300):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, None, "Timeout"

def checkout_defects4j_project(defects4j_framework, project_id, bug_id, version, work_dir):
    command = f"{defects4j_framework}/bin/defects4j checkout -p {project_id} -v {bug_id}{version[0]} -w {work_dir}"
    return run_command(command)

def compile_defects4j_project(defects4j_framework, work_dir):
    command = f"{defects4j_framework}/bin/defects4j compile -w {work_dir}"
    return run_command(command)

def test_defects4j_project(defects4j_framework, work_dir):
    command = f"{defects4j_framework}/bin/defects4j test -w {work_dir}"
    return run_command(command)

def checkout_all_defectes4j_project(defects4j_framework, checkout_dir, version: Literal["fixed", "buggy"]):
    print(f"Checking out all Defects4J projects ({version}) to {checkout_dir}...")
    if not os.path.exists(checkout_dir):
        print(f"\tErorr: {checkout_dir} not found.")
        return

    with ProcessPoolExecutor(max_workers=30) as executor:
        futures = {}
        projects = get_defects4j_projects(defects4j_framework)
        for project_id in projects:
            project_checkout_dir = os.path.join(checkout_dir, project_id)
            os.makedirs(project_checkout_dir, exist_ok=False)
            bugs = get_defects4j_bugs(defects4j_framework, project_id)
            for bug_id in bugs:
                work_dir = get_work_dir(checkout_dir, project_id, bug_id, version)
                future = executor.submit(checkout_defects4j_project, defects4j_framework, project_id, bug_id, version, work_dir)
                futures[future] = (project_id, bug_id)
        for future in futures:
            returncode, stdout, stderr = future.result(timeout=None)
            project_id, bug_id = futures[future]

# def parallel_process_defects4j_projects(defects4j_framework, func, *args):
#     print(f"Parallel processing all Defects4J projects with {func.__name__}...")
#     results = {}
#     with ProcessPoolExecutor(max_workers=30) as executor:
#         futures = {}
#         projects = get_defects4j_projects(defects4j_framework)
#         for project_id in projects:
#             bugs = get_defects4j_bugs(defects4j_framework, project_id)
#             project_bug_id = get_defects4j_project_bug_ids(project_id, bug_id)
#             for bug_id in bugs:
#                 future = executor.submit(func, defects4j_framework, project_id, bug_id, *args)
#                 futures[future] = project_bug_id
#         for future in futures:
#             result = future.result(timeout=None)
#             project_bug_id = futures[future]
#             results[project_bug_id] = result
#     return results
    
def get_target_classes_in_defects4j_project(defects4j_framework, project_id, bug_id):
    modified_classes_dir = os.path.join(defects4j_framework, 'projects', project_id, 'modified_classes')
    modified_classes_file = os.path.join(modified_classes_dir, f"{bug_id}.src")
    if not os.path.exists(modified_classes_file):
        print(f"\tError: {modified_classes_file} not found.")
        return None
    with open(modified_classes_file, 'r', encoding='utf-8', errors='replace') as file:
        target_classes = file.read().splitlines()
        return target_classes

def get_relevant_tests_in_defects4j_project(defects4j_framework, project_id, bug_id):
    relevant_tests_dir = os.path.join(defects4j_framework, 'projects', project_id, 'relevant_tests')
    relevant_tests_file = os.path.join(relevant_tests_dir, f"{bug_id}")
    if not os.path.exists(relevant_tests_file):
        print(f"\tError: {relevant_tests_file} not found.")
        return None
    with open(relevant_tests_file, 'r', encoding='utf-8', errors='replace') as file:
        relevant_tests = file.read().splitlines()
        return relevant_tests

# TEST_SRC_PATH_PREFIX = {
#     'Chart': ['tests'],
#     'Cli': ['src/test'],
#     'Closure': ['test'],
#     'Codec': ['src/test'],
#     'Collections': ['src/test/java'],
#     'Compress': ['src/test/java'],
#     'Csv': ['src/test/java'],
#     'Gson': ['gson/src/test/java'],
#     'JacksonCore': ['src/test/java'],
#     'JacksonDatabind': ['src/test/java'],
#     'JacksonXml': ['src/test/java'],
#     'Jsoup': ['src/test/java'],
#     'Jxpath': ['src/test'],
#     'Lang': ['src/test/java'],
#     'Math': ['src/test/java'],
#     'Mockito': ['test'],
#     'Time': ['src/test/java'],
# }
TEST_SRC_PATH_PREFIX = [
    'tests',
    'src/test',
    'src/test/java',
    'test',
    'gson/src/test/java',
]
def get_test_class_file_path_in_defects4j_project(checkout_dir, project_id, bug_id, version: Literal["fixed", "buggy"], test_class):
    work_dir = get_work_dir(checkout_dir, project_id, bug_id, version)
    test_file = test_class.replace('.', os.sep) + '.java'
    for path_prefix in TEST_SRC_PATH_PREFIX:
        test_path = os.path.join(work_dir, path_prefix, test_file)
        if os.path.exists(test_path):
            return test_path
    assert False, f"Error: {test_file} in {work_dir} not found."


def get_trigger_tests_in_defects4j_project(defects4j_framework, project_id, bug_id):
    trigger_tests_dir = os.path.join(defects4j_framework, 'projects', project_id, 'trigger_tests')
    trigger_tests_file = os.path.join(trigger_tests_dir, f"{bug_id}")
    if not os.path.exists(trigger_tests_file):
        print(f"\tError: {trigger_tests_file} not found.")
        return None
    with open(trigger_tests_file, 'r', encoding='utf-8', errors='replace') as file:
        trigger_tests = []
        current_test = None

        for line in file:
            
            if line.startswith('---'):
                if current_test is not None:
                    trigger_tests.append(current_test)
                current_test = {'test': line[4:].rstrip(), 'stack': []}
            elif current_test is not None:
                current_test['stack'].append(line.rstrip())

        if current_test is not None:
            trigger_tests.append(current_test)
        return trigger_tests

if __name__ == "__main__":
    def test_get_all_modified_methods_in_defects4j_project(defects4j_framework, checkout_dir):
        all_modified_files_lines = parse_patch_in_defects4j(defects4j_framework)
        all_modified_methods = get_all_modified_methods_in_defects4j_project(all_modified_files_lines, defects4j_framework, checkout_dir)
        print(json.dumps(all_modified_methods, indent=4))
    
    

    def test_get_defects4j_projects(defects4j_framework):
        print(get_defects4j_projects(defects4j_framework))
    
    def test_get_defects4j_bugs(defects4j_framework):
        projects = get_defects4j_projects(defects4j_framework)
        for project_id in projects:
            print(f"{project_id}: {get_defects4j_bugs(defects4j_framework, project_id)}")

    # all_modified_files_lines = parse_patch_in_defects4j(defects4j_framework)
    # # checkout_all_defectes4j_project(defects4j_framework, "/data/cmd/Ming/LLM_Based-Mutation/tools/mutant/utils/tmp")
    # all_modified_methods = get_all_modified_methods_in_defects4j_project(all_modified_files_lines, defects4j_framework, "/data/cmd/Ming/LLM_Based-Mutation/tools/mutant/utils/tmp")
    # print(json.dumps(all_modified_methods, indent=4))
    # for project in projects:
    #     for bug_id in get_defects4j_bugs(defects4j_framework, project):
    #         project_bug_id = f"{project}-{bug_id}"
    #         if project_bug_id not in all_modified_methods:
    #             print(f"Error: {project_bug_id} not found.")
    def test_get_target_classes_in_defects4j_project(defects4j_framework):
        projects = get_defects4j_projects(defects4j_framework)
        for project_id in projects:
            for bug_id in get_defects4j_bugs(defects4j_framework, project_id):
                print(f"{project_id}-{bug_id}:")
                print(get_target_classes_in_defects4j_project(defects4j_framework, project_id, bug_id))
    def test_get_relevant_tests_in_defects4j_project(defects4j_framework):
        projects = get_defects4j_projects(defects4j_framework)
        for project_id in projects:
            for bug_id in get_defects4j_bugs(defects4j_framework, project_id):
                print(f"{project_id}-{bug_id}:")
                print(get_relevant_tests_in_defects4j_project(defects4j_framework, project_id, bug_id))    
                
    # for project_bug_id, modified_methods in all_modified_methods.items():
    #     print(f"{project_bug_id}:")
    #     for file_path, methods in modified_methods.items():
    #         print(f"\t{file_path}:")
    #         for method in methods:
    #             print(f"\t\t{method['method_name']} ({method['start_line']}-{method['end_line']})")
    # print(json.dumps(all_modified_files_lines, indent=4))
    # project_id = "Chart"
    # bug_id = "1"
    # work_dir = "/data/cmd/Ming/LLM_Based-Mutation/tools/mutant/tmp/defects4j/Chart/Chart-1-fixed"
    # modified_methods = get_modifed_methods_in_defects4j_project(all_modified_files_lines, project_id, bug_id, work_dir)
    # print(json.dumps(modified_methods, indent=4))

    # print(checkout_defects4j_project(defects4j_path, project_id, bug_id, work_dir))

    defects4j_framework = "/data/cmd/Ming/LLM_Based-Mutation/tools/mutant/defects4j-2.1.0/framework"
    checkout_dir = "/data/cmd/Ming/LLM_Based-Mutation/tools/mutant/utils/tmp"

    # test_get_all_modified_methods_in_defects4j_project(defects4j_framework, checkout_dir)
    
    # print(get_trigger_tests_in_defects4j_project(defects4j_framework, "Chart", "3"))
    