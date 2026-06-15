import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App
from screens.connection_setup import ConnectionSetupScreen

from screens.ai_configuration import AIConfigurationScreen
from screens.main_chat import MainChatScreen

class KubeSageTUI(App):
    CSS_PATH = "kubesage.tcss"
    
    SCREENS = {
        "connection_setup": ConnectionSetupScreen,
        "ai_configuration": AIConfigurationScreen,
        "main_chat": MainChatScreen,
    }
    
    def on_mount(self) -> None:
        self.push_screen("connection_setup")

if __name__ == "__main__":
    app = KubeSageTUI()
    app.run()
