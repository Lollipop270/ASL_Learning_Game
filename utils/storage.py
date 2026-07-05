import json
import os
from utils.resource_path import resource_path

HIGHSCORE_FILE = resource_path("assets/data/highscore.json")

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            return json.load(f).get("highscore", 0)
    return 0

def save_highscore(score):
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump({"highscore": score}, f)