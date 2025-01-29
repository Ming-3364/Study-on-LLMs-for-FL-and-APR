import sys
from .dataset.defects4j import *
from .dataset.condefects import *
from .parser.java_parser import JavaParser
import re
import shutil
from .tools import *
from tqdm import tqdm
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

class Defects4JGenerator:
    def __init__(self, defects4j_framework, checkout_dir, prompt_dir, tmp_dir):
        self.defects4j_framework = defects4j_framework
        self.checkout_dir = checkout_dir
        self.prompt_dir = prompt_dir
        self.tmp_dir = tmp_dir
        self.all_modified_files_lines = parse_patch_in_defects4j(self.defects4j_framework)
        if not os.path.exists(checkout_dir):
            os.mkdir(checkout_dir)
            checkout_all_defectes4j_project(defects4j_framework, checkout_dir, 'buggy')
        self.all_modified_methods_buggy = get_all_modified_methods_in_defects4j_project(self.all_modified_files_lines, self.defects4j_framework, checkout_dir, 'buggy')

        self.id_tuple_list = self.get_project_bug_tuple_list()
        self.id_list = get_id_list(self.id_tuple_list)

    def get_project_bug_tuple_list(self):
        project_bug_tuple_list = []

        projects = get_defects4j_projects(self.defects4j_framework)
        for project_id in projects:
            bugs = get_defects4j_bugs(self.defects4j_framework, project_id)
            for bug_id in bugs:
                project_bug_tuple_list.append((project_id, bug_id))
        
        return project_bug_tuple_list

    def get_prompts_txt_file(self, output_dir, project_id, bug_id, method_id):
        id = get_id_by_tuple((project_id, bug_id))
        prompts_txt_file = os.path.join(output_dir, f"{id}.prompts_m{method_id}.txt")
        return prompts_txt_file
    
    def get_bug_info_txt_file(self, output_dir, project_id, bug_id, method_id):
        id = get_id_by_tuple((project_id, bug_id))
        bug_info_txt_file = os.path.join(output_dir, f"{id}.info_m{method_id}.txt")
        return bug_info_txt_file

    def output_prompt(self):
        projects = get_defects4j_projects(self.defects4j_framework)
        for project_id in projects:
            bugs = get_defects4j_bugs(self.defects4j_framework, project_id)
            for bug_id in bugs:
                id = get_id_by_tuple((project_id, bug_id))
                
                buggy_info = self.get_buggy_files_methods(project_id, bug_id)
                if buggy_info is None:
                    continue
                bug_info_list = self.get_bug_info_list(project_id, bug_id)
                if bug_info_list is None:
                    continue

                prompts_list = []
                for i, bug_info in enumerate(bug_info_list):
                    buggy_file, buggy_method, buggy_method_src, test_stack, test_assert, \
                    buggy_lines_in_method, buggy_statements, buggy_method_src_endswith_buggy_statement \
                            = get_bug_info_content(bug_info)

                    prompts = chk_get_prompt(buggy_method_src, test_stack, test_assert, buggy_lines_in_method, buggy_statements, buggy_method_src_endswith_buggy_statement)
                    if prompts is None:
                        continue
                    
                    prompts_list.append(prompts)
                
                for i, prompts in enumerate(prompts_list):
                    prompts_txt_file = self.get_prompts_txt_file(self.prompt_dir, project_id, bug_id, i)
                    output_prompts_txt(prompts_txt_file, prompts)
                
                prompts_list_json_file = get_prompts_list_json_file(self.prompt_dir, id)
                output_json(prompts_list_json_file, prompts_list)

    def output_info(self):
        projects = get_defects4j_projects(self.defects4j_framework)
        for project_id in projects:
            bugs = get_defects4j_bugs(self.defects4j_framework, project_id)
            for bug_id in bugs:
                id = get_id_by_tuple((project_id, bug_id))

                bug_info_list = self.get_bug_info_list(project_id, bug_id)
                if bug_info_list is None:
                    continue

                for i, bug_info in enumerate(bug_info_list):
                    bug_info_txt_file = self.get_bug_info_txt_file(self.prompt_dir, project_id, bug_id, i)
                    output_bug_info(bug_info_txt_file, bug_info)

                bug_info_list_json_file = get_bug_info_list_json_file(self.prompt_dir, id)
                output_json(bug_info_list_json_file, bug_info_list)
            
    def get_bug_info_list(self, project_id, bug_id):
        buggy_files_methods = self.get_buggy_files_methods(project_id, bug_id)
        if buggy_files_methods is None:
            return None
        bug_info_list = []
        for buggy_file, buggy_methods in buggy_files_methods.items():
            for buggy_method in buggy_methods:
                bug_info = {
                    "buggy_file": buggy_file,
                    "buggy_method": buggy_method,

                    "buggy_method_src": self.get_buggy_method_src(buggy_method),
                    "test_stack": self.get_test_stack(project_id, bug_id),
                    "test_assert": self.get_test_assert(project_id, bug_id),
                    "buggy_lines_in_method": self.get_buggy_lines_in_method(buggy_method),
                    "buggy_statements": self.get_buggy_statements(buggy_method),
                    "buggy_method_src_endswith_buggy_statement": self.get_buggy_method_src_endswith_buggy_statement(buggy_method)
                }
                bug_info_list.append(bug_info)
        return bug_info_list

    def get_buggy_files_methods(self, project_id, bug_id):
        project_bug_id = get_defects4j_project_bug_ids(project_id, bug_id)
        buggy_files_methods = self.all_modified_methods_buggy[project_bug_id]
        if len(buggy_files_methods) == 0:
            return None
        return buggy_files_methods
    
    def get_buggy_method_src(self, buggy_method):
        buggy_method_src = buggy_method["method_body"]
        return buggy_method_src

    def get_test_stack(self, project_id, bug_id):
        trigger_tests = get_trigger_tests_in_defects4j_project(self.defects4j_framework, project_id, bug_id)
        test_stack = ''
        for trigger_test in trigger_tests:
            test_stack += trigger_test['test'] + '\n'
            test_stack += "\n".join(trigger_test['stack'][:200]) + '\n'   # TODO: how many lines of stack should be keep
        return test_stack
    
    def get_test_assert(self, project_id, bug_id):
        trigger_tests = get_trigger_tests_in_defects4j_project(self.defects4j_framework, project_id, bug_id)
        for trigger_test in trigger_tests:
            test = trigger_test['test']
            stack = trigger_test['stack']
            
            test_class, test_method = test.split("::")[0], test.split("::")[1]
            for line in stack:
                if line.find(test_method) != -1:
                    line = line.strip()
                    test_class = line.split("at ")[1].split(f".{test_method}")[0]

            test_class_file_path = get_test_class_file_path_in_defects4j_project(self.checkout_dir, project_id, bug_id, 'buggy', test_class)
            with open(test_class_file_path, 'r', encoding='utf-8', errors='replace') as file:
                java_code = file.read()
                analyzer = JavaParser()

                found = False
                for line in stack:
                    if line.find(test_method) != -1:
                        found = True
                        line = line.strip()
                        pattern = r"at ([\w\.]+)\.([\w$]+)\(([\w\.]+):(\d+)\)"
                        match = re.match(pattern, line)
                        if match:                        
                            full_class_path = match.group(1)
                            method_name = match.group(2)
                            file_name = match.group(3)
                            line_number = int(match.group(4))

                            line_content = analyzer.get_line_content(java_code, line_number)
                            return line_content.strip() + '\n'
                if found:
                    assert False, f" {test_class_file_path} {line} not a known stack format!"
                
                # if test_method not in stack, find method in test_class
                method = analyzer.find_method_by_name(java_code, test_method)
                if method is not None:
                    return method['method_body']
                
                assert False, f" {test_class_file_path} {test_method} can't be found!"
    
    def get_buggy_lines(self, buggy_method):
        buggy_lines = buggy_method['buggy_lines']
        return buggy_lines

    def get_buggy_lines_in_method(self, buggy_method) -> list:
        buggy_lines = self.get_buggy_lines(buggy_method)
        buggy_lines_in_method = []
        for buggy_line in buggy_lines:
            start_line = buggy_method['start_line']
            buggy_lines_in_method.append(buggy_line - start_line + 1)
        return buggy_lines_in_method
    
    def get_statement_in_method_by_lines(self, method_body, line):
        lines = method_body.split('\n')
        return lines[line - 1]

    def get_buggy_statements(self, buggy_method):
        buggy_statments = []
        buggy_lines_in_method = self.get_buggy_lines_in_method(buggy_method)
        for lineno in buggy_lines_in_method:
            buggy_method_src = self.get_buggy_method_src(buggy_method)
            buggy_statement = self.get_statement_in_method_by_lines(buggy_method_src, lineno)
            buggy_statments.append(buggy_statement)
        return buggy_statments


    def get_buggy_method_src_endswith_buggy_statement(self, buggy_method):
        buggy_lines_in_method = self.get_buggy_lines_in_method(buggy_method)
        last_line = sorted(buggy_lines_in_method)[-1]
        buggy_method_src = self.get_buggy_method_src(buggy_method)
        lines = buggy_method_src.split('\n')
        return '\n'.join(lines[:last_line])

    def query_llm(self):
        query_llm(self.prompt_dir, self.id_list)

    def check_query_results_fl(self):
        check_query_results_fl(self.prompt_dir, self.id_list)

    def check_query_results_apr_program_bug(self, project_id, bug_id):
        id = get_id_by_tuple((project_id, bug_id))
        bug_info_list_json_file = get_bug_info_list_json_file(self.prompt_dir, id)
        query_results_list_json_file = get_query_results_list_json_file(self.prompt_dir, id)
        
        with open(bug_info_list_json_file, 'r', encoding='utf-8') as file:
            bug_info_list = json.load(file)
        with open(query_results_list_json_file, 'r', encoding='utf-8') as file:
            query_results_list = json.load(file)
        check_results_list = {}
        overall_status = {}
        prompt_id_list = ['prompt_apr_1', 'prompt_apr_2', 'prompt_apr_3', 'prompt_apr_4', 'prompt_apr_5', 'prompt_apr_6']
        llm_id_list = LLMManager().get_llm_id_list()
        for prompt_id in prompt_id_list:
            check_results_list[prompt_id] = {}
            overall_status[prompt_id] = {}
            for llm_id in llm_id_list:
                check_results_list[prompt_id][llm_id] = {}
                overall_status[prompt_id][llm_id] = {}
                status = ""
                # checkout buggy version
                work_dir = os.path.join(self.tmp_dir, f"{id}-{prompt_id}-{llm_id}")
                if os.path.exists(work_dir):
                    shutil.rmtree(work_dir)
                checkout_defects4j_project(self.defects4j_framework, project_id, bug_id, 'buggy', work_dir)

                # patch mehods
                replace_dict = {}
                for i, bug_info in enumerate(bug_info_list):
                    buggy_file = bug_info["buggy_file"]
                    buggy_method = bug_info["buggy_method"]
                    start_line = buggy_method["start_line"]
                    end_line = buggy_method["end_line"]

                    query_results = query_results_list[i]

                    file_path = os.path.join(work_dir, buggy_file)
                    if file_path not in replace_dict:
                        replace_dict[file_path] = []
                    if prompt_id in ['prompt_apr_1', 'prompt_apr_2', 'prompt_apr_3']:
                        
                        res = query_results[prompt_id][llm_id]
                        replace_dict[file_path].append((start_line, end_line, res))
                    elif prompt_id in ['prompt_apr_4', 'prompt_apr_5', 'prompt_apr_6']:
                        res = query_results[prompt_id][llm_id]
                        try:
                            data = json.loads(res)
                            for fix in data:
                                line_number = int(fix['line_number'])
                                line_number = start_line + line_number - 1
                                fixed_statement = fix['fixed_statement']
                                replace_dict[file_path].append((line_number, line_number, fixed_statement))
                        except Exception as e:
                            status = "Failed"
                    else:
                        assert False, f"Unknown prompt_id: {prompt_id}"

                if status == "Failed":
                    overall_status[prompt_id][llm_id] = status
                    continue

                rc = replace_lines_in_files(replace_dict)
                if rc == -1:
                    overall_status[prompt_id][llm_id] = "Failed"
                    continue
                    
                # compile
                rc, so, se = compile_defects4j_project(self.defects4j_framework, work_dir)
                check_results_list[prompt_id][llm_id]['compile'] = {
                    'rc': rc,
                    'so': so,
                    'se': se
                }
                if rc == 0:
                    status = "Compile success"
                    # run test
                    rc, so, se = test_defects4j_project(self.defects4j_framework, work_dir)
                    check_results_list[prompt_id][llm_id]['test'] = {
                        'rc': rc,
                        'so': so,
                        'se': se
                    }
                    if se == "Timeout":
                        status = "Timeout"
                    elif so.find("Failing tests: 0") != -1:
                        status = "Pass all tests"
                    else:
                        status = "Fail some tests"
                else:
                    status = "Compile failed"
                overall_status[prompt_id][llm_id] = status
        check_results_apr = {'overall_status': overall_status, 'check_results_list': check_results_list, }
        check_results_apr_json_file = get_check_results_apr_json_file(self.prompt_dir, id)
        output_json(check_results_apr_json_file, check_results_apr)
        return check_results_apr

    
    def check_query_results_apr(self):
        print("Checking apr...")

        id_tuple_list = self.get_project_bug_tuple_list()

        # filter
        filter_id_list = filter_for_fl_and_apr(self.prompt_dir, self.id_list)

        with ProcessPoolExecutor(max_workers=10) as executor:
            futures = {}
            
            for project_id, bug_id in id_tuple_list:
                id = get_id_by_tuple((project_id, bug_id))
                if id in filter_id_list:
                    future = executor.submit(self.check_query_results_apr_program_bug, project_id, bug_id)
                    futures[future] = (project_id, bug_id)
            for future in tqdm(as_completed(futures), total=len(futures), desc="Checking apr..."):
                try:
                    project_id, bug_id = futures[future]
                    check_results_apr = future.result()
                    if check_results_apr is None:
                        continue
                except Exception as e:
                    print(f"An error occurred while checking apr: {e}")
                    continue

    def prepare_apr_manual_check(self, id, prompt_id, llm_id):
        manual_check_apr_status_file = get_manual_check_apr_status_file(self.prompt_dir, id, prompt_id, llm_id)
        with open(manual_check_apr_status_file, 'w', encoding='utf-8') as file:
            file.write(f"ID: {id}\n")
            file.write(f"Prompt: {prompt_id}\n")
            file.write(f"LLM: {llm_id}\n\n")

            project_id, bug_id = get_tuple_by_id(id)
            patch_file = os.path.join(self.defects4j_framework, "projects", project_id, 'patches', f"{bug_id}.src.patch")
            file.write(f"{patch_file}\n\n")
            llm_res = prepare_llm_res_for_apr_manual_check(self.prompt_dir, id, prompt_id, llm_id)
            file.write(llm_res)
        return manual_check_apr_status_file

    def collect_apr_status_for_manual_check(self):
        apr_status_file = "stat/apr_status_for_manual_check-d4j.json"
        collect_apr_status_for_manual_check(self.prompt_dir, self.id_list, apr_status_file)
        tmp_apr_status_file = "stat/apr_status_for_manual_check-d4j.tmp.json"
        with open(apr_status_file, 'r', encoding='utf-8') as file:
            apr_status = json.load(file)
            for id in apr_status.keys():
                for llm_id in LLMManager().get_llm_id_list():
                    for prompt_id in ['prompt_apr_1', 'prompt_apr_2', 'prompt_apr_3', 'prompt_apr_4', 'prompt_apr_5', 'prompt_apr_6']:
                        status = apr_status[id][prompt_id][llm_id]
                        if status == "PassAllTests":
                            manual_check_apr_status_file = self.prepare_apr_manual_check(id, prompt_id, llm_id)
                            apr_status[id][prompt_id][llm_id] = f"PassAllTests: check {manual_check_apr_status_file}"
            output_json(tmp_apr_status_file, apr_status)      


    def stat_check_results(self):
        fl_stat, apr_stat = stat_check_results_for_files(self.prompt_dir, self.id_list)
        print("fl_stat:")
        print(json.dumps(fl_stat, indent=4))
        print("apr_stat:")
        print(json.dumps(apr_stat, indent=4))

    def get_localized_bugs(self):
        localized_bugs = get_localized_bugs(self.prompt_dir, self.id_list)

        header = ["project"]
        llm_id_list = LLMManager().get_llm_id_list()
        header.extend(llm_id_list)
        rows = []

        projects = get_defects4j_projects(self.defects4j_framework)
        project_res = {}
        for project_id in projects:
            project_res[project_id] = {}
            for llm_id in llm_id_list:
                project_res[project_id][llm_id] = []
        for llm_id in LLMManager().get_llm_id_list():
            for id in localized_bugs[llm_id]:
                project_id, bug_id = get_tuple_by_id(id)
                project_res[project_id][llm_id].append(bug_id)

        for project_id in projects:
            row = [project_id]
            for llm_id in llm_id_list:
                row.append(len(project_res[project_id][llm_id]))
            rows.append(row)
        tsv_file = "localized_bugs-d4j.tsv"
        write_tsv(tsv_file, header, rows)
                
        create_venn_svg(localized_bugs, "defects4j", "stat/unique_localized_bugs-d4j.svg")

        bug_type_percentage_in_localized_bugs = get_bug_type_percentage_in_localized_bugs(self.prompt_dir, self.id_list)
        write_bug_type_percentage_in_bugs_tsv(bug_type_percentage_in_localized_bugs, "stat/bug_type_percentage_in_localized_bugs-d4j.tsv")

    def get_fixed_bugs(self):
        fixed_bugs = get_fixed_bugs("stat/manual_check-d4j.json")

        header = ["project"]
        llm_id_list = LLMManager().get_llm_id_list()
        header.extend(llm_id_list)
        rows = []

        projects = get_defects4j_projects(self.defects4j_framework)
        project_res = {}
        for project_id in projects:
            project_res[project_id] = {}
            for llm_id in llm_id_list:
                project_res[project_id][llm_id] = []
        for llm_id in LLMManager().get_llm_id_list():
            for id in fixed_bugs[llm_id]:
                project_id, bug_id = get_tuple_by_id(id)
                project_res[project_id][llm_id].append(bug_id)

        for project_id in projects:
            row = [project_id]
            for llm_id in llm_id_list:
                row.append(len(project_res[project_id][llm_id]))
            rows.append(row)
        tsv_file = "stat/fixed_bugs-d4j.tsv"
        write_tsv(tsv_file, header, rows)
                
        create_venn_svg(fixed_bugs, "defects4j", "stat/unique_fixed_bugs-d4j.svg")

        bug_type_percentage_in_fixed_bugs = get_bug_type_percentage_in_fixed_bugs("stat/manual_check-d4j.json")
        write_bug_type_percentage_in_bugs_tsv(bug_type_percentage_in_fixed_bugs, "stat/bug_type_percentage_in_fixed_bugs-d4j.tsv")

    def get_result_classification_fl(self):
        result_classification = get_result_classification_fl(self.prompt_dir, self.id_list)
        tsv_file = "stat/result_classification-d4j.tsv"
        pie_chart_file = "stat/result_classification-d4j.svg"
        write_result_classification_fl_tsv(result_classification, tsv_file)
        # generate_pie_charts_from_tsv(tsv_file, pie_chart_file, "fl")
        return result_classification

    def get_result_classification_apr(self):
        result_classification = get_result_classification_apr("stat/manual_check-d4j.json")
        tsv_file = "stat/result_classification-apr-d4j.tsv"
        pie_chart_file = "stat/result_classification-apr-d4j.svg"
        write_result_classification_apr_tsv(result_classification, tsv_file)
        # generate_pie_charts_from_tsv(tsv_file, pie_chart_file, "apr")
        return result_classification

    def write_localized_bugs_by_different_prompts_tsv(self):
        write_localized_bugs_by_different_prompts_tsv(self.prompt_dir, self.id_list, "stat/localized_bugs_by_different_prompts-d4j.tsv")

    def write_fixed_bugs_by_different_prompts_tsv(self):
        write_fixed_bugs_by_different_prompts_tsv("stat/manual_check-d4j.json", "stat/fixed_bugs_by_different_prompts-d4j.tsv")
