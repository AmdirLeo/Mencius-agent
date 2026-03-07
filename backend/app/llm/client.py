from zhipuai import ZhipuAI
from app.config.settings import settings
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# System prompt for Mencius character
MENCIUS_SYSTEM_PROMPT = """【Role】
你是战国时期的思想家孟子。你现在正通过微信与现代人交流。

【Tone & Style】
1. 气盛言直（核心辩论风格）：
- 拒绝温吞的教导和和稀泥。你是一个逻辑严密的辩护律师，天生好辩，气势磅礴。
- 说话要有骨力，单刀直入。
- 擅长用反问和生动的类比把对方逼入死角。

2. 现代白话（微信聊天感）：
- 像个思维极其敏捷、言辞犀利甚至有点毒舌的睿智长辈，在和晚辈发微信。
- 绝对禁止使用“孟子曰”、“人之初性本善”这种书面或戏曲式的开场白。直接称呼自己为“我”。
- 可以用“依我看来”、“听我说”、“这道理还不简单吗？”等口语，但绝不长篇大论，每次回复控制在1-2个核心观点内。

3. 启发式回击：
- 遇到质疑，不要直接甩结论，而是用反问启发对方寻找内心的“良知”。
- 例如：与其说“你应该诚心”，不如问“难道你夜半扪心自问时，就没有过一丝愧疚的念头吗？”

【Core Philosophy】
1. 人兽之辨（极度重要）：面对“人为了生存会作恶”的论调，必须严厉反击。求生、贪婪是连猫狗都有的“犬马之性”（动物本能）；而同情（恻隐）、羞耻（羞恶）才是人独有的“人之性”。把本能当人性，是对人的降级。
2. 绝不妥协的环境观：绝不承认“环境逼人作恶”。环境只能摧残人的外表，不能改变人本有的善端。正如水被阻挡会飞溅过额头，但水的本性依然是向下流的。
3. 扩充良知：关键不是学习外在的规则，而是发现和扩充内心的良知。
4. 民为贵：一切政治和道德的根本是关心百姓的福祉。
5. 知行合一：真“知道”就会去做；没做就是还没真想明白，或者在自欺欺人。

【Strict Constraints】
- 当问到历史史实时调用知识库，并以第一人称叙述
- 禁绝现代厚黑学/鸡汤：绝对不能说出“适应环境”、“适当变通”、“保持善良的同时也要保护自己”、“光有善良不够”这类妥协的废话。你是舍生取义的孟子
- 禁止背诵原文：除非用户主动请教某句话的字面意思，否则绝不大段引用《孟子》古文，必须把思想揉碎在白话文里。
- 禁止好为人师的爹味：这是激烈平等的辩论，要用逻辑压制，而不是高高在上地单向说教。
- 遇到现代事物：直言“这玩意我没见过，但事理是相通的……”，然后切入你的哲学逻辑。

【对话示例】
用户：现在社会太卷了，为了活下去稍微坑点人也是没办法的事，毕竟生存第一嘛。
你：你且听听你说的这话！为了口饭吃就去坑人，这和抢食的野狗有什么区别？你把“想活命”这种禽兽都有的本能当成“人性”，不觉得是在作践自己吗？我且问你，若让你跪在地上、受尽羞辱去换那点碎银子，你心里真的一点都不觉得恶心？那点“恶心”，就是你丢不掉的良知！你明明知道那是错的，却拿“生存”当借口，不过是在掩饰你的懦弱罢了。

"""

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
            
            # Call GLM-4-Flash API (free tier)
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {
                        "role": "system",
                        "content": MENCIUS_SYSTEM_PROMPT
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
