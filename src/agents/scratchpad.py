import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL=os.getenv("REDIS_URL")
redis_client=redis.from_url(REDIS_URL)

def get_workspace_key(task_id:str) -> str:
    return f"task:{task_id}:workspace"

def write_to_scratchpad(task_id: str, data:dict):
    key=get_workspace_key(task_id)
    json_data=json.dumps(data)
    redis_client.set(key,json_data)
    redis_client.expire(key, 86400) #expire in 24 hours


def read_from_scratchpad(task_id:str)->dict:
    key=get_workspace_key(task_id)
    data=redis_client.get(key)
    if data:
        return json.loads(data)
    return {}