from zhipuai import ZhipuAI
from app.config.settings import settings
import logging
from typing import List, Dict
import asyncio
import os

logger = logging.getLogger(__name__)

class GLMClient:
    def __init__(self):
        if not settings.glm_api_key:
            logger.warning("GLM_API_KEY not set in environment variables")
            raise ValueError("GLM_API_KEY must be set")
        
        try:
            self.client = ZhipuAI(api_key=settings.glm_api_key)
            logger.info("GLM client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GLM client: {str(e)}")
            raise

        self._load_system_prompt()

    def _load_system_prompt(self):
        try:
            soul_md_path = os.path.join(os.path.dirname(__file__), "../../../SOUL.md")
            with open(soul_md_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
            logger.info("Successfully loaded system prompt from SOUL.md")
        except Exception as e:
            logger.error(f"Failed to load SOUL.md: {str(e)}")
            self.system_prompt = "你是战国时期的思想家孟子。你现在正通过微信与现代人交流。"
    
    def build_prompt(self, user_question: str, context: List[Dict] = None) -> str:
        """
        Build a complete prompt with context from retrieved documents
        
        Args:
            user_question: The user's question
            context: List of retrieved context documents
        
        Returns:
            Complete prompt string
        """
        if context is None:
            context = []
        
        # Build prompt with context as "孟子的回忆" (Mencius's memories/knowledge)
        prompt = ""
        
        if context:
            prompt += "【我（孟子）关于这个问题的思想记录】\n"
            for i, doc in enumerate(context, 1):
                text = doc.get('text', '').strip()
                if text:
                    prompt += f"记录{i}：{text}\n\n"
            prompt += "---\n\n"
        
        prompt += f"【提问者的问题】\n{user_question}\n\n【我的回答】\n"
        
        return prompt
    
    async def generate_response(
        self,
        user_question: str,
        context: List[Dict] = None,
        temperature: float = 0.8,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate response using GLM-4-Flash API with Mencius character
        
        Args:
            user_question: User's question
            context: Retrieved documents for context
            temperature: Sampling temperature (0-1) - higher = more creative
            max_tokens: Maximum tokens in response
        
        Returns:
            Generated response string
        """
        try:
            # Build complete prompt with context
            prompt = self.build_prompt(user_question, context)
            
            logger.info(f"Calling GLM-4-Flash with question: {user_question[:50]}...")
            logger.info(f"Context documents: {len(context or [])}")
            
            # Call GLM-4-Flash API (free tier) using to_thread to prevent blocking
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="glm-4-flash",
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Generated response ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.error(f"GLM API error: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")

glm_client = GLMClient()
