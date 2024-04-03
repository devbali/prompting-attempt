import os
import asyncio
import json

from shared import *

with open("golang_preprompt_json.txt") as f:
  preprompt = f.read()

system_prompt, grpc_section, sample_section, request_section = preprompt.split("----")

user_prompt = lambda grpcs, sample_files, src_name, src_code:  f"""
{grpc_section.replace("$$$GRPCS$$$", "\n\n".join(grpcs))}
{"\n________\n".join([sample_section.replace("$$$SAMPLEFILENAME$$$", name).replace("$$$SAMPLEFILECODE$$$", code).replace("$$$SAMPLEOBJ$$$", jobj) for name, code, jobj in sample_files])}
__________
{request_section.replace("$$$REQUESTFILENAME$$$", src_name).replace("$$$REQUESTFILECODE$$$", src_code)}
"""

async def evaluate_on_src_file (src_file, dir_path, manual_json_path, grpc_path):
  global user_prompt
  sample_files = []
  
  grpcs = []
  for text_file in os.listdir(dir_path):
    name = f"{dir_path}/{text_file}"
    prefix = text_file.split(".")[0]
    if name != src_file:
      with open(name, "r") as f:
        code = f.read()
      with open(f"{manual_json_path}/{prefix}.json", "r") as f:
        json_sample = f.read()
      
      sample_files.append((text_file, code, json_sample))
    
    try:
      with open(f"{grpc_path}/{prefix}.txt", "r") as f:
        grpc_text = f.read()
      grpcs.append(grpc_text)
    except FileNotFoundError:
      pass
  
  with open(src_file, "r") as f:
    src_code = f.read()
  src_name = src_file.split("/")[-1]
  
  res = None
  batch = 2
  sleep_time = 0
  while res is None:
    await asyncio.sleep(sleep_time)
    full_user_prompt = user_prompt(grpcs, sample_files, src_name, src_code)
    tasks = [call_gpt(system_prompt, full_user_prompt) for _ in range(batch)]
    results = await asyncio.gather(*tasks)
    for result in results:
        if valid_top_level(result):
          res = result
    
  return res

async def run_all_in_directory (dir_path, manual_json_path, grpc_path):
  tasks = []
  names = []
  for text_file in os.listdir(dir_path):
    name = f"{dir_path}/{text_file}"
    names.append(name)
    tasks.append(evaluate_on_src_file(name, dir_path, manual_json_path, grpc_path))
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
manual_json_path = "manual json"
grpc_path = "grpcs"
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_all_in_directory(dir_path, manual_json_path, grpc_path))
    loop.close()

