# services/ai_service.py

from typing import List, Dict, Optional, Generator
import google.generativeai as genai
from openai import OpenAI
import anthropic

from config import settings
from utils.logger import get_logger
from utils.exceptions import IntegrationException

logger = get_logger(__name__)


class AIService:
    """Multi-provider AI service (Google Gemini, OpenAI, Anthropic)"""
    
    def __init__(self):
        """Initialize AI service with configured providers"""
        self.providers = {}
        
        # Initialize Google Gemini
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.providers['gemini'] = True
                logger.info("Google Gemini initialized")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}")
        
        # Initialize OpenAI
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.providers['openai'] = True
                logger.info("OpenAI initialized")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")
        
        # Initialize Anthropic
        if settings.ANTHROPIC_API_KEY:
            try:
                self.anthropic_client = anthropic.Anthropic(
                    api_key=settings.ANTHROPIC_API_KEY
                )
                self.providers['anthropic'] = True
                logger.info("Anthropic initialized")
            except Exception as e:
                logger.warning(f"Anthropic initialization failed: {e}")
        
        if not self.providers:
            logger.warning("No AI providers configured")
    
    def chat(
        self, prompt: str, system_instruction: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """Send chat completion request
        
        Args:
            prompt: User prompt
            system_instruction: System instructions
            history: Conversation history
            provider: Provider name (gemini, openai, anthropic)
            model: Model name (overrides default)
            
        Returns:
            AI response text
            
        Raises:
            IntegrationException: If request fails
        """
        # Select provider
        provider = provider or settings.AI_DEFAULT_PROVIDER
        
        if provider not in self.providers:
            raise IntegrationException(f"Provider {provider} not available")
        
        try:
            if provider == 'gemini':
                return self._chat_gemini(prompt, system_instruction, history, model)
            elif provider == 'openai':
                return self._chat_openai(prompt, system_instruction, history, model)
            elif provider == 'anthropic':
                return self._chat_anthropic(prompt, system_instruction, history, model)
            else:
                raise IntegrationException(f"Unknown provider: {provider}")
                
        except Exception as e:
            logger.error(f"AI chat failed ({provider}): {e}")
            raise IntegrationException(f"AI request failed: {str(e)}")
    
    def _chat_gemini(
        self, prompt: str, system_instruction: Optional[str],
        history: Optional[List[Dict]], model_name: Optional[str]
    ) -> str:
        """Google Gemini chat implementation"""
        model_name = model_name or "gemini-2.0-flash-exp"
        
        # Create model
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_instruction
        )
        
        # Convert history to Gemini format
        gemini_history = []
        if history:
            for msg in history:
                role = "user" if msg['role'] == 'user' else "model"
                gemini_history.append({
                    "role": role,
                    "parts": [msg['content']]
                })
        
        # Start chat
        chat = model.start_chat(history=gemini_history)
        
        # Send message
        response = chat.send_message(prompt)
        
        return response.text
    
    def _chat_openai(
        self, prompt: str, system_instruction: Optional[str],
        history: Optional[List[Dict]], model_name: Optional[str]
    ) -> str:
        """OpenAI chat implementation"""
        model_name = model_name or "gpt-4o"
        
        # Build messages
        messages = []
        
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": prompt})
        
        # Send request
        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=settings.AI_MAX_TOKENS
        )
        
        return response.choices[0].message.content
    
    def _chat_anthropic(
        self, prompt: str, system_instruction: Optional[str],
        history: Optional[List[Dict]], model_name: Optional[str]
    ) -> str:
        """Anthropic Claude chat implementation"""
        model_name = model_name or "claude-3-5-sonnet-20241022"
        
        # Build messages
        messages = history or []
        messages.append({"role": "user", "content": prompt})
        
        # Send request
        response = self.anthropic_client.messages.create(
            model=model_name,
            max_tokens=settings.AI_MAX_TOKENS,
            system=system_instruction or "",
            messages=messages
        )
        
        return response.content[0].text
    
    def stream_chat(
        self, prompt: str, system_instruction: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        provider: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Stream chat completion (for real-time UI updates)
        
        Args:
            prompt: User prompt
            system_instruction: System instructions
            history: Conversation history
            provider: Provider name
            
        Yields:
            Text chunks
        """
        provider = provider or settings.AI_DEFAULT_PROVIDER
        
        if provider == 'openai':
            # OpenAI streaming
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": prompt})
            
            stream = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        else:
            # Non-streaming providers: yield full response
            response = self.chat(prompt, system_instruction, history, provider)
            yield response
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        return list(self.providers.keys())
    
    def is_available(self, provider: str = None) -> bool:
        """Check if AI service is available
        
        Args:
            provider: Specific provider to check (None for any)
            
        Returns:
            True if available
        """
        if provider:
            return provider in self.providers
        return len(self.providers) > 0


# Global instance
ai_service = AIService()