from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Input, ListView, ListItem, Markdown
from config import get_active_profile
from api import APIClient

class MainChatScreen(Screen):
    def compose(self) -> ComposeResult:
        with Horizontal():
            # Sidebar
            with Vertical(id="chat-sidebar"):
                yield Label("┌─ SESSIONS ───────────┐", classes="title")
                self.sessions_list = ListView(id="sessions_list")
                yield self.sessions_list
                yield Button("New Session", id="btn_new")
                yield Button("Back", id="btn_back")
                self.status_label = Label("", classes="error-label")
                yield self.status_label

            # Main Chat Area
            with Vertical(id="chat-main"):
                yield Label("┌─ KUBESAGE TERMINAL ────────────────────────────────────┐", classes="title")
                self.chat_history = VerticalScroll(id="chat-history")
                yield self.chat_history
                
                with Horizontal(id="chat-input-container"):
                    self.chat_input = Input(placeholder="> Enter command or prompt...", id="chat_input")
                    yield self.chat_input
                    yield Button("Send", id="btn_send")

    async def on_mount(self) -> None:
        self.client = None
        self.profile = get_active_profile()
        self.current_session_id = None
        
        if self.profile:
            self.client = APIClient(self.profile["server_url"])
            await self._fetch_sessions()

    async def _fetch_sessions(self) -> None:
        try:
            sessions = self.client.get_sessions(self.profile["user_id"])
            await self.sessions_list.clear()
            
            if not sessions:
                self.sessions_list.append(ListItem(Label("No sessions"), id="no_sessions"))
            else:
                for s in sessions:
                    item_id = f"session_{s['id']}"
                    item = ListItem(Label(f"> {s['title']} ({s['id']})"), id=item_id)
                    item.session_id = s["id"]
                    self.sessions_list.append(item)
                
                # Auto-select first session if none selected
                if self.current_session_id is None:
                    self.current_session_id = sessions[0]["id"]
                    self.sessions_list.index = 0
                    
            await self._load_session_history()
        except Exception as e:
            self.status_label.update(f"Error fetching sessions: {e}")

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id != "no_sessions" and hasattr(event.item, "session_id"):
            self.current_session_id = event.item.session_id
            await self._load_session_history()

    async def _load_session_history(self) -> None:
        await self.chat_history.query("*").remove()
        if not self.current_session_id:
            return
            
        try:
            session_data = self.client.get_session(self.profile["user_id"], self.current_session_id)
            for msg in session_data.get("messages", []):
                role = "USER" if msg["role"] == "user" else "KUBESAGE"
                content = msg["content"]
                
                if role == "USER":
                    await self.chat_history.mount(Markdown(f"**USER:**\n\n{content}"))
                else:
                    await self.chat_history.mount(Markdown(f"**KUBESAGE:**\n\n{content}"))
                await self.chat_history.mount(Label("-" * 40))
            
            self.chat_history.scroll_end(animate=False)
            self.status_label.update("")
        except Exception as e:
            self.status_label.update(f"Error loading history: {e}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_new":
            await self._on_new_session()
        elif event.button.id == "btn_send":
            await self._on_send()
        elif event.button.id == "btn_back":
            self.app.pop_screen()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat_input":
            await self._on_send()

    async def _on_new_session(self) -> None:
        try:
            resp = self.client.create_session(self.profile["user_id"], "New TUI Session")
            self.current_session_id = resp["id"]
            await self._fetch_sessions()
        except Exception as e:
            self.status_label.update(f"Error creating session: {e}")

    async def _on_send(self) -> None:
        if not self.current_session_id:
            self.status_label.update("Please select or create a session first.")
            return
            
        message = self.chat_input.value
        if not message:
            return
            
        self.status_label.update("Sending...")
        
        try:
            # Locally append for responsiveness
            await self.chat_history.mount(Markdown(f"**USER:**\n\n{message}"))
            await self.chat_history.mount(Label("-" * 40))
            self.chat_history.scroll_end(animate=False)
            self.chat_input.value = ""
            
            # Send to backend
            resp = self.client.send_message(self.profile["user_id"], self.current_session_id, message)
            
            # Re-load full history to get AI response safely
            await self._load_session_history()
        except Exception as e:
            self.status_label.update(f"Error sending: {e}")
