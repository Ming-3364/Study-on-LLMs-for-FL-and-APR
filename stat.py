from util.CondefectsDataset import *
from util.Defects4jDataset import *
import os

defects4j_framework = "<defects4j_framework>" # your absolute path of defects4j_framework, e.g., "/path/to/defects4j-2.1.0/framework"
checkout_dir = '<checkout_dir>' # your absolute path of checkout_dir
output_dir = 'output/defects4j'
tmp_dir = 'tmp'

defects4j_generator = Defects4JGenerator(defects4j_framework, d4j_checkout_dir, d4j_output_dir, d4j_tmp_dir)

condefects_home = "<condefects_home>" # your absolute path of condefects_home, e.g., "/path/to/ConDefects"
condefects_checkout_dir = "<checkout_dir>" # your absolute path of checkout_dir
time_from = "2024-03-01"
time_to = "2024-06-30"
output_dir = 'output/condefects'
tmp_dir = 'tmp'

condefects_generator = CondefectsGenerator(condefects_home, condefects_checkout_dir, time_from, time_to, "Java", junit_jar_path, cond_output_dir, cond_tmp_dir)

# defects4j_generator.output_info()
# defects4j_generator.output_prompt()
# defects4j_generator.query_llm()
# defects4j_generator.check_query_results_fl()
# defects4j_generator.check_query_results_apr()
# defects4j_generator.stat_check_results()

# defects4j_generator.get_localized_bugs()
# condefects_generator.get_localized_bugs()

defects4j_generator.get_fixed_bugs()
condefects_generator.get_fixed_bugs()

# defects4j_generator.get_result_classification()
# condefects_generator.get_result_classification()

defects4j_generator.get_result_classification_apr()
condefects_generator.get_result_classification_apr()

defects4j_generator.write_fixed_bugs_by_different_prompts_tsv()
condefects_generator.write_fixed_bugs_by_different_prompts_tsv()

def create_venn_of_uniquely_located_bugs_by_different_prompts():
    result_classification_d4j = defects4j_generator.get_result_classification_fl()
    result_classification_cond = condefects_generator.get_result_classification_fl()
    result_classification = merge_result_classification([result_classification_d4j, result_classification_cond])
    create_venn_of_uniquely_results_by_different_prompts(result_classification, "stat/unique_located_bugs_by_different_prompts", "fl")

def create_venn_of_uniquely_fixed_bugs_by_different_prompts():
    result_classification_d4j = defects4j_generator.get_result_classification_apr()
    result_classification_cond = condefects_generator.get_result_classification_apr()
    result_classification = merge_result_classification([result_classification_d4j, result_classification_cond])
    create_venn_of_uniquely_results_by_different_prompts(result_classification, "stat/unique_fixed_bugs_by_different_prompts", "apr")

# create_venn_of_uniquely_located_bugs_by_different_prompts()
create_venn_of_uniquely_fixed_bugs_by_different_prompts()

def get_defects4j_bugnum():
    project_bugnum = {}
    for root, dirs, files in os.walk(d4j_output_dir):
        for file in files:
            if file.endswith(".query_results.json"):
                id = file.split(".")[0]
                project_id, bug_id = id.split("_")
                if project_id not in project_bugnum:
                    project_bugnum[project_id] = 0
                project_bugnum[project_id] += 1
    projects = sorted(project_bugnum.keys())
    for project in projects:
        print(project_bugnum[project])

# get_defects4j_bugnum()