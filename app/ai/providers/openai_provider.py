import base64
from app.ai.providers.base import BaseAIProvider
from app.core.config import Config
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):

    def __init__(self):
        self.client = None

        if Config.OPENAI_API_KEY:
            try:
                self.client = AsyncOpenAI(
                    api_key=Config.OPENAI_API_KEY
                )
            except Exception as e:
                logger.error(f"OpenAI initialization error: {e}")
                self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def get_capabilities(self) -> dict:
        return {
            "text": True,
            "vision": True,
            "image_generation": True,
            "model_name": "gpt-4o-mini"
        }

    async def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        history: list,
        image_bytes: bytes = None,
        image_mime: str = "image/jpeg"
    ) -> str:

        if not self.is_available():
            raise ValueError(
                "مفتاح OpenAI API غير متوفر أو معطل."
            )

        messages = [
            {
                "role": "system",
                "content": system_instruction
            }
        ]

        for msg in history:
            messages.append(
                {
                    "role": msg["role"],
                    "content": msg["content"]
                }
            )

        if image_bytes:
            base64_image = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            user_content = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{image_mime};"
                            f"base64,{base64_image}"
                        )
                    }
                }
            ]

            messages.append(
                {
                    "role": "user",
                    "content": user_content
                }
            )

        else:
            messages.append(
                {
                    "role": "user",
                    "content": prompt
                }
            )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )

            content = response.choices[0].message.content

            if not content:
                raise RuntimeError(
                    "OpenAI returned an empty response."
                )

            return content

        except Exception as e:
            logger.error(
                f"OpenAI generate_response Error: {e}"
            )
            raise

    async def generate_image(self, prompt: str) -> str:

        if not self.is_available():
            raise ValueError(
                "OpenAI API غير متوفر."
            )

        try:
            # استخدام واجهة الصور الحديثة في OpenAI.
            # إذا كان حسابك لا يدعم توليد الصور،
            # سيظهر خطأ واضح يمكن التعامل معه.

            response = await self.client.images.generate(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            if not response.data:
                raise RuntimeError(
                    "لم يتم إرجاع صورة من OpenAI."
                )

            image = response.data[0]

            if getattr(image, "url", None):
                return image.url

            if getattr(image, "b64_json", None):
                raise RuntimeError(
                    "تم إرجاع الصورة بصيغة Base64، "
                    "والبوت يحتاج حالياً إلى رابط صورة."
                )

            raise RuntimeError(
                "OpenAI لم يُرجع رابط صورة صالح."
            )

        except Exception as e:
            logger.error(
                f"OpenAI generate_image Error: {e}"
            )

            raise ValueError(
                f"فشل توليد الصورة من OpenAI: {e}"
            ) from e