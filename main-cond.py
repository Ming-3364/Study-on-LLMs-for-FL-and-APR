from util.CondefectsDataset import *
from util.Defects4jDataset import *

condefects_home = "<condefects_home>" # your absolute path of condefects_home, e.g., "/path/to/ConDefects"
condefects_checkout_dir = "<checkout_dir>" # your absolute path of checkout_dir
time_from = "2024-03-01"
time_to = "2024-06-30"
output_dir = 'output/condefects'
tmp_dir = 'tmp'

condefects_generator = CondefectsGenerator(condefects_home, condefects_checkout_dir, time_from, time_to, "Java", "", output_dir, tmp_dir)
condefects_generator.output_info()
condefects_generator.output_prompt()
condefects_generator.query_llm()
condefects_generator.check_query_results_fl()
condefects_generator.check_query_results_apr()
condefects_generator.stat_check_results()

condefects_generator.collect_apr_status_for_manual_check()