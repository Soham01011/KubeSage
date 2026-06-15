from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Label, Button, Input, ListView, ListItem
from config import get_active_profile
from api import APIClient

class AIConfigurationScreen(Screen):
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("┌─ AI CONFIGURATION ───────────────┐", classes="title")
            
            yield Label("AI Provider (e.g. ollama):")
            yield Input(value="ollama", id="input_provider")
            
            yield Label("Available Models:")
            self.model_list = ListView(id="model_list")
            yield self.model_list
            
            self.error_label = Label("", classes="error-label")
            yield self.error_label
            
            with Horizontal(classes="dialog-buttons"):
                yield Button("Save & Continue", id="btn_save")
                yield Button("Back", id="btn_back")

    async def on_mount(self) -> None:
        self.client = None
        self.profile = get_active_profile()
        if self.profile:
            self.client = APIClient(self.profile["server_url"])
            await self._fetch_models()

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input_provider":
            await self._fetch_models()

    async def _fetch_models(self) -> None:
        if not self.client or not self.profile:
            return
            
        provider = self.query_one("#input_provider", Input).value
        await self.model_list.clear()
        
        if not provider:
            return
            
        try:
            models = self.client.get_models(self.profile["user_id"], provider)
            if not models:
                self.model_list.append(ListItem(Label("No models found"), id="no_models"))
            else:
                for i, m in enumerate(models):
                    item_id = f"model_{i}"
                    item = ListItem(Label(f"> {m}"), id=item_id)
                    item.model_name = m 
                    self.model_list.append(item)
            self.error_label.update("")
        except Exception as e:
            self.model_list.append(ListItem(Label("Error fetching models")))
            self.error_label.update(f"API Error: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            self._save_and_continue()
        elif event.button.id == "btn_back":
            self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id not in ["no_models", "error_models"]:
            self._save_and_continue()

    def _save_and_continue(self):
        provider = self.query_one("#input_provider", Input).value
        
        if not self.model_list.highlighted_child or not hasattr(self.model_list.highlighted_child, "model_name"):
            self.error_label.update("Please select a valid model")
            return
            
        model = self.model_list.highlighted_child.model_name
        
        if not provider or not model:
            self.error_label.update("Please select provider and model")
            return
            
        try:
            self.client.update_settings(self.profile["user_id"], provider, model)
            self.app.push_screen("main_chat")
        except Exception as e:
            self.error_label.update(f"Error saving: {e}")
