from openai import AsyncOpenAI
import json

client = AsyncOpenAI()
verbose = False

def valid_action (action):
  try:
    assert isinstance(action, dict)
    assert "type" in action
    assert action["type"] in ["seq", "min", "max", "rpc", "external rpc"]
    assert "args" in action
    assert not action["type"] == "rpc" or len(action["args"]) == 0
    assert not action["type"] == "external rpc" or len(action["args"]) == 1
    assert action["type"] not in ["seq", "min", "max"] or len(action["args"]) >= 2
    for arg in action["args"]:
      assert valid_action(arg) 
  except AssertionError:
    return False
  return True

def valid_node (node):
  try:
    assert isinstance(node, dict)
    assert "name" in node
    assert isinstance(node["name"], str)
    assert "service" in node
    assert isinstance(node["service"], str)
    assert "action" in node
    assert valid_action(node["action"])
  except AssertionError:
    return False
  return True

def valid_top_level (obj):
  try:
    assert "nodes" in obj
    assert isinstance(obj["nodes"], list)
    for node in obj["nodes"]:
      assert valid_node(node)
  except AssertionError:
    print("Invalid top level", obj)
    return False
  return True

gpt_count = 0
async def call_gpt (system_prompt, user_prompt):
  global gpt_count
  if verbose:
    print(f"{system_prompt} | {user_prompt}")
  response = await client.chat.completions.create(
      model="gpt-4-turbo-preview",
      response_format={ "type": "json_object" },
      messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
      ]
    )
  gpt_count += 1
  return json.loads(response.choices[0].message.content)
