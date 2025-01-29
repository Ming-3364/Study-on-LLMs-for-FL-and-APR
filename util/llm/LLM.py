from openai import OpenAI
import json
import tiktoken

class LLM:
    def __init__(self, base_url, api_key, model, max_tokens=None):
        self.client = OpenAI(
            base_url = base_url,
            api_key = api_key
        )
        self.model = model
        self.max_tokens = max_tokens

    def truncate_prompt(self, prompt, max_tokens):
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(prompt)
        if len(tokens) > max_tokens:
            truncated_prompt = encoding.decode(tokens[-max_tokens:])
            return truncated_prompt
        return prompt

    def query(self, prompt):
        try:
            # if self.model == "deepseek-chat":
            #     raise Exception("deepseek-chat is not supported")
            # return "xxx"

            if self.max_tokens:
                prompt = self.truncate_prompt(prompt, self.max_tokens)
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(e)
            return None

    def test(self, prompt="hello"):
        print(self.query(prompt))

    def print_models(self):
        models = self.client.models.list()
        print(models)

if __name__ == "__main__":
    base_url = ""
    api_key = ""
    model = "gpt-4o-mini"
    llm = LLM(base_url, api_key, model)
    llm.print_models()
    llm.test()
