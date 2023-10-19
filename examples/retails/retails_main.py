import json

import tiktoken

from examples.retails.utils import ModelConfig, task_breakdown

if __name__ == '__main__':
    enc = tiktoken.get_encoding("cl100k_base")

    # model config for order collection
    # mc_order = ModelConfig()
    # mc_order.dir_prompt = 'prompt'
    # mc_order.dir_output = "output"
    # mc_order.prompt_load_order = ['order_collect.txt']
    # mc_order.prompt_query = 'order_query.txt'
    # with open('c.json') as f:
    #     mc_order.credentials = json.load(f)
    # mc_order.encoder = enc

    # collection order
    # order_environment = {'items': ['juice', 'water', 'cola', 'cookie', 'bread']}
    # order_instr = 'i am thirsty'
    # collected_item = collect_order(mc_order, order_instr, order_environment)

    # task config for task breakdown
    mc_task = ModelConfig()
    mc_task.dir_prompt = 'prompt'
    mc_task.dir_output = "output"
    mc_task.prompt_load_order = [
        'task_1_role.txt',
        'task_2_action.txt',
        'task_3_env.txt',
        'task_4_output.txt',
        'task_5_output.txt'
    ]
    mc_task.prompt_query = 'task_6_query.txt'
    with open('c.json') as f:
        mc_task.credentials = json.load(f)
    mc_task.encoder = enc

    # task breakdown
    task_environment = {'items': ['juice', 'water', 'cola', 'cookie', 'bread']}
    collected_item = 'juice'
    task_instr = 'pickup the ' + str(collected_item)
    task_breakdown(mc_task, task_instr, task_environment)

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
