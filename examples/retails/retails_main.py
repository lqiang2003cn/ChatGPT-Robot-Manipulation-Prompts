import json
import os
import re

import requests
import tiktoken


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
    def __init__(self, credentials_param, prompt_load_order_param):
        self.json_dict = None
        self.environment = None
        self.credentials = credentials_param
        self.messages = []
        self.max_token_length = 15000  # 4000
        self.max_completion_length = 2000  # 1300
        self.last_response = None
        self.last_response_raw = None
        self.query = ''
        self.instruction = ''
        # load prompt file
        fp_system = os.path.join(dir_system, 'system.txt')
        with open(fp_system) as fb:
            data = fb.read()
        self.system_message = {"role": "system", "content": data}

        for prompt_name in prompt_load_order_param:
            fp_prompt = os.path.join(dir_prompt, prompt_name + '.txt')
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
        fp_query = os.path.join(dir_query, 'query.txt')
        with open(fp_query) as fb:
            self.query = fb.read()

    def create_prompt(self):
        prompt = [self.system_message]
        for message in self.messages:
            prompt.append(
                {"role": message['sender'], "content": message['text']})
        prompt_content = ""
        for message in prompt:
            prompt_content += message["content"]

        print('prompt length: ' + str(len(enc.encode(prompt_content))))
        if len(enc.encode(prompt_content)) > self.max_token_length - \
                self.max_completion_length:
            print('prompt too long. truncated.')
            # truncate the prompt by removing the oldest two messages
            self.messages = self.messages[2:]
            prompt = self.create_prompt()
        return prompt

    def generate(self, message, environment_param, is_user_feedback=False):
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

        json_data = {
            "model": "gpt-3.5-turbo-16k-0613",
            'messages': self.create_prompt(),
            "temperature": 2.0,
            "max_tokens": self.max_completion_length,
            "top_p": 0.5,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        headers = {"Authorization": "Bearer " + self.credentials["api_key"]}
        session = requests.Session()
        # session.trust_env = False
        response = session.post(self.credentials["api_base"], headers=headers, json=json_data).json()
        text_response = response['choices'][0]['message']['content']
        self.last_response_raw = text_response
        self.messages.append({"sender": "assistant", "text": self.last_response_raw})
        # analyze the response
        self.last_response = text_response
        self.last_response = extract_json_part(self.last_response)
        self.last_response = self.last_response.replace("'", "\"")
        try:
            self.json_dict = json.loads(self.last_response, strict=False)
            self.environment = self.json_dict["environment_after"]
        except BaseException as e:
            print(e)
            self.json_dict = None
            return None
        return self.json_dict


if __name__ == '__main__':
    enc = tiktoken.get_encoding("cl100k_base")
    with open('c.json') as f:
        credentials = json.load(f)
    dir_system = './system'
    dir_prompt = './prompt'
    dir_query = './query'
    prompt_load_order = ['prompt_role',
                         'prompt_function',
                         'prompt_environment',
                         'prompt_output_format',
                         'prompt_example']
    dir_name = "output"
    environment = ['juice', 'water', 'cola', 'cookie', 'bread']
    instruction = input('customer input:')
    aimodel = ChatGPT(credentials, prompt_load_order)
    text = aimodel.generate(instruction, environment, is_user_feedback=False)
    while True:
        user_feedback = input('user feedback (return empty if satisfied): ')
        if user_feedback == 'q':
            print('exit')
            exit()
        if user_feedback != '':
            print('not empty user feedback')
            text = aimodel.generate(user_feedback, environment, is_user_feedback=True)
        else:
            # update the current environment
            print('update environment')
            environment = aimodel.environment
            break

# if __name__ == '__main__':
#     dir_name = "output"
#     waittime_sec = 30
#     max_trial = 100
#     trial_idx = 0
#     user_feedback = ""
#     time_api_called = time.time() - waittime_sec
#     environment = ['juice', 'water', 'cola', 'cookie', 'bread']
#     instructions = input('customer input:')
#     aimodel = None
#     while trial_idx < max_trial:
#         while True:
#             # if api is called within 60 seconds, wait
#             current_time = time.time()
#             if current_time - time_api_called < waittime_sec:
#                 print("waiting for " + str(waittime_sec - (current_time - time_api_called)) + " seconds...")
#                 time.sleep(waittime_sec - (current_time - time_api_called))
#             if trial_idx == 0:
#                 aimodel = ChatGPT_api(credentials, prompt_load_order=prompt_load_order)
#                 text = aimodel.generate(instructions[0], environment, is_user_feedback=False)
#             else:  # trial_idx > 0: # use user feedback
#                 assert user_feedback != ""
#                 text = aimodel.generate(user_feedback, environment, is_user_feedback=True)
#                 time_api_called = time.time()
#             if text is not None:
#                 break
#             else:
#                 print("api call failed. retrying...")
#                 current_time = time.time()
#                 if current_time - time_api_called < waittime_sec:
#                     print("waiting for " + str(waittime_sec - (current_time - time_api_called)) + " seconds...")
#                     time.sleep(waittime_sec - (current_time - time_api_called))
#                 uf = "Your return cannot be interpreted as a valid json dictionary. Please reformat your response."
#                 text = aimodel.generate(uf, environment, is_user_feedback=True)
#                 break
#         if text is None:
#             trial_idx = 5
#             print('Retry failed, AI model is not accessible')
#             break
#         print("self test is running...")
#         script = generate_script(text["task_cohesion"]["task_sequence"])
#         user_feedback = test_execution(comm, script)
#         if len(user_feedback) > 0:
#             # VirtualHome sometimes fails to execute the script even if the
#             # script is correct, so retry once just in case.
#             user_feedback = test_execution(comm, script)
#         print('result of self test: ' + user_feedback)
#         was_execution_successful = False
#         if len(user_feedback) > 0:
#             was_execution_successful = False
#         else:
#             was_execution_successful = True
#
#         dump_name = './' + dir_name + f'/{scenario_name}/{trial_idx}'
#         fp = os.path.join(dump_name + '.json')
#         aimodel.json_dict['was_execution_successful'] = was_execution_successful
#         aimodel.json_dict['user_feedback'] = user_feedback
#         with open(fp, 'w') as f:
#             json.dump(aimodel.json_dict, f, indent=4)
#         if not was_execution_successful:  # if execution was not successful, retry using the feedback
#             trial_idx += 1
#             if trial_idx == max_trial:
#                 break
#         else:
#             trial_idx = 5
#             break
