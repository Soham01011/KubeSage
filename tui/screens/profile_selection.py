from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, ListView, ListItem
from config import get_profiles, set_active_profile

class ProfileSelectionScreen(Screen):
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("┌─ SELECT KUBESAGE PROFILE ────────┐", classes="title")
            
            self.profile_list = ListView(id="profile-list")
            yield self.profile_list
            
            with Horizontal(classes="dialog-buttons"):
                yield Button("[ SELECT ]", id="btn_select")
                yield Button("[ NEW PROFILE ]", id="btn_new")
                yield Button("[ QUIT ]", id="btn_quit")

    def on_mount(self) -> None:
        self.refresh_profiles()

    def refresh_profiles(self) -> None:
        self.profile_list.clear()
        self.profiles = get_profiles()
        
        if not self.profiles:
            self.profile_list.append(ListItem(Label("No profiles found. Please create a new one."), id="no_profiles"))
        else:
            for pid, prof in self.profiles.items():
                display_str = f"> {prof['name']} ({prof['username']} @ {prof['server_url']})"
                # Valid Textual IDs must not have spaces, so we prefix it.
                item_id = f"profile_{pid}"
                self.profile_list.append(ListItem(Label(display_str), id=item_id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_select":
            self._handle_select()
        elif event.button.id == "btn_new":
            self.app.push_screen("connection_setup")
        elif event.button.id == "btn_quit":
            self.app.exit()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id != "no_profiles":
            self._handle_select()

    def _handle_select(self):
        if not self.profile_list.highlighted_child:
            return
            
        item_id = self.profile_list.highlighted_child.id
        if item_id and item_id.startswith("profile_"):
            pid = item_id.replace("profile_", "")
            set_active_profile(pid)
            self.app.push_screen("ai_configuration")
