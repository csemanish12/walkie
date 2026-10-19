import httpx

url = "http://localhost:11434/api/chat"
data = {
  "model": "gemma4:e4b",
  "think": True,
  "stream": False,
  "messages": [
  {
    "role": "user", "content": "what is the color of sky"
  }
]
}
response = httpx.post(url, json=data, timeout=300)
if response.status_code == 200:
  json_response = response.json()
  answer = json_response["message"]["content"]
  token = json_response["eval_count"]
  time = json_response["total_duration"] / 1e9
  prompt_read_time = json_response["prompt_eval_duration"] / 1e9
  eval_duration = json_response["eval_duration"] / 1e9
  token_per_sec = token / eval_duration
  print(f"{answer} | {token} tokens | {time:.2f} s total | {prompt_read_time:.2f} s reading prompt | {token_per_sec:.2f} tok/s ")

else:
  print("unable to fetch response")