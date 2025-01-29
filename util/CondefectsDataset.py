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

class CondefectsGenerator:
    def __init__(self, condefects_home, checkout_dir, time_from, time_to, language, lib_path, prompt_dir, tmp_dir):
        self.condefects_home = condefects_home
        # checkout_condefects(condefects_home, checkout_dir, time_from, time_to, language)
        self.checkout_dir = checkout_dir
        self.prompt_dir = prompt_dir
        self.classpath = f".:{lib_path}/*"
        self.tmp_dir = tmp_dir

        self.id_tuple_list = self.get_task_program_tuple_list()
        self.id_list = get_id_list(self.id_tuple_list)

    def get_task_program_tuple_list(self):
        task_program_tuple_list = []

        tasks = get_condefects_tasks(self.checkout_dir)
        for task_id in tasks:
            program_list = get_java_programs_in_task(self.checkout_dir, task_id)
            for program_id in program_list:
                task_program_tuple_list.append((task_id, program_id))
        
        return task_program_tuple_list
    
    def get_prompts_txt_file(self, output_dir, task_id, program_id):
        id = get_id_by_tuple((task_id, program_id))
        prompts_txt_file = os.path.join(output_dir, f"{id}.prompts.txt")
        return prompts_txt_file

    def get_bug_info_txt_file(self, output_dir, task_id, program_id):
        id = get_id_by_tuple((task_id, program_id))
        bug_info_txt_file = os.path.join(output_dir, f"{id}.info.txt")
        return bug_info_txt_file

    def output_prompt(self):
        tasks = get_condefects_tasks(self.checkout_dir)
        for task_id in tasks:
            program_list = get_java_programs_in_task(self.checkout_dir, task_id)
            for program_id in program_list:
                id = get_id_by_tuple((task_id, program_id))

                bug_info_list = self.get_bug_info_list(task_id, program_id)
                bug_info = bug_info_list[0]

                buggy_file, buggy_method, buggy_method_src, test_stack, test_assert, \
                buggy_lines_in_method, buggy_statements, buggy_method_src_endswith_buggy_statement \
                        = get_bug_info_content(bug_info)

                prompts_list = []
                prompts = chk_get_prompt(buggy_method_src, test_stack, test_assert, buggy_lines_in_method, buggy_statements, buggy_method_src_endswith_buggy_statement)
                prompts_list.append(prompts)

                if prompts is None:
                    continue

                prompts_txt_file = self.get_prompts_txt_file(self.prompt_dir, task_id, program_id)
                output_prompts_txt(prompts_txt_file, prompts)

                prompts_list_json_file = get_prompts_list_json_file(self.prompt_dir, id)
                output_json(prompts_list_json_file, prompts_list)

    def output_info(self):
        tasks = get_condefects_tasks(self.checkout_dir)
        for task_id in tasks:
            program_list = get_java_programs_in_task(self.checkout_dir, task_id)
            for program_id in program_list:
                id = get_id_by_tuple((task_id, program_id))

                bug_info_list = self.get_bug_info_list(task_id, program_id)
                bug_info = bug_info_list[0]

                bug_info_txt_file = self.get_bug_info_txt_file(self.prompt_dir, task_id, program_id)
                output_bug_info(bug_info_txt_file, bug_info)

                bug_info_list_json_file = get_bug_info_list_json_file(self.prompt_dir, id)
                output_json(bug_info_list_json_file, bug_info_list)
            
    
    def get_bug_info_list(self, task_id, program_id):
        bug_info = {
            "buggy_file": "faultyVersion.java",
            "buggy_method": self.get_buggy_method(task_id, program_id),

            "buggy_method_src": self.get_buggy_method_src(task_id, program_id),
            "test_stack": self.get_test_stack(task_id, program_id),
            "test_assert": self.get_test_assert(task_id, program_id),
            "buggy_lines_in_method": self.get_buggy_lines_in_method(task_id, program_id),
            "buggy_statements": self.get_buggy_statements(task_id, program_id),
            "buggy_method_src_endswith_buggy_statement": self.get_buggy_method_src_endswith_buggy_statement(task_id, program_id)
        }
        return [bug_info]

    def get_buggy_method(self, task_id, program_id):
        program_path = get_java_program_path(self.checkout_dir, task_id, program_id)
        buggy_lineno = self.get_buggy_line(task_id, program_id)
        if buggy_lineno is None:
            return None
        program_faulty_version_code = get_program_faulty_version(program_path)
        analyzer = JavaParser()
        buggy_method = analyzer.find_method_by_line(program_faulty_version_code, buggy_lineno)
        if buggy_method is None:
            return None
        return buggy_method

    def get_buggy_method_src(self, task_id, program_id):
        method_json = self.get_buggy_method(task_id, program_id)
        if method_json is None:
            return None
        buggy_method_src = method_json["method_body"]
        return buggy_method_src
    
    def get_test_stack(self, task_id, program_id):
        return "None"

    def get_test_assert(self, task_id, program_id):
        return "None"
    
    def get_buggy_line(self, task_id, program_id):
        program_path = get_java_program_path(self.checkout_dir, task_id, program_id)
        fault_location = get_program_fault_location(program_path)
        if fault_location == 0:
            return None
        buggy_line = fault_location
        return buggy_line
    
    def get_buggy_lines(self, task_id, program_id):
        buggy_line = self.get_buggy_line(task_id, program_id)
        return [buggy_line]
    
    def get_buggy_line_in_method(self, task_id, program_id) -> int:
        method_json = self.get_buggy_method(task_id, program_id)
        buggy_lineno = self.get_buggy_line(task_id, program_id)
        if method_json is None or buggy_lineno is None:
            return None
        start_line = method_json['start_line']
        buggy_line_in_method = buggy_lineno - start_line + 1
        return buggy_line_in_method
    
    def get_buggy_lines_in_method(self, task_id, program_id) -> list:
        buggy_line_in_method = self.get_buggy_line_in_method(task_id, program_id)
        return [buggy_line_in_method]
    
    def get_line_from_str(self, lines_str, lineno):
        try:
            lines = lines_str.split('\n')
            return lines[lineno - 1]
        except:
            return None
    
    def get_buggy_statements(self, task_id, program_id):
        buggy_method_src = self.get_buggy_method_src(task_id, program_id)
        buggy_lineno_in_method = self.get_buggy_line_in_method(task_id, program_id)
        buggy_statement = self.get_line_from_str(buggy_method_src, buggy_lineno_in_method)
        buggy_statements = [buggy_statement]
        return buggy_statements
    
    def get_buggy_method_src_endswith_buggy_statement(self, task_id, program_id):
        buggy_method_src = self.get_buggy_method_src(task_id, program_id)
        buggy_lineno_in_method = self.get_buggy_line_in_method(task_id, program_id)
        try:
            lines = buggy_method_src.split('\n')
            return '\n'.join(lines[:buggy_lineno_in_method])
        except:
            return None

    def query_llm(self):
        query_llm(self.prompt_dir, self.id_list)

    def check_query_results_fl(self):
        check_query_results_fl(self.prompt_dir, self.id_list)

    def check_query_results_apr_task_program(self, task_id, program_id):
        id = get_id_by_tuple((task_id, program_id))
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
                print("\tcheckout...")
                work_dir = os.path.join(self.tmp_dir, f"{id}-{prompt_id}-{llm_id}")
                if os.path.exists(work_dir):
                    shutil.rmtree(work_dir)
                checkout_condefects_task_program(self.condefects_home, work_dir, task_id, program_id)
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
                print("\tcompileing...")
                version = "faultyVersion"
                rc, so, se = compile_condefects_task_program(self.condefects_home, work_dir, version)
                check_results_list[prompt_id][llm_id]['compile'] = {
                    'rc': rc,
                    'so': so,
                    'se': se
                }
                if se == '':
                    status = "Compile success"
                    # test
                    print("\ttesting...")
                    failed_tests, test_res_info_list = test_condefects_task_program(self.condefects_home, work_dir, task_id)
                    check_results_list[prompt_id][llm_id]['test'] = {
                        'test_res_info_list': test_res_info_list
                    }
                    if len(failed_tests) == 0:
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

        id_tuple_list = self.get_task_program_tuple_list()

        # filter
        filter_id_list = filter_for_fl_and_apr(self.prompt_dir, self.id_list)
        print(len(filter_id_list))
        print(filter_id_list)
        # return
        
        # debug
        for task_id, program_id in id_tuple_list:
            id = get_id_by_tuple((task_id, program_id))
            if id in filter_id_list:
                print(f"Checking apr for {id}")
                self.check_query_results_apr_task_program(task_id, program_id)
        return

        with ProcessPoolExecutor(max_workers=10) as executor:
            futures = {}
            
            for task_id, program_id in id_tuple_list:
                id = get_id_by_tuple((task_id, program_id))
                if id in filter_id_list:
                    future = executor.submit(self.check_query_results_apr_task_program, task_id, program_id)
                    futures[future] = (task_id, program_id)
            for future in tqdm(as_completed(futures), total=len(futures), desc="Checking apr..."):
                try:
                    task_id, program_id = futures[future]
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

            task_id1, task_id2, program_id = get_tuple_by_id(id)
            task_id = task_id1 + "_" + task_id2
            program_path = os.path.join(self.checkout_dir, task_id, "Java", program_id)
            correct_version = os.path.join(program_path, "correctVersion.java")
            file.write(f"{correct_version}\n\n")
            fault_location = get_program_fault_location(program_path)
            file.write(f"{fault_location}\n\n")
            llm_res = prepare_llm_res_for_apr_manual_check(self.prompt_dir, id, prompt_id, llm_id)
            file.write(llm_res)
        return manual_check_apr_status_file

    def collect_apr_status_for_manual_check(self):
        apr_status_file = "stat/apr_status_for_manual_check-cond.json"
        collect_apr_status_for_manual_check(self.prompt_dir, self.id_list, apr_status_file)
        tmp_apr_status_file = "stat/apr_status_for_manual_check-cond.tmp.json"
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
        for llm_id in localized_bugs.keys():
            print(f"llm_id: {llm_id} ({len(localized_bugs[llm_id])})")
        create_venn_svg(localized_bugs, "condefects", "stat/unique_localized_bugs-cond.svg")

    def get_fixed_bugs(self):
        fixed_bugs = get_fixed_bugs("stat/manual_check-cond.json")
        for llm_id in fixed_bugs.keys():
            print(f"llm_id: {llm_id} ({len(fixed_bugs[llm_id])})")
        create_venn_svg(fixed_bugs, "condefects", "stat/unique_fixed_bugs-cond.svg")

    def get_result_classification_fl(self):
        result_classification = get_result_classification_fl(self.prompt_dir, self.id_list)
        tsv_file = "stat/result_classification-cond.tsv"
        pie_chart_file = "stat/result_classification-cond.svg"
        write_result_classification_fl_tsv(result_classification, tsv_file)
        # generate_pie_charts_from_tsv(tsv_file, pie_chart_file, "fl")
        return result_classification

    def get_result_classification_apr(self):
        result_classification = get_result_classification_apr("stat/manual_check-cond.json")
        tsv_file = "stat/result_classification-apr-cond.tsv"
        pie_chart_file = "stat/result_classification-apr-cond.svg"
        write_result_classification_apr_tsv(result_classification, tsv_file)
        # generate_pie_charts_from_tsv(tsv_file, pie_chart_file, "apr")
        return result_classification
    
    def write_localized_bugs_by_different_prompts_tsv(self):
        write_localized_bugs_by_different_prompts_tsv(self.prompt_dir, self.id_list, "stat/localized_bugs_by_different_prompts-cond.tsv")

    def write_fixed_bugs_by_different_prompts_tsv(self):
        write_fixed_bugs_by_different_prompts_tsv("stat/manual_check-cond.json", "stat/fixed_bugs_by_different_prompts-cond.tsv")

