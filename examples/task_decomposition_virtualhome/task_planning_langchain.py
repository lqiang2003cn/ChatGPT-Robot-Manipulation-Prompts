import json
import os
import time

import tiktoken
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from virtualhome.simulation.unity_simulator.comm_unity import UnityCommunication

import prompt.prompts as pt

enc = tiktoken.get_encoding("cl100k_base")

dir_system = './system'
dir_prompt = './prompt'
dir_query = './query'
prompt_load_order = ['prompt_role',
                     'prompt_function',
                     'prompt_environment',
                     'prompt_output_format',
                     'prompt_example']


def reset(comm, scene_index=None):
    response = comm.post_command(
        {'id': str(time.time()), 'action': 'reset', 'intParams': [] if scene_index is None else [scene_index]}
    )
    return response['success']


def generate_script(input_array):
    output_array = []
    for action in input_array:

        action = action.replace(">", "").replace("<", "").replace(" ", "")
        # Split the action into its constituent parts
        parts = action.split('(')
        verb = parts[0].lower()
        arguments = parts[1].strip(')')
        # Check if there are any objects
        if len(arguments) == 0:
            objects = []
        else:
            objects = arguments.split(',')
            objects = [obj.split('_') for obj in objects]
        # Create the output string
        if len(objects) == 0:
            output_array.append('<char0> [{}]'.format(verb))
        elif len(objects) == 1:
            obj_type, obj_id = objects[0]
            output_array.append(
                '<char0> [{}] <{}> ({})'.format(
                    verb, obj_type, obj_id))
        else:
            obj1_type, obj1_id = objects[0]
            obj2_type, obj2_id = objects[1]
            output_array.append(
                '<char0> [{}] <{}> ({}) <{}> ({})'.format(
                    verb, obj1_type, obj1_id, obj2_type, obj2_id))

    return output_array


def remove_brackets(name):
    return name.replace('<', '').replace('>', '')


def which_room(graph_param, node_id):
    # Create a mapping from each node ID to its corresponding node data
    id_to_node = {node['id']: node for node in graph_param['nodes']}
    # Create a mapping from child node ID to its parent node ID
    child_to_parent = {}
    for edge in graph_param['edges']:
        if edge['from_id'] in child_to_parent.keys():
            child_to_parent[edge['from_id']].append(
                (edge['to_id'], edge['relation_type']))
        else:
            child_to_parent[edge['from_id']] = [
                (edge['to_id'], edge['relation_type'])]
    if node_id not in child_to_parent.keys():
        return None
    # Find the parent node ID(s) of the input node
    parent_node_ids = child_to_parent[node_id]
    # Iterate over all parent node IDs
    for parent_node_id in parent_node_ids:
        # Check if the parent node is a room
        if 'Rooms' in id_to_node[parent_node_id[0]]['category']:
            # Return the name of the room
            return id_to_node[parent_node_id[0]]['class_name']
    # If no room is found, return None
    return None


def find_parent_node(graph_param, node_name, room_name):
    # Create a mapping from each node ID to its corresponding node data
    id_to_node = {node['id']: node for node in graph_param['nodes']}
    name_to_id = {}
    for node in graph_param['nodes']:
        if node['class_name'] in name_to_id.keys():
            name_to_id[node['class_name']].append(node['id'])
        else:
            name_to_id[node['class_name']] = [node['id']]
    child_to_parent = {}
    for edge in graph_param['edges']:
        if edge['from_id'] in child_to_parent.keys():
            child_to_parent[edge['from_id']].append(
                (edge['to_id'], edge['relation_type']))
        else:
            child_to_parent[edge['from_id']] = [
                (edge['to_id'], edge['relation_type'])]
    if '_' in node_name:
        node_ids = [int(node_name.split('_')[1])]
        node_name = node_name.split('_')[0]
    else:
        # Find the node ID of the input node name
        if node_name not in name_to_id.keys():
            return None
        node_ids = name_to_id[node_name]
        # print(node_ids)
        node_ids = [node_id for node_id in node_ids if which_room(graph_param, node_id) == room_name]
        # print(node_ids)
    return_dict = {"object_states": {}, "asset_states": {}}
    for node_id in node_ids:
        if 'GRABBABLE' in id_to_node[node_id]['properties']:
            key_to_add = "object_states"
        else:
            key_to_add = "asset_states"
        # Find the parent node ID(s) of the input node
        if node_id not in child_to_parent.keys():
            return None
        else:
            parent_node_ids = child_to_parent[node_id]

        # Iterate over all parent node IDs
        for parent_node_id in parent_node_ids:
            parent_node = id_to_node[parent_node_id[0]]
            relation_type = parent_node_id[1]
            # focus only in and on
            if relation_type != 'INSIDE' and relation_type != 'ON':
                continue
            if 'Decor' in parent_node['category']:
                continue
            # print(parent_node['class_name'], parent_node_id[1])
            if "<{}_{}>".format(node_name, node_id) in return_dict[key_to_add].keys():
                return_dict[key_to_add]["<{}_{}>".format(node_name, node_id)].append(
                    "{}(<{}_{}>)".format(relation_type, parent_node['class_name'], parent_node_id[0])
                )
            else:
                return_dict[key_to_add]["<{}_{}>".format(node_name, node_id)] = \
                    ["{}(<{}_{}>)".format(relation_type, parent_node['class_name'], parent_node_id[0])]
    return return_dict


def populate_environment(graph_param, start_objects, start_room):
    environment_result = {
        "assets": [],
        "asset_states": {},
        "objects": [],
        "object_states": {},
    }
    # Create a mapping from each node ID to its corresponding node data
    id_to_node = {node['id']: node for node in graph_param['nodes']}
    # note that there are multiple nodes with the same class name
    name_to_id = {}
    for node in graph_param['nodes']:
        if node['class_name'] in name_to_id.keys():
            name_to_id[node['class_name']].append(node['id'])
        else:
            name_to_id[node['class_name']] = [node['id']]
    # Create a mapping from child node ID to its parent node ID
    child_to_parent = {}
    for edge in graph_param['edges']:
        if edge['from_id'] in child_to_parent.keys():
            child_to_parent[edge['from_id']].append((edge['to_id'], edge['relation_type']))
        else:
            child_to_parent[edge['from_id']] = [(edge['to_id'], edge['relation_type'])]
    objects_to_check = [remove_brackets(name) for name in start_objects]

    while objects_to_check:
        current_object = objects_to_check.pop()
        # print(objects_to_check)
        if "<{}>".format(current_object) not in environment_result["objects"] and \
                "<{}>".format(current_object) not in environment_result["assets"]:
            # add to the environment
            if 'GRABBABLE' in id_to_node[int(current_object.split('_')[-1])]['properties']:
                environment_result["objects"].append("<{}>".format(current_object))
            else:
                environment_result["assets"].append("<{}>".format(current_object))

            # find the parent and add the relationship to the environment
            parent_info = find_parent_node(graph_param, remove_brackets(current_object), start_room)
            if parent_info is not None:
                if "object_states" in parent_info:
                    for obj, states in parent_info["object_states"].items():
                        # add states to the environment
                        environment_result["object_states"]["<{}>".format(remove_brackets(obj))] = ["{}(<{}>)".format(
                            state.split('(')[0], remove_brackets(state.split('(')[-1].split(')')[0])) for state in states]
                        # add the new objects involved in the states to the
                        # list of objects to check
                        for state in states:
                            involved_object = remove_brackets(state.split('(')[-1].split(')')[0])
                            if "<{}>".format(involved_object) not in environment_result["objects"] and \
                                    "<{}>".format(involved_object) not in environment_result["assets"]:
                                objects_to_check.append(involved_object)
                if "asset_states" in parent_info:
                    for obj, states in parent_info["asset_states"].items():
                        # add states to the environment
                        environment_result["asset_states"]["<{}>".format(remove_brackets(obj))] = [
                            "{}(<{}>)".format(state.split('(')[0], remove_brackets(state.split('(')[-1].split(')')[0])) for state
                            in states
                        ]
                        # add the new assets involved in the states to the list
                        # of assets to check
                        for state in states:
                            # remove brackets while keeping the ID
                            involved_asset = remove_brackets(state.split(
                                '(')[-1].split(')')[0])  # remove the ID and brackets
                            if "<{}>".format(involved_asset) not in environment_result["assets"] and "<{}>".format(
                                    involved_asset) not in environment_result["objects"]:
                                objects_to_check.append(involved_asset)
    # want to add 'object_properties' to the environment
    asset_properties = {}
    for asset in environment_result['asset_states']:
        asset_id = asset.strip('>').strip('<').split('_')[1]
        tmp_properties = []
        if "CAN_OPEN" in id_to_node[int(asset_id)]['properties']:
            tmp_properties.append("IS_OPENABLE")
        else:
            tmp_properties.append("NOT_OPENABLE")
        asset_properties[asset] = tmp_properties
    environment_result['asset_properties'] = asset_properties
    object_properties = {}
    for obj in environment_result['object_states']:
        obj_id = obj.strip('>').strip('<').split('_')[1]
        tmp_properties = []
        if "CAN_OPEN" in id_to_node[int(obj_id)]['properties']:
            tmp_properties.append("IS_OPENABLE")
        else:
            tmp_properties.append("NOT_OPENABLE")
        object_properties[obj] = tmp_properties
    environment_result['object_properties'] = object_properties
    return environment_result


def find_unique_objects(graph_param, object_name, start_room):
    hit_object = find_parent_node(graph_param, object_name, start_room)
    if hit_object is None:
        return []
    if len(hit_object['object_states']) > 0:
        object_list = hit_object['object_states'].keys()
    elif len(hit_object['asset_states']) > 0:
        object_list = hit_object['asset_states'].keys()
    else:
        # error
        raise ValueError('No object found')
    return list(object_list)


def extract_objects(script_param):
    objects_all = []
    for action in script_param:
        parts = action.split('(')
        arguments = parts[1].replace(" ", "").strip(')')
        # Check if there are any objects
        if len(arguments) == 0:
            objects = []
        else:
            objects = arguments.split(',')
        objects_all.extend(objects)
    return list(set(objects_all))


class ChatGPTAgent:
    def __init__(self):
        self.json_dict = None
        self.environment = None
        self.messages = []
        self.max_token_length = 15000  # 4000
        self.max_completion_length = 2000  # 1300
        self.instruction = ''
        self.comm = UnityCommunication()

        # langchain implementation
        self.messages_pt = ChatPromptTemplate.from_messages([
            ('system', pt.system_prompt),
            ('human', pt.role_prompt_user),
            ('ai', pt.role_prompt_ai),
            ('human', pt.function_prompt_user),
            ('ai', pt.function_prompt_ai),
            ('human', pt.env_prompt_user),
            ('ai', pt.env_prompt_ai),
            ('human', pt.output_format_prompt_user),
            ('ai', pt.output_format_prompt_ai),
            ('human', pt.example_prompt_user),
            ('ai', pt.example_prompt_ai),
            ('human', pt.query_prompt_user)
        ])
        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-1106")
        self.chain = self.messages_pt | self.llm
        self.responses = {}

    def generate(self, curr_instruction, curr_env, is_user_feedback=False):
        if is_user_feedback:
            self.messages_pt.append(('humane', curr_instruction))
        variables = {
            "env_prompt_user_example": pt.env_prompt_user_example,
            "example_prompt_user_example_input": pt.example_prompt_user_example_input,
            "example_prompt_user_example_output": pt.example_prompt_user_example_output,
            "curr_env": curr_env,
            "curr_instruction": curr_instruction
        }
        variables.update(self.responses)
        curr_messages = self.messages_pt.format_messages(**variables)
        for m in curr_messages:
            print('####################################', m.type, '####################################\n', m.content)
        response = self.chain.invoke(variables)

        response_num = "{response_" + str(len(self.responses)) + "}"
        self.responses[response_num] = response.content
        self.messages_pt.append(("ai", response_num))
        try:
            self.json_dict = json.loads(response.content, strict=False)
            self.environment = self.json_dict["environment_after"]
        except BaseException as e:
            print(e)
            self.json_dict = None
            return None
        return self.json_dict

    def execution_script(self, script_param, result_param):
        self.comm.reset(0)
        print('Starting scene...')
        self.comm.add_character('Chars/Male2', initial_room='kitchen')
        for i, script_atom in enumerate(script_param):
            task = result_param["task_cohesion"]["task_sequence"][i]
            task_atom = script_atom.split("[")[1].split("]")[0]
            ret = self.comm.render_script([script_atom], frame_rate=10, recording=True)
            if ret[0] is False:
                feedback = "You are wrong! Modify your answer. The following line failed in a simulator: " + task + "\n" + \
                           "The verb {" + task_atom + "} is not applicable to the object(s). Refer to \'HUMAN ACTION LIST\' in my instruction."
                return feedback
        return None


if __name__ == '__main__':
    dir_name = "out_task_planning_gpt-3.5-turbo-16k_temp=2.0"
    agent = ChatGPTAgent()
    max_trial = 5
    for scenario_id in range(1, 15):
        for trial_idx in range(max_trial):
            print(f"scenario_id={scenario_id}, trial_idx={trial_idx}")
            scenario_name = 'scenario_' + str(scenario_id)
            dump_name = './' + dir_name + f'/{scenario_name}/{trial_idx}'
            fp = os.path.join(dump_name + '.json')
            if os.path.exists(fp):
                continue
            with open('scenarios/' + str(scenario_id) + '.json') as f:
                scenario = json.load(f)
            instructions = scenario['instructions']
            reference_program = scenario['program']
            print(f"instructions(scenario_id={scenario_id}): {instructions[0]}")

            s, graph = agent.comm.environment_graph()
            environment = populate_environment(graph, extract_objects(reference_program), "kitchen")
            scenario_name = 'scenario_' + str(scenario_id)
            if not os.path.exists('./' + dir_name + '/' + scenario_name):
                os.makedirs('./' + dir_name + '/' + scenario_name)

            # for each instruction, retry until the response is json
            max_retry_for_json = 5
            retry_for_json = 1
            result = agent.generate(instructions[0], environment, is_user_feedback=False)
            while retry_for_json <= max_retry_for_json:
                if result is not None:
                    break
                else:
                    retry_for_json += 1
                    print("api call failed. retrying...")
                    msg = "Your return cannot be interpreted as a valid json dictionary. Please reformat your response."
                    text = agent.generate(msg, environment, is_user_feedback=True)

            if result is None:
                continue

            print("running scripts generated by AI...")
            script = generate_script(result["task_cohesion"]["task_sequence"])
            user_feedback = agent.execution_script(script, result)
            if user_feedback is not None:
                # VirtualHome sometimes fails to execute the script even if the
                # script is correct, so retry once just in case.
                user_feedback = agent.execution_script(script, result)
            print('result of self test: ' + user_feedback)

            was_execution_successful = False
            if user_feedback is not None:
                was_execution_successful = False
            else:
                was_execution_successful = True
            dump_name = './' + dir_name + f'/{scenario_name}/{trial_idx}'
            fp = os.path.join(dump_name + '.json')
            agent.json_dict['was_execution_successful'] = was_execution_successful
            agent.json_dict['user_feedback'] = user_feedback
            with open(fp, 'w') as f:
                json.dump(agent.json_dict, f, indent=4)
