from typing import List, Dict, Any, Tuple
from openai import AsyncOpenAI
import json

from .base import AIProvider

class OllamaProvider(AIProvider):
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434/v1"):
        # Ollama's API is compatible with OpenAI's client when pointed to the /v1 endpoint
        self.client = AsyncOpenAI(base_url=base_url, api_key="ollama")
        self.model_name = model_name

    async def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Any]:
        kwargs = {
            "model": self.model_name,
            "messages": messages,
        }
        
        # Format tools for OpenAI standard (which Ollama supports)
        if tools:
            formatted_tools = []
            for tool in tools:
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {})
                    }
                })
            kwargs["tools"] = formatted_tools

        response = await self.client.chat.completions.create(**kwargs)
        
        message = response.choices[0].message
        
        # Extract assistant message
        assistant_msg = {
            "role": "assistant",
            "content": message.content if message.content else ""
        }
        
        tool_calls = message.tool_calls
        
        return assistant_msg, tool_calls

    def format_tool_result(self, tool_call_id: str, tool_name: str, result: str) -> Dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result
        }

    async def get_models(self) -> List[str]:
        try:
            # Ollama's OpenAI-compatible endpoint supports /v1/models
            response = await self.client.models.list()
            return [model.id for model in response.data]
        except Exception as e:
            print(f"Failed to fetch models from Ollama: {e}")
            return []
