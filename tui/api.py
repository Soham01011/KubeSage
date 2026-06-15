import requests
from typing import Dict, Any, List

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        
    def _get_headers(self, user_id: int) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-User-ID": str(user_id)
        }

    def create_user(self, username: str, usergroup: str) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/users/",
            json={"username": username, "usergroup": usergroup}
        )
        resp.raise_for_status()
        return resp.json()

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/users/by-username/{username}")
        resp.raise_for_status()
        return resp.json()

    def get_models(self, user_id: int, provider: str = None) -> List[str]:
        url = f"{self.base_url}/settings/models"
        if provider:
            url += f"?provider={provider}"
        resp = requests.get(url, headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json().get("models", [])

    def get_settings(self, user_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/settings/", headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def update_settings(self, user_id: int, provider: str, model: str) -> Dict[str, Any]:
        resp = requests.put(
            f"{self.base_url}/settings/",
            headers=self._get_headers(user_id),
            json={"ai_provider": provider, "model_name": model}
        )
        resp.raise_for_status()
        return resp.json()

    def get_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        resp = requests.get(f"{self.base_url}/chat/sessions", headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def create_session(self, user_id: int, title: str) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/chat/sessions",
            headers=self._get_headers(user_id),
            json={"title": title}
        )
        resp.raise_for_status()
        return resp.json()

    def send_message(self, user_id: int, session_id: int, message: str) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/chat/sessions/{session_id}/message",
            headers=self._get_headers(user_id),
            json={"message": message}
        )
        resp.raise_for_status()
        return resp.json()

    def get_session(self, user_id: int, session_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/chat/sessions/{session_id}", headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()
