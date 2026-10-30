from app.ai.providers.base import BaseAIProvider
from app.core.config import Config
from google import genai
from google.genai import types
import asyncio
import logging
import io

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):

    def __init__(self):

        # قراءة جميع مفاتيح Gemini من Config
        self.api_keys = getattr(Config, "GEMINI_API_KEYS", [])

        # لو لم تكن قائمة المفاتيح موجودة، نحاول استخدام المفتاح القديم
        if not self.api_keys:

            old_key = getattr(
                Config,
                "GEMINI_API_KEY",
                ""
            )

            if old_key:
                self.api_keys = [old_key]

        # إزالة أي مفاتيح فارغة
        self.api_keys = [
            key.strip()
            for key in self.api_keys
            if key and key.strip()
        ]

        self.clients = []

        # إنشاء Client مستقل لكل مفتاح
        for index, api_key in enumerate(self.api_keys, start=1):

            try:

                client = genai.Client(
                    api_key=api_key
                )

                self.clients.append(client)

                logger.info(
                    f"Gemini API key {index} initialized successfully."
                )

            except Exception as e:

                logger.error(
                    f"Gemini API key {index} initialization error: {e}"
                )

        self.available = len(self.clients) > 0

        # المفتاح الحالي الذي سيبدأ منه الاستخدام
        self.current_key_index = 0

    def is_available(self) -> bool:
        return self.available

    def get_capabilities(self) -> dict:
        return {
            "text": True,
            "vision": True,
            "image_generation": True,
            "model_name": "gemini-3.6-flash"
        }

    def _is_quota_error(self, error: Exception) -> bool:

        """
        تحديد هل الخطأ متعلق بالـQuota أو Rate Limit
        بحيث ننتقل للمفتاح التالي.
        """

        error_text = str(error).lower()

        quota_keywords = [
            "429",
            "resource_exhausted",
            "quota",
            "rate limit",
            "ratelimit",
            "too many requests",
            "requests per minute",
            "requests per day",
            "limit exceeded",
            "exceeded your current quota"
        ]

        return any(
            keyword in error_text
            for keyword in quota_keywords
        )

    async def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        history: list,
        image_bytes: bytes = None,
        image_mime: str = None,
        model_name: str = "gemini-3.6-flash"
    ) -> str:

        if not self.is_available():

            raise ValueError(
                "لا توجد مفاتيح Google Gemini API متاحة."
            )

        loop = asyncio.get_running_loop()

        # عدد المفاتيح التي سنحاول استخدامها
        total_keys = len(self.clients)

        last_error = None

        # نبدأ من المفتاح الحالي
        for attempt in range(total_keys):

            key_index = (
                self.current_key_index + attempt
            ) % total_keys

            client = self.clients[key_index]

            logger.info(
                f"Trying Gemini API key "
                f"{key_index + 1}/{total_keys} "
                f"with model: {model_name}"
            )

            def build_and_call():

                contents = []

                # إضافة المحادثة السابقة
                for msg in history:

                    role = (
                        "user"
                        if msg["role"] == "user"
                        else "model"
                    )

                    contents.append(
                        types.Content(
                            role=role,
                            parts=[
                                types.Part.from_text(
                                    text=str(
                                        msg["content"]
                                    )
                                )
                            ]
                        )
                    )

                # الرسالة الحالية
                if image_bytes:

                    contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(
                                    text=prompt
                                ),
                                types.Part.from_bytes(
                                    data=image_bytes,
                                    mime_type=(
                                        image_mime
                                        or "image/jpeg"
                                    )
                                )
                            ]
                        )
                    )

                else:

                    contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(
                                    text=prompt
                                )
                            ]
                        )
                    )

                # إرسال الطلب
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction
                    )
                )

                if not response.text:

                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return response.text

            try:

                response_text = await loop.run_in_executor(
                    None,
                    build_and_call
                )

                # نجاح المفتاح الحالي
                self.current_key_index = key_index

                logger.info(
                    f"Gemini request succeeded using "
                    f"API key {key_index + 1}/{total_keys}"
                )

                return response_text

            except Exception as e:

                last_error = e

                logger.error(
                    f"Gemini Response error "
                    f"[key {key_index + 1}/{total_keys}] "
                    f"[{model_name}]: {e}"
                )

                # لو المشكلة Quota/Rate Limit
                # ننتقل للمفتاح التالي
                if self._is_quota_error(e):

                    logger.warning(
                        f"Gemini API key "
                        f"{key_index + 1} quota/rate limit "
                        f"reached. Switching to next key..."
                    )

                    continue

                # لو الخطأ ليس Quota
                # لا داعي لتغيير المفتاح
                raise

        # جميع المفاتيح فشلت بسبب Quota/Rate Limit
        logger.error(
            "All Gemini API keys failed بسبب "
            "quota/rate limit."
        )

        raise last_error

    async def generate_image(
        self,
        prompt: str
    ) -> bytes:

        if not self.is_available():

            raise ValueError(
                "لا توجد مفاتيح Google Gemini API متاحة."
            )

        loop = asyncio.get_running_loop()

        # نستخدم المفتاح الحالي فقط هنا.
        # نظام الصور الأساسي في مشروعك لا يعتمد على هذه الدالة
        # لأنه يستخدم Pollinations.

        client = self.clients[
            self.current_key_index
        ]

        def generate():

            response = client.models.generate_content(
                model="gemini-3.1-flash-image",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )

            if not response.parts:

                raise RuntimeError(
                    "Gemini لم يُرجع أي بيانات للصورة."
                )

            for part in response.parts:

                if part.inline_data is not None:

                    image = part.as_image()

                    image_buffer = io.BytesIO()

                    image.save(
                        image_buffer,
                        format="PNG"
                    )

                    return image_buffer.getvalue()

            raise RuntimeError(
                "Gemini لم يُرجع صورة في الاستجابة."
            )

        try:

            image_bytes = await loop.run_in_executor(
                None,
                generate
            )

            return image_bytes

        except Exception as e:

            logger.error(
                f"Gemini image generation error: {e}"
            )

            raise