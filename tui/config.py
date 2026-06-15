import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

CONFIG_FILE = Path.home() / ".kubesage_tui.json"

def load_config() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {"active_profile_id": None, "profiles": {}}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"active_profile_id": None, "profiles": {}}

def save_config(config: Dict[str, Any]):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_profiles() -> Dict[str, Any]:
    return load_config().get("profiles", {})

def get_active_profile() -> Optional[Dict[str, Any]]:
    config = load_config()
    active_id = config.get("active_profile_id")
    if active_id and active_id in config.get("profiles", {}):
        profile = config["profiles"][active_id]
        profile["id"] = active_id
        return profile
    return None

def set_active_profile(profile_id: str):
    config = load_config()
    if profile_id in config.get("profiles", {}):
        config["active_profile_id"] = profile_id
        save_config(config)

def add_profile(name: str, server_url: str, user_id: int, username: str, usergroup: str) -> str:
    config = load_config()
    import uuid
    profile_id = str(uuid.uuid4())
    
    if "profiles" not in config:
        config["profiles"] = {}
        
    config["profiles"][profile_id] = {
        "name": name,
        "server_url": server_url.rstrip("/"),
        "user_id": user_id,
        "username": username,
        "usergroup": usergroup
    }
    config["active_profile_id"] = profile_id
    save_config(config)
    return profile_id
