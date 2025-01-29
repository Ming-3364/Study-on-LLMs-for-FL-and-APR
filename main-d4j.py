from util.CondefectsDataset import *
from util.Defects4jDataset import *

defects4j_framework = "<defects4j_framework>" # your absolute path of defects4j_framework, e.g., "/path/to/defects4j-2.1.0/framework"
checkout_dir = '<checkout_dir>' # your absolute path of checkout_dir
output_dir = 'output/defects4j'
tmp_dir = 'tmp'

defects4j_generator = Defects4JGenerator(defects4j_framework, checkout_dir, output_dir, tmp_dir)
defects4j_generator.output_info()
defects4j_generator.output_prompt()
defects4j_generator.query_llm()
defects4j_generator.check_query_results_fl()
defects4j_generator.check_query_results_apr()
defects4j_generator.stat_check_results()

defects4j_generator.collect_apr_status_for_manual_check()