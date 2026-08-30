import logging

from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.router import ModelRouter
from app.ai.context_manager import ContextManager
from app.database.db_manager import DBManager
from app.tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class Orchestrator:

    # ترتيب الـFallback لكل موديل
    GEMINI_FALLBACKS = {
        "gemini-3.7-flash": [
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        ],

        "gemini-3.6-flash": [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        ],

        "gemini-3.5-flash": [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        ],

        "gemini-3.5-flash-lite": [
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
        ],
    }

    def __init__(self, db: DBManager):
        self.db = db

        self.openai = OpenAIProvider()
        self.gemini = GeminiProvider()

    async def _try_gemini_models(
        self,
        models: list,
        prompt: str,
        system_instruction: str,
        history: list,
        image_bytes: bytes = None
    ):

        last_error = None

        for model_name in models:

            if not self.gemini.is_available():
                break

            try:
                logger.info(
                    f"Trying Gemini model: {model_name}"
                )

                response = await self.gemini.generate_response(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    history=history,
                    image_bytes=image_bytes,
                    model_name=model_name
                )

                logger.info(
                    f"Gemini model succeeded: {model_name}"
                )

                return response, model_name

            except Exception as e:

                last_error = e

                logger.warning(
                    f"Gemini model failed "
                    f"[{model_name}], trying next model: {e}"
                )

        if last_error:
            raise last_error

        raise RuntimeError(
            "No Gemini model is available."
        )

    async def process_ai_request(
        self,
        telegram_id: int,
        conversation_id: str,
        prompt: str,
        image_bytes: bytes = None,
        force_provider: str = None
    ) -> tuple:

        # إعدادات المستخدم
        settings = self.db.get_settings(telegram_id)

        default_model = (
            settings['default_model']
            if settings
            else 'auto'
        )

        web_search_enabled = (
            settings['web_search_enabled']
            if settings
            else 1
        )

        # تحديد نوع الطلب
        routed_need = ModelRouter.decide_best_model(
            prompt,
            has_image=(image_bytes is not None)
        )

        chosen = force_provider or default_model

        logger.info(
            f"User {telegram_id} selected model: {chosen}"
        )

        # --------------------------------------------------
        # Memory
        # --------------------------------------------------

        memories = self.db.get_memories(telegram_id)

        memory_context = "\n".join(
            [
                f"- {m['memory_text']}"
                for m in memories
            ]
        )

        # --------------------------------------------------
        # System instruction
        # --------------------------------------------------

        system_instruction = (
            "أنت مساعد ذكاء اصطناعي تفاعلي متكامل ومحترف "
            "يدعى AI Telegram Assistant.\n"
            "أجب بدقة وبأسلوب واضح ومفيد وسهل القراءة.\n\n"

            f"معلومات الذاكرة طويلة المدى المتاحة عن المستخدم:\n"
            f"{memory_context}\n\n"

            "اكتب ردودك كنص عادي فقط. "
            "لا تستخدم HTML ولا Markdown ولا أي علامات تنسيق خاصة. "
            "لا تستخدم <b> أو <i> أو <code> أو <pre>. "
            "ولا تستخدم ``` أو ** أو __. "
            "اكتب كما لو أنك شخص عادي يتحدث مع المستخدم مباشرة."
        )

        # --------------------------------------------------
        # Web Search
        # --------------------------------------------------

        search_text = ""
        provider_notes = ""

        if web_search_enabled and (
            routed_need == "search-heavy"
            or "ابحث عن" in prompt
        ):

            try:
                results = await WebSearchTool.search_ddg(prompt)

                if results:

                    search_text = (
                        "\n\n"
                        "[معلومات من الإنترنت تم جلبها مباشرة]:\n"
                    )

                    search_text += "\n".join(
                        [
                            f"العنوان: {r['title']}\n"
                            f"الرابط: {r['href']}\n"
                            f"الوصف: {r['body']}\n"
                            for r in results[:3]
                        ]
                    )

                    provider_notes = (
                        "🌐 تم استخدام البحث عبر الإنترنت "
                        "لتقديم أحدث البيانات\n"
                    )

            except Exception as e:

                logger.error(
                    f"Web Search Error within Orchestrator: {e}"
                )

        final_prompt = prompt + search_text

        # --------------------------------------------------
        # Conversation history
        # --------------------------------------------------

        db_history = self.db.get_messages(
            conversation_id
        )

        history = ContextManager.get_managed_context(
            db_history
        )

        # --------------------------------------------------
        # MODEL SELECTION
        # --------------------------------------------------

        # المستخدم اختار OpenAI
        if chosen == "openai":

            if self.openai.is_available():

                try:

                    response = await self.openai.generate_response(
                        prompt=final_prompt,
                        system_instruction=system_instruction,
                        history=history,
                        image_bytes=image_bytes
                    )

                    self.db.log_usage(
                        telegram_id,
                        "ai_generation",
                        len(final_prompt) + len(response)
                    )

                    return response, provider_notes

                except Exception as e:

                    logger.warning(
                        f"OpenAI failed: {e}"
                    )

            # لو OpenAI فشل، ننتقل إلى Gemini
            if self.gemini.is_available():

                try:

                    models = [
                        "gemini-3.6-flash",
                        "gemini-3.5-flash",
                        "gemini-3.5-flash-lite"
                    ]

                    response, used_model = (
                        await self._try_gemini_models(
                            models,
                            final_prompt,
                            system_instruction,
                            history,
                            image_bytes
                        )
                    )

                    provider_notes += (
                        f"⚠️ تم التحويل تلقائيًا إلى "
                        f"{used_model} بعد فشل OpenAI.\n"
                    )

                    self.db.log_usage(
                        telegram_id,
                        "ai_generation_fallback",
                        len(final_prompt) + len(response)
                    )

                    return response, provider_notes

                except Exception as e:

                    logger.error(
                        f"Gemini fallback failed: {e}"
                    )

            return (
                "عذرًا، تعذر معالجة طلبك حاليًا. "
                "يرجى المحاولة مرة أخرى بعد قليل.",
                ""
            )

        # --------------------------------------------------
        # المستخدم اختار Gemini محدد
        # --------------------------------------------------

        if chosen in self.GEMINI_FALLBACKS:

            if self.gemini.is_available():

                try:

                    models = self.GEMINI_FALLBACKS[
                        chosen
                    ]

                    response, used_model = (
                        await self._try_gemini_models(
                            models,
                            final_prompt,
                            system_instruction,
                            history,
                            image_bytes
                        )
                    )

                    # لو استخدمنا موديل مختلف عن المختار
                    if used_model != chosen:

                        provider_notes += (
                            f"⚠️ تعذر استخدام {chosen}، "
                            f"فتم التحويل تلقائيًا إلى "
                            f"{used_model}.\n"
                        )

                    self.db.log_usage(
                        telegram_id,
                        "ai_generation",
                        len(final_prompt) + len(response)
                    )

                    return response, provider_notes

                except Exception as e:

                    logger.warning(
                        f"All selected Gemini models failed: {e}"
                    )

            # Gemini فشل بالكامل → OpenAI
            if self.openai.is_available():

                try:

                    response = await self.openai.generate_response(
                        prompt=final_prompt,
                        system_instruction=system_instruction,
                        history=history,
                        image_bytes=image_bytes
                    )

                    provider_notes += (
                        "⚠️ تعذر استخدام Gemini، "
                        "فتم التحويل تلقائيًا إلى OpenAI.\n"
                    )

                    self.db.log_usage(
                        telegram_id,
                        "ai_generation_fallback",
                        len(final_prompt) + len(response)
                    )

                    return response, provider_notes

                except Exception as e:

                    logger.error(
                        f"OpenAI fallback failed: {e}"
                    )

            return (
                "عذرًا، تعذر معالجة طلبك حاليًا. "
                "يرجى المحاولة مرة أخرى بعد قليل.",
                ""
            )

        # --------------------------------------------------
        # AUTO
        # --------------------------------------------------

        if chosen == "auto":

            # الطلبات البرمجية أو المعقدة
            if routed_need == "coding-reasoning":

                auto_models = [
                    "gemini-3.7-flash",
                    "gemini-3.6-flash",
                    "gemini-3.5-flash",
                    "gemini-3.5-flash-lite"
                ]

            # الصور تحتاج موديل متعدد الوسائط قوي
            elif image_bytes:

                auto_models = [
                    "gemini-3.6-flash",
                    "gemini-3.7-flash",
                    "gemini-3.5-flash"
                ]

            # الطلبات العادية نبدأ بالأسرع
            else:

                auto_models = [
                    "gemini-3.6-flash",
                    "gemini-3.5-flash",
                    "gemini-3.5-flash-lite"
                ]

            if self.gemini.is_available():

                try:

                    response, used_model = (
                        await self._try_gemini_models(
                            auto_models,
                            final_prompt,
                            system_instruction,
                            history,
                            image_bytes
                        )
                    )

                    self.db.log_usage(
                        telegram_id,
                        "ai_generation",
                        len(final_prompt) + len(response)
                    )

                    return response, provider_notes

                except Exception as e:

                    logger.warning(
                        f"Auto Gemini routing failed: {e}"
                    )

            # Gemini كله فشل → OpenAI
            if self.openai.is_available():

                try:

                    response = await self.openai.generate_response(
                        prompt=final_prompt,
                        system_instruction=system_instruction,
                        history=history,
                        image_bytes=image_bytes
                    )

                    provider_notes += (
                        "⚠️ تم التحويل تلقائيًا إلى OpenAI "
                        "بعد تعذر استخدام Gemini.\n"
                    )

                    self.db.log_usage(
                        telegram_id,
                        "ai_generation_fallback",
                        len(final_prompt) + len(response)
                    )

                    return response, provider_notes

                except Exception as e:

                    logger.error(
                        f"Auto OpenAI fallback failed: {e}"
                    )

            return (
                "عذرًا، تعذر معالجة طلبك حاليًا. "
                "يرجى المحاولة مرة أخرى بعد قليل.",
                ""
            )

        # --------------------------------------------------
        # Unknown selection
        # --------------------------------------------------

        return (
            "عذرًا، اختيار الموديل غير صالح. "
            "استخدم /models لاختيار موديل صحيح.",
            ""
        )