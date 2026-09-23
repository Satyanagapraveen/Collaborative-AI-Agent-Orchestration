import json
import os
import logging
from datetime import datetime, timezone

log_dir=os.path.join(os.getcwd(),"logs")
os.makedirs(log_dir, exist_ok=True)
log_file_path=os.path.join(log_dir,"agent_activity.log")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "task_id": getattr(record, "task_id","SYSTEM"),
            "agent_name": getattr(record, "agent_name","Orchestrator"),
            "action_details": record.getMessage()
        }
        return json.dumps(log_entry)
logger=logging.getLogger("agent_logger")
logger.setLevel(logging.INFO)

file_handler=logging.FileHandler(log_file_path)
file_handler.setFormatter(JSONFormatter())

if not logger.handlers:
    logger.addHandler(file_handler)
def log_agent_action(task_id: str, agent_name: str, action_details: str, level: int = logging.INFO):
    extra_context = {"task_id": task_id, "agent_name": agent_name}
    logger.log(level, action_details, extra=extra_context)
    

