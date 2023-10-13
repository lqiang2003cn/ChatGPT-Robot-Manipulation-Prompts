import json
import os
import re

import requests


class ChatGPT:
    def __init__(self, configs):
        self.json_dict = None
        self.environment = None
        self.credentials = json.load(open('c.json'), strict=False)
        self.messages = []
        self.max_token_length = 15000  # 4000
        self.max_completion_length = 2000  # 1300
        self.last_response = None
        self.last_response_raw = None
        self.query = ''
        self.instruction = ''
        # load prompt file
        fp_system = os.path.join(configs["system"])
        with open(fp_system) as fl:
            data = fl.read()
        self.system_message = {"role": "system", "content": data}

        for prompt_name in configs["prompt_load_order"]:
            fp_prompt = os.path.join(prompt_name)
            with open(fp_prompt) as fl:
                data = fl.read()
            data_split = re.split(r'\[user]\n|\[assistant]\n', data)
            data_split = [item for item in data_split if len(item) != 0]
            # it starts with user and ends with system
            assert len(data_split) % 2 == 0
            for i, item in enumerate(data_split):
                if i % 2 == 0:
                    self.messages.append({"sender": "user", "text": item})
                else:
                    self.messages.append({"sender": "assistant", "text": item})
        fp_query = os.path.join(configs["query"])
        with open(fp_query) as fl:
            self.query = fl.read()

    def create_prompt(self):
        prompt = [self.system_message]
        for message in self.messages:
            prompt.append({"role": message['sender'], "content": message['text']})
        prompt_content = ""
        for message in prompt:
            prompt_content += message["content"]

        # prompt_len = ut.get_token_count(prompt_content)
        # print('prompt length: ' + str(prompt_len))
        # if prompt_len > self.max_token_length - self.max_completion_length:
        #     print('prompt too long. truncated.')
        #     # truncate the prompt by removing the oldest two messages
        #     self.messages = self.messages[2:]
        #     prompt = self.create_prompt()

        return prompt

    @staticmethod
    def extract_json_part(text_input):
        # because the json part is in the middle of the text, we need to extract it.
        # json part is between ```python and ```.
        # skip if there is no json part
        if text_input.find('```python') == -1:
            return text_input
        text_json = text_input[text_input.find(
            '```python') + len('```python'):text_input.find('\n```')]
        text_json.replace('```', '')
        return text_json

    def generate(self, message, environment, is_user_feedback=False):
        if is_user_feedback:
            self.messages.append({'sender': 'user', 'text': message})
        else:
            text_base = self.query
            if text_base.find('[ENVIRONMENT]') != -1:
                text_base = text_base.replace('[ENVIRONMENT]', json.dumps(environment))
            if text_base.find('[INSTRUCTION]') != -1:
                text_base = text_base.replace('[INSTRUCTION]', message)
                self.instruction = text_base
            self.messages.append({'sender': 'user', 'text': text_base})

        response_text = self.call_gpt({
            "model": "gpt-3.5-turbo-16k-0613",
            # "model": "gpt-3.5-turbo-16k",
            'messages': self.create_prompt(),
            "temperature": 2.0,
            "max_tokens": self.max_completion_length,
            "top_p": 0.5,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        })
        self.last_response_raw = response_text
        self.messages.append({"sender": "assistant", "text": self.last_response_raw})
        # analyze the response
        self.last_response = response_text
        self.last_response = self.extract_json_part(self.last_response)
        # self.last_response = self.last_response.replace("'", "\"")
        try:
            self.json_dict = json.loads(self.last_response, strict=False)
            self.environment = self.json_dict["environment_after"]
        except BaseException as e:
            print(e)
            self.json_dict = None
            return None
        return self.json_dict

    def call_gpt(self, json_data):
        headers = {"Authorization": "Bearer " + self.credentials["api_key"]}
        session = requests.Session()
        session.trust_env = False
        response = session.post(
            self.credentials["api_base"],
            headers=headers,
            json=json_data
        ).json()
        resp_text = response['choices'][0]['message']['content']
        return resp_text

#
# if __name__ == "__main__":
#     global_configs = {
#         "system": "block_p01_system.txt",
#         "prompt_load_order": [
#             "block_p02_role.txt",
#             "block_p03_env.txt",
#             "block_p04_function.txt",
#             "block_p05_output.txt",
#             "block_p06_example.txt"
#         ],
#         "query": "block_p07_query.txt",
#     }
#     gpt = ChatGPT(global_configs)
#
#     input_json = {
#         "environment": {
#             "assets": [
#                 "<table_777>",
#                 "<floor_888>"
#             ],
#             "asset_states": {
#                 "<table_111>": ["ON(<floor_888>)"]
#             },
#             "objects": [
#                 "<block_001>",
#                 "<block_009>"
#             ],
#             "object_states": {
#                 "<block_001>": ["ON(<block_009>)"],
#                 "<block_009>": ["ON(<table_111>)"]
#             }
#         },
#         "instructions": [
#             "put block 009 on top of block 001"
#         ],
#     }
#
#     json_dict = gpt.generate(input_json["instructions"][0], input_json["environment"], is_user_feedback=False)
#     time_str = time.strftime("%Y%m%d-%H%M%S")
#     json_file_name = "../json_files/result_" + time_str + ".json"
#     with open(json_file_name, 'w') as fp:
#         json.dump(json_dict, fp)
