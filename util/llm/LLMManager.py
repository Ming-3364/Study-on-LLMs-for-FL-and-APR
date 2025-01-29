from .LLM import LLM
from tqdm import tqdm
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class LLMManager:
    def __init__(self):
        self.llm_info = {
            # config your llm here
            # e.g.
            # "llm_name": {
            #     "base_url": "xxx",
            #     "api_key": "xxx"
            #     "model": "gpt-4o-mini",
            # }
        }


    def get_llm(self, llm_name):
        llm_config = self.llm_info[llm_name]
        base_url = llm_config["base_url"]
        api_key = llm_config["api_key"]
        model = llm_config["model"]
        max_tokens = llm_config["max_tokens"]
        return LLM(base_url, api_key, model, max_tokens)


    def query_llm(self, llm_name, prompt):
        llm = self.get_llm(llm_name)
        res = llm.query(prompt)
        return res

    def query_all_llm(self, prompt):
        results = {}
        try:
            with ThreadPoolExecutor(max_workers=len(self.llm_info.keys())) as executor:
                futures = {}
                for llm_name in self.llm_info.keys():
                    future = executor.submit(self.query_llm, llm_name, prompt)
                    futures[future] = llm_name
                for future in tqdm(as_completed(futures), total=len(futures), desc="Querying different llms...", leave=False):
                    llm_name = futures[future]
                    results[llm_name] = future.result()
        except Exception as e:
            assert False, f"Failed to query all llms: {str(e)}"
        for llm_name, res in results.items():
            if res is None:
                assert False, f"Failed to query {llm_name}"
        return results
    
    def get_llm_id_list(self):
        return list(self.llm_info.keys())

    def test(self, prompt="hello"):
        res = {}
        for llm_name in self.llm_info.keys():
            try:
                res[llm_name] = self.query_llm(llm_name, prompt)
            except Exception as e:
                res[llm_name] = str(e)
        print(json.dumps(res, indent=4))

if __name__ == "__main__":
    llm_manager = LLMManager()
    llm_manager.test()