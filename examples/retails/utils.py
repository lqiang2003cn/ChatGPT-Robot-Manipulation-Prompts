import json
import os
import re

import requests


class ModelConfig:

    def __init__(self):
        self.dir_prompt = None
        self.dir_output = None
        self.prompt_system = None
        self.prompt_user = None
        self.prompt_query = None
        self.credentials = None
        self.encoder = None


def extract_json_part(text_param):
    # because the json part is in the middle of the text, we need to extract it.
    # json part is between ```python and ```.
    # skip if there is no json part
    if text_param.find('```python') == -1:
        return text_param
    text_json = text_param[text_param.find(
        '```python') + len('```python'):text_param.find('\n```')]
    text_json.replace('```', '')
    return text_json


class ChatGPT:
    def __init__(self, model_config: ModelConfig):
        self.mc = model_config
        self.json_dict = None
        self.environment = None
        self.messages = []
        self.max_token_length = 15000  # 4000
        self.max_completion_length = 2000  # 1300
        self.last_response = None
        self.last_response_raw = None
        self.query = ''
        self.instruction = ''
        self.system_message = None

        if self.mc.prompt_system is not None:
            self.system_message = {"role": "system", "content": self.mc.prompt_system}

        for prompt_name in self.mc.prompt_load_order:
            fp_prompt = os.path.join(self.mc.dir_prompt, prompt_name)
            with open(fp_prompt) as fb:
                data = fb.read()
            data_split = re.split(r'\[user]\n|\[assistant]\n', data)
            data_split = [item for item in data_split if len(item) != 0]
            # it starts with user and ends with system
            assert len(data_split) % 2 == 0
            for i, item in enumerate(data_split):
                if i % 2 == 0:
                    self.messages.append({"sender": "user", "text": item})
                else:
                    self.messages.append({"sender": "assistant", "text": item})

        fp_query = os.path.join(self.mc.dir_prompt, self.mc.prompt_query)
        with open(fp_query) as fb:
            self.query = fb.read()

    def create_prompt(self):
        prompt = []
        if self.system_message is not None:
            prompt.append(self.system_message)
        for message in self.messages:
            prompt.append({"role": message['sender'], "content": message['text']})
        prompt_content = ""
        for message in prompt:
            prompt_content += message["content"]

        # print('prompt length: ' + str(len(enc.encode(prompt_content))))
        if len(self.mc.encoder.encode(prompt_content)) > self.max_token_length - self.max_completion_length:
            print('prompt too long. truncated.')
            # truncate the prompt by removing the oldest two messages
            self.messages = self.messages[2:]
            prompt = self.create_prompt()
        return prompt

    def generate(self, message, environment_param, is_user_feedback=False):
        # Remove unsafe user inputs. May need further refinement in the future.
        if message.find('<|im_start|>') != -1:
            message = message.replace('<|im_start|>', '')
        if message.find('<|im_end|>') != -1:
            message = message.replace('<|im_end|>', '')

        if is_user_feedback:
            self.messages.append({'sender': 'user', 'text': message})
        else:
            text_base = self.query
            if text_base.find('[ENVIRONMENT]') != -1:
                text_base = text_base.replace('[ENVIRONMENT]', json.dumps(environment_param))
            if text_base.find('[INSTRUCTION]') != -1:
                text_base = text_base.replace('[INSTRUCTION]', message)
                self.instruction = text_base
            self.messages.append({'sender': 'user', 'text': text_base})

        prompt = self.create_prompt()

        json_data = {
            "model": "gpt-3.5-turbo-16k-0613",
            'messages': prompt,
            "temperature": 0.0,
            "max_tokens": self.max_completion_length,
            "top_p": 0.5,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        headers = {"Authorization": "Bearer " + self.mc.credentials["api_key"]}
        session = requests.Session()
        # session.trust_env = False
        response = session.post(self.mc.credentials["api_base"], headers=headers, json=json_data).json()
        text_response = response['choices'][0]['message']['content']
        self.last_response_raw = text_response
        self.messages.append({"sender": "assistant", "text": self.last_response_raw})
        # analyze the response
        self.last_response = text_response
        self.last_response = extract_json_part(self.last_response)
        self.last_response = self.last_response.replace("'", "\"")
        try:
            self.json_dict = json.loads(self.last_response, strict=False)
        except BaseException as e:
            print(e)
            self.json_dict = None
            return None
        return self.json_dict


def collect_order(mc_p, instruction_p, environment_p):
    aimodel = ChatGPT(mc_p)
    text = aimodel.generate(instruction_p, environment_p, is_user_feedback=False)
    print(text)

    # collect order
    while True:
        if text['state'] == 'succeed':
            print('order collection succeeds')
            break

        # user_feedback = input('user feedback (return empty if satisfied): ')
        user_feedback = 'OK'
        if user_feedback != '':
            text = aimodel.generate(user_feedback, environment_p, is_user_feedback=True)
            print(text)
        else:
            print('user quit')
            break

    return text['item']


def task_breakdown(mc_p, instruction_p, environment_p):
    aimodel = ChatGPT(mc_p)
    text = aimodel.generate(instruction_p, environment_p, is_user_feedback=False)
    print(text)

    while True:
        user_feedback = ''
        if user_feedback != '':
            text = aimodel.generate(user_feedback, environment_p, is_user_feedback=True)
            print(text)
        else:
            print('user quit')
            break

    return text['item']
