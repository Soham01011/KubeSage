from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Label, Button, Input
from config import add_profile
from api import APIClient

class ConnectionSetupScreen(Screen):
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("┌─ CONNECTION SETUP ───────────────┐", classes="title")
            
            yield Label("SERVER URL")
            yield Input(value="http://127.0.0.1:8000", id="input_url")
            
            yield Label("PROFILE NAME")
            yield Input(value="Local Cluster", id="input_pname")
            
            yield Label("USERNAME")
            yield Input(placeholder="e.g. admin", id="input_username")
            
            yield Label("USER GROUP")
            yield Input(value="dev", id="input_group")
            
            self.status_label = Label("", classes="status-label")
            yield self.status_label
            
            with Horizontal(classes="dialog-buttons"):
                yield Button("Register", id="btn_register")
                yield Button("Login", id="btn_login")
                yield Button("Cancel", id="btn_cancel")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        url = self.query_one("#input_url", Input).value
        username = self.query_one("#input_username", Input).value
        pname = self.query_one("#input_pname", Input).value
        group = self.query_one("#input_group", Input).value
        
        if button_id == "btn_cancel":
            # For now just exit, or if we had profile selection, go there
            self.app.exit()
            return
            
        if not url or not username or not pname:
            self.status_label.update("Fields cannot be empty!")
            return

        try:
            client = APIClient(url)
            if button_id == "btn_register":
                resp = client.create_user(username, group)
                user_id = resp["id"]
                add_profile(pname, url, user_id, username, group)
                self.app.push_screen("ai_configuration")
                
            elif button_id == "btn_login":
                resp = client.get_user_by_username(username)
                user_id = resp["id"]
                group = resp["usergroup"]
                add_profile(pname, url, user_id, username, group)
                self.app.push_screen("ai_configuration")
                
        except Exception as e:
            self.status_label.update(f"API Error: {e}")
