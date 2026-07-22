"""Manual single-shot probe of the served model. Edit _prompt.txt with the exact prompt,
run this, read the full raw response. Drive the ReAct loop by hand: after each response,
append the env's real reply + the next '\n>' to _prompt.txt and run again.

Env knobs (all optional):
  PROMPT_FILE  (default _prompt.txt)
  STOP         e.g. STOP='\n' to reproduce the newline-stop; UNSET = no stop (default)
  TEMP         default 0.7      TOP_P  default 0.95      MAX_TOKENS  default 1024
"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from openai import OpenAI

c = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
prompt = open(os.environ.get("PROMPT_FILE", "_prompt.txt")).read()

stop_env = os.environ.get("STOP")
stop = [stop_env.encode().decode("unicode_escape")] if stop_env else None

r = c.completions.create(
    model="qwen",
    prompt=prompt,
    temperature=float(os.environ.get("TEMP", "0.7")),
    top_p=float(os.environ.get("TOP_P", "0.95")),
    max_tokens=int(os.environ.get("MAX_TOKENS", "1024")),
    stop=stop,
)
ch = r.choices[0]
print("################ PROMPT SENT — last 400 chars ################")
print(prompt[-400:])
print("\n################ RAW RESPONSE (verbatim, exactly as returned) ################")
print(ch.text)
print("\n################ META ################")
print("finish_reason=%s | completion_tokens=%s | stop=%r | temp=%s max_tokens=%s"
      % (ch.finish_reason, r.usage.completion_tokens, stop,
         os.environ.get("TEMP", "0.7"), os.environ.get("MAX_TOKENS", "1024")))
