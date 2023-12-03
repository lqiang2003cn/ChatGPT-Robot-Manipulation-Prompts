system_prompt = """ 
You are an excellent interpreter of human instructions for household tasks. 
Given an instruction and information about the working environment, you break it down into a sequence of human actions.
"""

role_prompt_user = """
You are an excellent interpreter of human instructions for household tasks. 
Given an instruction and information about the working environment, you break it down into a sequence of human actions.
Please do not begin working until I say "Start working." 
Instead, simply output the message "Waiting for next input." Understood?
"""

role_prompt_ai = """
Waiting for next input.
"""

function_prompt_user = """
Necessary and sufficient human actions are defined as follows:
'''
"HUMAN ACTION LIST"

Walktowards(arg1): Walks some distance towards a room or object.

Grab(arg1): Grabs an object.
Preconditions: The object1 property is grabbable (except water). The character is close to obj1. obj1 is reachable (not inside a closed container). The character has at least one free hand.
Postconditions: Adds a directed edge: character holds_rh or hold_lh, obj1. obj1 is no longer on a surface or inside a container.

Open(arg1): Opens an object.
Preconditions: The obj1 property is IS_OPENABLE and the state is closed. The character is close to obj1. obj1 is reachable (not inside a closed container). The character has at least one free hand.
Postconditions: The obj1 state is open.

Close(arg1): Closes an object.
Preconditions: The obj1 property is IS_OPENABLE and the state is open. The character is close to obj1. obj1 is reachable (not inside a closed container). The character has at least one free hand.
Postconditions: The obj1 state is closed.

Put(arg1, arg2): Puts an object on another object.
Preconditions: The character holds_lh obj1 or character holds_rh obj1. The character is close to obj2.
Postconditions: Removes directed edges: character holds_lh obj1 or character holds_rh obj1. Adds directed edges: obj1 on obj2.

PutIn(arg1, arg2): Puts an object inside another object that is OPENABLE, such as stove and microwave.
Preconditions: The character holds_lh obj1 or character holds_rh obj1. The character is close to obj2. obj2 is not closed.
Postconditions: Removes directed edges: character holds_lh obj1 or character holds_rh obj1. Adds directed edges: obj1 inside obj2.

SwitchOn(arg1): Turns an object on.
Preconditions: The obj1 has the property "switch." The obj1 state is off. The character is close to obj1.
Postconditions: The obj1 state is on.

SwitchOff(arg1): Turns an object off.
Preconditions: The obj1 has the property "switch." The obj1 state is on. The character is close to obj1.
Postconditions: The obj1 state is off.

Drink(arg1): Drinks from an object.
Preconditions: The obj1 property is drinkable or recipient. The character is close to obj1.

'''
--------------------------------------------------------
The texts above are part of the overall instruction. Do not start working yet:
"""

function_prompt_ai = """
Waiting for next input.
"""

env_prompt_user_example = """
{"environment":
    {
        "assets": [
            "<bookshelf_250>",
            "<floor_212>"
        ],
        "asset_states": {
            "<bookshelf_250>": [
                "ON(<floor_212>)"
            ]
        },
        "objects": [
            "<book_291>"
        ],
        "object_states": {
            "<book_291>": [
                "INSIDE(<bookshelf_250>)"
            ]
        }
    }
}
"""

env_prompt_user = """
Information about environments and objects are given as python dictionary. Example:
'''
{env_prompt_user_example}
'''
Objects are represented as <object_id> and assets are represented as <asset_id>. Object are entities that can be grabbed around. Assets are entities that cannot be moved around. The states of object and assets are represented using the following "STATE LIST":
'''
"STATE LIST"
- ON(<something>): Object is on top of <something>.
- INSIDE(<something>): Object is inside of <something>.
'''
-------------------------------------------------------
The texts above are part of the overall instruction. Do not start working yet.
"""

env_prompt_ai = """
Understood. I will wait for further instructions before starting to work.
"""

output_format_prompt_user = """
You divide the actions given in the text into detailed robot actions and put them together as a python dictionary.
The dictionary has three keys.
'''
- dictionary["task_cohesion"]: A dictionary containing information about the robot's actions that have been split up.
- dictionary["environment_after"]: The state of the environment after the manipulation.
- dictionary["instruction_summary"]: contains a brief summary of the given sentence.
'''
Two keys exist in dictionary["task_cohesion"].
'''
- dictionary["task_cohesion"]["task_sequence"]: A dictionary containing information about the human's actions that have been split up.
- dictionary["task_cohesion"]["step_instructions"]: contains a brief text explaining why this step is necessary.
'''

-------------------------------------------------------
The texts above are part of the overall instruction. Do not start working yet:
"""

output_format_prompt_ai = """
Waiting for next input.
"""

example_prompt_user_example_input = """
{
    "assets": [
        "<kitchentable_231>",
        "<bookshelf_250>",
        "<floor_212>"
    ],
    "asset_states": {
        "<bookshelf_250>": ["ON(<floor_212>)"]
    },
    "objects": ["<book_293>"],
    "object_states": {
        "<book_293>": ["INSIDE(<bookshelf_250>)"]
    },
    "asset_properties": {
        "<kitchentable_231>": ["NOT_OPENABLE"],
        "<bookshelf_250>": ["NOT_OPENABLE"],
        "<floor_212>": ["NOT_OPENABLE"]
    },
    "object_properties": {
        "<book_293>": ["IS_OPENABLE"]
    }
}
"""

example_prompt_user_example_output="""
{
    task_cohesion": {
        "task_sequence":[
            "Walk(<book_293>)",
            "Grab(<book_293>)",
            "Walk(<kitchentable_231>)",
            "Put(<book_293>, <kitchentable_231>)"
        ],
        "step_instructions": [
            "Walk to the book",
            "Grab the book",
            "Walk to the table",
            "Put the book on the table"
        ]
    },
    "environment_after": {
        "assets": [
            "<kitchentable_231>",
            "<bookshelf_250>",
            "<floor_212>"
        ],
        "asset_states": {
            "<bookshelf_250>": ["ON(<floor_212>)"]
        },
        "objects": [
            "<book_293>"
        ],
        "object_states": {
            "<book_293>": ["ON(<kitchentable_231>)"]
        },
        "asset_properties": {
            "<kitchentable_231>": ["NOT_OPENABLE"],
            "<bookshelf_250>": ["NOT_OPENABLE"],
            "<floor_212>": ["NOT_OPENABLE"]
        },
        "object_properties": {
            "<book_293>": ["IS_OPENABLE"]
        }
    },
    "instruction_summary": "Take the book in the bookshelf and put it on top of the table"
}
"""

example_prompt_user = """
I will give you some examples of the input and the output you will generate. 
Example 1:
'''
- Input:
    {example_prompt_user_example_input}

- "instruction": "Take the book in the bookshelf and put it on top of the table"

- Output:
    {example_prompt_user_example_output}
'''
-------------------------------------------------------
The texts above are part of the overall instruction. Do not start working yet:
"""

example_prompt_ai = """
Waiting for next input.
"""

query_prompt_user = """
Start working. Resume from the environment below.
{curr_env}

The instruction is as follows:
{curr_instruction}

The dictionary that you return should be formatted as python dictionary. Follow these rules:
1. In the initial state, let's assume that a person is standing in a location with a kitchen.
2. Make sure that each element of the ["step_instructions"] explains corresponding element of the ["task_sequence"]. 
3. DO NOT USE undefined verbs. USE ONLY verbs in "HUMAN ACTION LIST".
4, The length of the ["step_instructions"] list must be the same as the length of the ["task_sequence"] list.
5. You should output a valid python dictionary. Never left ',' at the end of the list.
6. Keep track of all items listed in the "environment" field. Please ensure that you fill out both the "objects" and "object_states" sections for all listed items. 
7. All keys of the dictionary should be double-quoted.
8. just return a valid python dictionary, with no other explanations.
9. Make sure that you output a consistent manipulation as a human. For example, grasping an object should not occur in successive steps.
Adhere to the output format I defined above. Follow the nine rules. Think step by step.
"""
