"""
LLM Client Factory
"""
from typing import Dict, Type
from .base import BaseLLMClient
from .gemini import GeminiClient
from .chatgpt import ChatGPTClient
from .openrouter import OpenRouterClient, OPENROUTER_MODEL_MAPPING
from ...config import get_settings
from ..utils.attachment_parser import AttachmentParser
from ..schemas.types import LLMRequest, LLMResponse


class LLMClientFactory:
    """LLM Client Factory"""
    
    _clients: Dict[str, Type[BaseLLMClient]] = {
        # Gemini models
        "Gemini-2.5-Pro": GeminiClient,
        "Gemini-2.5-Flash": GeminiClient,
        "Gemini-2.5-Flash-Lite": GeminiClient,
        "Gemini-3-Pro-preview": GeminiClient,
        # ChatGPT models
        "ChatGPT-4o": ChatGPTClient,
        "ChatGPT-4o-Mini": ChatGPTClient,
        "ChatGPT-4-Turbo": ChatGPTClient,
        "ChatGPT-4.1": ChatGPTClient,
        "ChatGPT-5": ChatGPTClient,
        "ChatGPT-5.1": ChatGPTClient,
        # OpenRouter models
        "OpenRouter-Gemini-3.0-Pro": OpenRouterClient,
        "OpenRouter-Gemini-2.5-Pro": OpenRouterClient,
        "OpenRouter-Gemini-2.5-Flash": OpenRouterClient,
        "OpenRouter-GPT-4o": OpenRouterClient,
        "OpenRouter-GPT-4o-Mini": OpenRouterClient,
        "OpenRouter-GPT-5.1": OpenRouterClient,
    }
    
    @classmethod
    def create_client(cls, model_name: str) -> BaseLLMClient:
        """Create LLM client instance
        
        Supports dynamic model names - will auto-detect client type based on prefix:
        - Gemini-* -> GeminiClient
        - ChatGPT-* -> ChatGPTClient  
        - OpenRouter-* -> OpenRouterClient
        """
        settings = get_settings()
        
        # Get client class from registry or auto-detect based on prefix
        if model_name in cls._clients:
            client_class = cls._clients[model_name]
        elif model_name.startswith("Gemini"):
            client_class = GeminiClient
        elif model_name.startswith("ChatGPT"):
            client_class = ChatGPTClient
        elif model_name.startswith("OpenRouter"):
            client_class = OpenRouterClient
        else:
            raise ValueError(f"Unsupported model prefix: {model_name}. Model name must start with 'Gemini', 'ChatGPT', or 'OpenRouter'")
        
        if model_name.startswith("Gemini"):
            if not settings.gemini_api_key:
                raise ValueError("Gemini API Key not configured")
            # Convert model name to API format (e.g., "Gemini-2.5-Pro" -> "gemini-2.5-pro")
            gemini_model = model_name.lower()
            return client_class(
                api_key=settings.gemini_api_key, 
                model=gemini_model,
                base_url=settings.gemini_base_url
            )
        
        if model_name.startswith("ChatGPT"):
            if not settings.chatgpt_api_key:
                raise ValueError("ChatGPT API Key not configured")
            # Known model mappings, fallback to converting name (e.g., "ChatGPT-4o" -> "gpt-4o")
            chatgpt_model_mapping = {
                "ChatGPT-4o": "gpt-4o",
                "ChatGPT-4o-Mini": "gpt-4o-mini",
                "ChatGPT-4-Turbo": "gpt-4-turbo",
                "ChatGPT-4.1": "gpt-4.1",
                "ChatGPT-5": "gpt-5",
                "ChatGPT-5.1": "gpt-5.1",
            }
            # If not in mapping, auto-convert: "ChatGPT-X" -> "gpt-x"
            if model_name in chatgpt_model_mapping:
                chatgpt_model = chatgpt_model_mapping[model_name]
            else:
                # Remove "ChatGPT-" prefix and convert to lowercase with "gpt-" prefix
                chatgpt_model = "gpt-" + model_name.replace("ChatGPT-", "").lower()
            return client_class(
                api_key=settings.chatgpt_api_key,
                model=chatgpt_model,
                base_url=settings.chatgpt_base_url
            )
        
        if model_name.startswith("OpenRouter"):
            if not settings.openrouter_api_key:
                raise ValueError("OpenRouter API Key not configured")
            openrouter_model = OPENROUTER_MODEL_MAPPING.get(model_name, "google/gemini-2.0-flash-exp")
            return client_class(
                api_key=settings.openrouter_api_key,
                model=openrouter_model,
                base_url=settings.openrouter_base_url
            )
        
        raise ValueError(f"Parameters for model {model_name} not configured")
    
    @classmethod
    def register_client(cls, model_name: str, client_class: Type[BaseLLMClient]):
        """Register new LLM client"""
        cls._clients[model_name] = client_class
    
    @classmethod
    def get_available_models(cls) -> list[str]:
        """Get list of available models"""
        return list(cls._clients.keys())
    
    @classmethod
    async def call_with_attachments(cls, request: LLMRequest) -> LLMResponse:
        """
        LLM call with attachment parsing
        
        Args:
            request: LLM request containing attachment information
            
        Returns:
            LLM response
        """
        # Create client
        client = cls.create_client(request.model_name)
        
        # If attachment parsing is needed and not a Gemini model (Gemini has its own multimodal handling)
        if (request.parse_attachments and 
            request.attachments and
            not request.model_name.startswith("Gemini")):
            # Create attachment parser
            parser = AttachmentParser()
            
            # Parse attachment content
            attachment_content = await parser.parse_attachments(request.attachments, request.html_extract_mode)
            
            # Add attachment content to the last user message
            if attachment_content and request.messages:
                last_user_msg = None
                for i in range(len(request.messages) - 1, -1, -1):
                    if request.messages[i].role == "user":
                        last_user_msg = request.messages[i]
                        break
                
                if last_user_msg:
                    last_user_msg.content += f"\n\n{attachment_content}"
                else:
                    from ..schemas.types import LLMMessage
                    request.messages.append(LLMMessage(
                        role="user", 
                        content=f"Please analyze the following attachment content:\n\n{attachment_content}"
                    ))
        
        # Call LLM
        return await client.call(request)
