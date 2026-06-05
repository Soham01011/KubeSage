from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class AIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Any]:
        """
        Send a chat request to the AI provider.
        Returns a tuple: (assistant_message, tool_calls_if_any)
        assistant_message should be a dict like {"role": "assistant", "content": "Hello!"}
        """
        pass

    @abstractmethod
    def format_tool_result(self, tool_call_id: str, tool_name: str, result: str) -> Dict[str, Any]:
        """
        Format the result of a tool call into a message format the provider understands.
        """
        pass

    @abstractmethod
    async def get_models(self) -> List[str]:
        """
        Fetch available models from the provider.
        """
        pass
