import os
import asyncio
import json

from shared import *

with open("python_preprompt.txt") as f:
  preprompt = f.read()

system_prompt, user_prompt = preprompt.split("----")

async def evaluate_on_src_file (src_file):
  global user_prompt
  with open(src_file, "r") as f:
    src_code = f.read()
  src_name = src_file.split("/")[-1]
  user_prompt = user_prompt.replace("$$$CODEHERE$$$", src_code).replace("$$$NAMEHERE$$$", src_name)
  
  res = None
  batch = 5
  while res is None:
    tasks = [call_gpt(system_prompt, user_prompt) for _ in range(batch)]
    results = await asyncio.gather(*tasks)
    for result in results:
        if valid_top_level(result):
          res = result
    
  return res

async def run_all_in_directory (dir_path):
  tasks = []
  names = []
  for text_file in os.listdir(dir_path):
    name = f"{dir_path}/{text_file}"
    names.append(name)
    tasks.append(evaluate_on_src_file(name))
  results = await asyncio.gather(*tasks)
  for i in range(len(names)):
    print(f"Name: {names[i]}, result: {results[i]}")
  print(f"{gpt_count} queries for {len(names)} source files")
  nodes = []
  for result in results:
    nodes += result["nodes"]
  
  with open("out.json", "w") as f:
    json.dump({"nodes": nodes}, f, indent=2)

dir_path = "src files"
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_all_in_directory(dir_path))
    loop.close()
