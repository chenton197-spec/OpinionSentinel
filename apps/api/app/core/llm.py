import json
import logging
import httpx
from typing import Optional
from fastapi import HTTPException
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        # Default to anthropic to maintain backward compatibility
        self.provider = getattr(self.settings, 'llm_provider', 'anthropic').lower()
        
        # Priority: unified key -> legacy anthropic key
        self.api_key = getattr(self.settings, 'llm_api_key', None)
        if not self.api_key:
            self.api_key = getattr(self.settings, 'anthropic_api_key', None)
            
        self.model = getattr(self.settings, 'llm_model', None)
        if not self.model:
            self.model = getattr(self.settings, 'anthropic_model', 'claude-sonnet-4-5')
            
        self.base_url = getattr(self.settings, 'llm_base_url', None)

    def generate_json(self, prompt: str, system_prompt: str = "", disable_reasoning: bool = False) -> str:
        """
        统一的模型调用入口，并要求返回 JSON 格式结果。
        """
        if not self.api_key:
            raise HTTPException(status_code=400, detail="本地未配置大模型 API Key 环境变量，请配置后重试。")

        if self.provider == 'anthropic':
            return self._call_anthropic(prompt, system_prompt)
        elif self.provider in ['openai', 'zhipu', 'deepseek', 'qwen', 'moonshot']:
            return self._call_openai_compatible(prompt, system_prompt, disable_reasoning)
        elif self.provider == 'gemini':
            return self._call_gemini(prompt, system_prompt)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的模型厂商配置: {self.provider}")

    def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        import anthropic
        client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url if self.base_url else "https://api.anthropic.com"
        )
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise HTTPException(status_code=502, detail=f"调用 Anthropic 模型失败: {str(e)}")

    def _call_openai_compatible(self, prompt: str, system_prompt: str, disable_reasoning: bool = False) -> str:
        # 兼容各大 OpenAI 格式厂商（默认使用 api.openai.com，如果是国内模型则通过 baseUrl 覆盖）
        url = self.base_url.rstrip("/") + "/v1/chat/completions" if self.base_url else "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 结合 system prompt（明确需要返回JSON防止部分较老模型不兼容 json_object 配置报错）
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        
        model_name = self.model
            
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.3
        }
        
        # OpenAI 支持明确指定 response_format: raw json
        if self.provider == 'openai':
            payload["response_format"] = {"type": "json_object"}
            
        if self.provider == 'deepseek':
            if disable_reasoning:
                payload["thinking"] = {"type": "disabled"}
            else:
                payload["thinking"] = {"type": "enabled"}
                payload["reasoning_effort"] = "high"

        try:
            with httpx.Client(timeout=60) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                
                # 如果部分模型返回包含了 ```json 的标记片段，在此处统一清理
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                     content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                    
                return content.strip()
        except Exception as e:
            if isinstance(e, httpx.HTTPStatusError):
                logger.error(f"OpenAI 兼容接口 HTTP 异常: {e.response.text}")
            logger.error(f"OpenAI API call failed: {e}")
            raise HTTPException(status_code=502, detail=f"调用大模型失败: {str(e)}")

    def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        if self.base_url:
             url = f"{self.base_url.rstrip('/')}/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json"
            }
        }
        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

        try:
            with httpx.Client(timeout=60) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            if isinstance(e, httpx.HTTPStatusError):
                logger.error(f"Gemini HTTP 异常: {e.response.text}")
            logger.error(f"Gemini API call failed: {e}")
            raise HTTPException(status_code=502, detail=f"调用 Gemini 失败: {str(e)}")

llm_client = LLMClient()
