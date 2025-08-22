import os
from dotenv import load_dotenv
import yaml

load_dotenv()

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Inject Mongo URI from .env
config["database"]["mongodb"]["uri"] = os.getenv("MONGODB_URI")

# Optional helper to access nested keys
def get_config(path: str, default=None):
    keys = path.split(".")
    data = config
    for key in keys:
        if key not in data:
            return default
        data = data[key]
    return data
