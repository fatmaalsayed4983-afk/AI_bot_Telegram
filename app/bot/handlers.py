import os
import uuid
import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.database.db_manager import DBManager
from app.bot.keyboards import Keyboards
from app.bot.middleware import BotMiddleware
from app.ai.orchestrator import Orchestrator
from app.tools.deep_research import DeepResearchTool
from app.tools.file_analyzer import FileAnalyzer
from app.tools.image_generator import ImageGeneratorTool
from app.tools.code_sandbox import CodeSandbox
from app.core.config import Config
from app.core.security import SecurityChecker

logger = logging.getLogger(__name__)

class Handlers:
    def __init__(self, db: DBManager, orchestrator: Orchestrator, middleware: BotMiddleware):
        self.db = db
        self.orchestrator = orchestrator
        self.middleware = middleware
        self.active_conversations = {}  # user_id -> conversation_id

    def get_current_conv(self, user_id: int) -> str:
        if user_id not in self.active_conversations:
            # Try getting last conversation from database
            convs = self.db.get_user_conversations(user_id)
            if convs:
                self.active_conversations[user_id] = convs[0]['conversation_id']
            else:
                new_id = str(uuid.uuid4())
                self.db.create_conversation(new_id, user_id, "محادثة تلقائية")
                self.active_conversations[user_id] = new_id
        return self.active_conversations[user_id]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username or f"user_{user_id}"
        
        # Register or update user
        self.middleware.process_user(user_id, username)
        self.get_current_conv(user_id)
        
        welcome_text = (
            "👋 <b>مرحباً بك في مساعد تيليجرام الذكي المتكامل!</b>\n\n"
            "هذا المساعد يدار بالكامل عبر تقنيات الذكاء الاصطناعي الأقوى (OpenAI & Gemini).\n\n"
            "🚀 <b>أبرز المزايا والوظائف المتاحة:</b>\n"
            "- إجابات أسئلة طبيعية ونقاش حر.\n"
            "- تحليل الصور والملفات والمستندات بذكاء.\n"
            "- البحث المباشر في الويب وجلب آخر التطورات.\n"
            "- وضع مخصص للتطوير والبرمجة مع تشغيل الكود بشكل آمن.\n"
            "- ذاكرة طويلة المدى وخصوصية تامة معزولة لكل مستخدم.\n\n"
            "👇 <b>استخدم القائمة التفاعلية أدناه للتحكم بجميع الخصائص:</b>"
        )
        await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=Keyboards.main_menu())

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📖 <b>دليل الأوامر السريعة المتاحة للمساعد الذكي:</b>\n\n"
            "/start - تشغيل البوت وفتح القائمة التفاعلية\n"
            "/help - عرض شاشة المساعدة الحالية\n"
            "/new - بدء محادثة جديدة كلياً\n"
            "/models - اختيار وتفضيل نموذج الذكاء الاصطناعي\n"
            "/settings - ضبط خيارات الويب والبحث والملفات\n"
            "/memory - عرض وحذف معلومات الذاكرة طويلة المدى\n"
            "/image &lt;الوصف&gt; - توليد صور ممتازة بـ AI\n"
            "/research &lt;موضوع البحث&gt; - إجراء بحث عميق عبر الإنترنت\n"
            "/code &lt;الكود&gt; - تشغيل آمن وموثوق لأكواد بايثون\n"
            "/clear - مسح كافة محتويات المحادثة الحالية\n"
            "/health - فحص واختبار الاتصال والجهوزية والمزودات\n"
            "/admin - لوحة إدارة المشرفين الخاصة بالنظام"
        )
        await update.message.reply_text(help_text, parse_mode="HTML")

    async def new_conv_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        new_id = str(uuid.uuid4())
        self.db.create_conversation(new_id, user_id, f"محادثة رقم {len(self.db.get_user_conversations(user_id)) + 1}")
        self.active_conversations[user_id] = new_id
        await update.message.reply_text("✨ تم بدء محادثة جديدة وتصفير سياق الردود المتراكم بنجاح.")

    async def models_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        settings = self.db.get_settings(user_id)
        current_model = settings['default_model'] if settings else 'auto'
        await update.message.reply_text(
            f"🤖 <b>قائمة نماذج الذكاء الاصطناعي المتاحة:</b>\nالموديل المفضل المختار حالياً: <b>{current_model}</b>",
            parse_mode="HTML",
            reply_markup=Keyboards.models_menu(current_model)
        )

    async def settings_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        settings = self.db.get_settings(user_id)
        search_enabled = bool(settings['web_search_enabled']) if settings else True
        await update.message.reply_text(
            "⚙️ <b>إعدادات المساعد والاتصال بالويب:</b>",
            parse_mode="HTML",
            reply_markup=Keyboards.settings_menu(search_enabled)
        )

    async def memory_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        memories = self.db.get_memories(user_id)
        if not memories:
            await update.message.reply_text("🧠 ذاكرتك المخصصة فارغة حتى الآن. يمكنك إرسال معلومات مثل 'اسمي أحمد' ليقوم المساعد بحفظها وتذكرها تلقائياً.")
            return
            
        mem_list = []
        for m in memories:
            mem_list.append(f"🔸 {m['memory_text']} (حذف: /del_mem_{m['memory_id']})")
        
        text = "🧠 <b>الذاكرة طويلة المدى المسجلة الخاصة بك:</b>\n\n" + "\n".join(mem_list)
        await update.message.reply_text(text, parse_mode="HTML")

    async def delete_memory_via_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        cmd = update.message.text
        mem_id_str = cmd.replace("/del_mem_", "").strip()
        if mem_id_str.isdigit():
            self.db.delete_memory(int(mem_id_str))
            await update.message.reply_text("✅ تم حذف هذه المعلومة المحددة من ذاكرتك بنجاح.")
        else:
            await update.message.reply_text("⚠️ معرف الذاكرة غير صالح.")

    async def image_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        prompt = " ".join(context.args)
        if not prompt:
            await update.message.reply_text("⚠️ يرجى كتابة وصف الصورة بعد الأمر. مثال:\n/image فضاء خارجي بأسلوب سايبربانك")
            return
            
        await update.message.reply_text("🎨 جاري معالجة وتوليد الصورة بذكاء، يرجى الانتظار قليلاً...")
        try:
            image_bytes = await ImageGeneratorTool.generate(
                prompt,
                self.orchestrator.gemini
            )

            image_bytes = await ImageGeneratorTool.generate(
                prompt,
                self.orchestrator.gemini
            )

            await update.message.reply_photo(
                photo=image_bytes,
                caption=f"🖼️ الصورة المولدة من أجلك لوصف: {prompt[:100]}"
            )

        except Exception as e:
            logger.error(
                f"Gemini image generation failure: {e}"
            )

            await update.message.reply_text(
                "❌ عذرًا، حدث خطأ أثناء توليد الصورة بواسطة Gemini."
            )

    async def research_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        topic = " ".join(context.args)
        if not topic:
            await update.message.reply_text("⚠️ يرجى كتابة موضوع البحث بعد الأمر. مثال:\n/research مستقبل الحوسبة الكمية")
            return
            
        await update.message.reply_text("🔬 جاري إجراء البحث العميق والتحقق من المصادر ومقارنتها تلقائياً...")
        try:
            report = await DeepResearchTool.conduct_research(topic)
            await update.message.reply_text(report, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            await update.message.reply_text(f"❌ فشل إجراء البحث العميق بسبب خطأ: {e}")

    async def code_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        code = " ".join(context.args)
        if not code:
            await update.message.reply_text("⚠️ يرجى إدخال الكود البرمجي بعد الأمر لتشغيله في البيئة الآمنة. مثال:\n/code print(1 + 1)")
            return
            
        await update.message.reply_text("⚙️ جاري تشغيل الكود في بيئة معزولة (Sandbox)... ")
        output = CodeSandbox.execute_python_code(code)
        safe_output = SecurityChecker.sanitize_html_text(output)
        await update.message.reply_text(f"💻 <b>مخرجات التشغيل:</b>\n<pre>{safe_output}</pre>", parse_mode="HTML")

    async def clear_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        conv_id = self.get_current_conv(user_id)
        self.db.clear_conversation(conv_id)
        await update.message.reply_text("🗑️ تم مسح رسائل وسياق المحادثة الحالية بنجاح.")

    async def health_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        openai_status = "متصل جاهز ✅" if self.orchestrator.openai.is_available() else "غير متاح ❌"
        gemini_status = "متصل جاهز ✅" if self.orchestrator.gemini.is_available() else "غير متاح ❌"
        db_status = "نشط ومتصل ✅" if self.db.conn else "غير متصل ❌"
        
        health_msg = (
            "❤️ <b>حالة وسلامة البوت والنظام المتكامل:</b>\n\n"
            f"💻 حالة قاعدة البيانات: <b>{db_status}</b>\n"
            f"🤖 مزود OpenAI: <b>{openai_status}</b>\n"
            f"🤖 مزود Google Gemini: <b>{gemini_status}</b>\n"
            f"🛡️ بيئة Sandbox البرمجية: <b>نشطة ومؤمنة ✅</b>\n"
            f"📂 حد الملف المسموح به: <b>{Config.MAX_FILE_SIZE_MB} ميجابايت</b>\n\n"
            "<i>يعمل النظام حالياً بكفاءة عالية على السيرفر ومستعد لخدمتك 24/7!</i>"
        )
        await update.message.reply_text(health_msg, parse_mode="HTML")

    async def admin_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.db.get_or_create_user(user_id, "")
        if user['role'] != 'admin':
            await update.message.reply_text("🚫 عذرًا، لا تملك الصلاحية للوصول إلى لوحة الإدارة الحساسة.")
            return
            
        await update.message.reply_text(
            "👨‍💼 <b>مرحباً بك في لوحة تحكم المشرفين والمدراء:</b>",
            parse_mode="HTML",
            reply_markup=Keyboards.admin_panel()
        )

    # Callback Query handlers
    async def handle_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        await query.answer()
        
        # Process user registration
        self.middleware.process_user(user_id, query.from_user.username or "")
        
        if data == "back_to_main":
            await query.edit_message_text(
                "👇 <b>استخدم القائمة التفاعلية أدناه للتحكم بجميع الخصائص:</b>",
                parse_mode="HTML",
                reply_markup=Keyboards.main_menu()
            )
        elif data == "menu_models":
            settings = self.db.get_settings(user_id)
            current_model = settings['default_model'] if settings else 'auto'
            await query.edit_message_text(
                f"🤖 <b>قائمة نماذج الذكاء الاصطناعي المتاحة:</b>\nالموديل المفضل المختار حالياً: <b>{current_model}</b>",
                parse_mode="HTML",
                reply_markup=Keyboards.models_menu(current_model)
            )
        elif data.startswith("set_model_"):
            model = data.replace("set_model_", "")
            self.db.update_setting(user_id, 'default_model', model)
            await query.edit_message_text(
                f"✅ تم تعديل الموديل الافتراضي إلى: <b>{model}</b> بنجاح.",
                parse_mode="HTML",
                reply_markup=Keyboards.models_menu(model)
            )
        elif data == "menu_settings":
            settings = self.db.get_settings(user_id)
            search_enabled = bool(settings['web_search_enabled']) if settings else True
            await query.edit_message_text(
                "⚙️ <b>إعدادات المساعد والاتصال بالويب:</b>",
                parse_mode="HTML",
                reply_markup=Keyboards.settings_menu(search_enabled)
            )
        elif data == "toggle_setting_search":
            settings = self.db.get_settings(user_id)
            current = bool(settings['web_search_enabled']) if settings else True
            new_val = 0 if current else 1
            self.db.update_setting(user_id, 'web_search_enabled', new_val)
            await query.edit_message_text(
                "⚙️ <b>إعدادات المساعد والاتصال بالويب:</b>",
                parse_mode="HTML",
                reply_markup=Keyboards.settings_menu(bool(new_val))
            )
        elif data == "menu_convs":
            convs = self.db.get_user_conversations(user_id)
            current_id = self.get_current_conv(user_id)
            text = "💬 <b>قائمة المحادثات الخاصة بك:</b>\n\n"
            for c in convs:
                prefix = "▶️ (الحالية) " if c['conversation_id'] == current_id else "▫️ "
                text += f"{prefix}{c['title']} (معرف: {c['conversation_id'][:8]})\n"
            
            await query.edit_message_text(
                text,
                parse_mode="HTML",
                reply_markup=Keyboards.conversation_options(current_id)
            )
        elif data == "menu_new_conv":
            new_id = str(uuid.uuid4())
            self.db.create_conversation(new_id, user_id, f"محادثة رقم {len(self.db.get_user_conversations(user_id)) + 1}")
            self.active_conversations[user_id] = new_id
            await query.edit_message_text("✨ تم فتح محادثة جديدة فارغة كلياً بنجاح! يمكنك البدء بالكتابة الآن.")
        elif data.startswith("clear_conv_"):
            cid = data.replace("clear_conv_", "")
            self.db.clear_conversation(cid)
            await query.edit_message_text("🗑️ تم تصفير ومسح رسائل المحادثة المحددة.")
        elif data.startswith("delete_conv_"):
            cid = data.replace("delete_conv_", "")
            self.db.delete_conversation(cid)
            # Reset active conversation
            if user_id in self.active_conversations:
                del self.active_conversations[user_id]
            await query.edit_message_text("❌ تم حذف المحادثة تماماً من قاعدة البيانات.")
        elif data == "menu_memory":
            memories = self.db.get_memories(user_id)
            if not memories:
                await query.edit_message_text(
                    "🧠 ذاكرتك المخصصة فارغة حتى الآن. يمكنك إرسال معلومات مثل 'اسمي أحمد' ليقوم المساعد بحفظها وتذكرها تلقائياً.",
                    reply_markup=Keyboards.main_menu()
                )
                return
            mem_list = [f"🔸 {m['memory_text']}" for m in memories]
            text = "🧠 <b>الذاكرة طويلة المدى المسجلة الخاصة بك:</b>\n\n" + "\n".join(mem_list)
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=Keyboards.main_menu())
        elif data == "menu_deep_research":
            await query.edit_message_text("🔬 لإجراء بحث عميق وتوليد تقرير ويب شامل ومطول وموثق، أرسل الأمر بالطريقة التالية:\n\n/research <i>موضوع البحث المطلوب بالتفصيل</i>", parse_mode="HTML")
        elif data == "menu_img_generate":
            await query.edit_message_text("🖼️ لتوليد صور ذكية فائقة الدقة باستخدام DALL-E 3، أرسل الأمر بالطريقة التالية:\n\n/image <i>وصف تفصيلي كامل للصورة المراد إنشاؤها</i>", parse_mode="HTML")
        elif data == "menu_programmer":
            await query.edit_message_text("👨‍💻 <b>وضع البرمجة وتشغيل الأكواد:</b>\n\nأرسل الكود عبر استخدام الأمر المباشر:\n/code <i>الكود هنا</i>\n\nأو قم بإرسال ملف برمجي يحمل الإمتداد (py, js, html, sql) مرفقاً بنص مثل 'اشرح الكود' وسنقوم بتحليله فوراً!", parse_mode="HTML")
        elif data == "menu_health":
            openai_status = "متصل جاهز ✅" if self.orchestrator.openai.is_available() else "غير متاح ❌"
            gemini_status = "متصل جاهز ✅" if self.orchestrator.gemini.is_available() else "غير متاح ❌"
            db_status = "نشط ومتصل ✅" if self.db.conn else "غير متصل ❌"
            
            health_msg = (
                "❤️ <b>حالة وسلامة البوت والنظام المتكامل:</b>\n\n"
                f"💻 حالة قاعدة البيانات: <b>{db_status}</b>\n"
                f"🤖 مزود OpenAI: <b>{openai_status}</b>\n"
                f"🤖 مزود Google Gemini: <b>{gemini_status}</b>\n"
                f"🛡️ بيئة Sandbox البرمجية: <b>نشطة ومؤمنة ✅</b>\n"
                f"📂 حد الملف المسموح به: <b>{Config.MAX_FILE_SIZE_MB} ميجابايت</b>\n\n"
                "<i>يعمل النظام حالياً بكفاءة عالية على السيرفر ومستعد لخدمتك 24/7!</i>"
            )
            await query.edit_message_text(health_msg, parse_mode="HTML", reply_markup=Keyboards.main_menu())
        elif data == "admin_stats":
            stats = self.db.get_system_stats()
            text = (
                "📊 <b>إحصائيات استهلاك وتفاعل البوت بالكامل:</b>\n\n"
                f"👥 إجمالي المستخدمين: <b>{stats['total_users']}</b>\n"
                f"💬 إجمالي غرف المحادثة: <b>{stats['total_conversations']}</b>\n"
                f"✉️ إجمالي الرسائل المخزنة: <b>{stats['total_messages']}</b>\n"
                f"🔥 إجمالي الأحرف المستهلكة: <b>{stats['total_tokens']}</b>"
            )
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=Keyboards.admin_panel())
        elif data == "admin_users":
            users = self.db.get_all_users_admin()
            text = "👥 <b>قائمة المسجلين حالياً بالنظام:</b>\n\n"
            for u in users:
                text += f"👤 {u['username']} (ID: <code>{u['telegram_id']}</code>) - رصيد: {u['credits']} | نشاط: {u['daily_usage']}\n"
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=Keyboards.admin_panel())

    # Text Message handler
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username or f"user_{user_id}"
        text = update.message.text
        
        # Rate limit check
        if self.middleware.is_rate_limited(user_id):
            await update.message.reply_text("⚠️ يرجى التمهل وتجنب إرسال الكثير من الطلبات في وقت واحد لحماية موارد الخادم.")
            return
            
        user = self.middleware.process_user(user_id, username)
        if not user['is_active']:
            await update.message.reply_text("🚫 حسابك معطل حالياً من قِبل المشرفين.")
            return
            
        conv_id = self.get_current_conv(user_id)
        
        # Try Memory Extraction first if configured
        if Config.ENABLE_MEMORY:
            from app.ai.memory import MemorySystem
            extracted = MemorySystem.parse_and_extract_memory(text)
            if extracted:
                self.db.add_memory(user_id, extracted)
                await update.message.reply_text("🧠 تم حفظ هذه المعلومة كإحدى تفضيلاتك في الذاكرة طويلة المدى لتخصيص محادثاتنا مستقبلاً!")

        # Keep history of User input
        self.db.add_message(conv_id, "user", text)
        
        # Show typing status
        await update.message.reply_chat_action("typing")
        
        # Forward to Orchestrator
        response, notes = await self.orchestrator.process_ai_request(user_id, conv_id, text)
        
        # إرسال رد الذكاء الاصطناعي كنص عادي بدون HTML
        final_text = response

        if notes:
            final_text = f"{notes}\n{final_text}"

        # Save Assistant Response
        self.db.add_message(conv_id, "assistant", response)

        # Split message if exceeds Telegram character limit
        if len(final_text) > 4000:
            chunks = [
                final_text[i:i+4000]
                for i in range(0, len(final_text), 4000)
            ]

            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(final_text)
    # Document & Attachment handler
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        doc = update.message.document
        caption = update.message.caption or ""
        
        # Validate file constraints
        max_size = Config.MAX_FILE_SIZE_MB * 1024 * 1024
        if doc.file_size > max_size:
            await update.message.reply_text(f"⚠️ حجم الملف يتجاوز الحد الأقصى المسموح به في الإعدادات ({Config.MAX_FILE_SIZE_MB} ميجابايت).")
            return
            
        # Download locally to temp directory
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        file_obj = await context.bot.get_file(doc.file_id)
        file_ext = os.path.splitext(doc.file_name)[1].lower()
        temp_dest = os.path.join(Config.TEMP_DIR, f"{uuid.uuid4()}{file_ext}")
        
        # Verify path security
        if not SecurityChecker.is_safe_path(Config.TEMP_DIR, temp_dest):
            await update.message.reply_text("⚠️ الكشف عن محاولة تلاعب بالمسارات غير مصرح بها!")
            return
            
        await update.message.reply_text("⏳ جاري تحميل وتجميع محتويات المستند للتحليل...")
        await file_obj.download_to_drive(temp_dest)
        
        try:
            # Analyze content
            content = FileAnalyzer.analyze_file_content(temp_dest, file_ext)
            
            if len(content.strip()) < 5:
                await update.message.reply_text("⚠️ فشل استخراج محتوى نصي ذو قيمة من هذا الملف المعين.")
                return
                
            # Send as AI prompt context
            conv_id = self.get_current_conv(user_id)
            instruction = f"لقد قام المستخدم بمشاركتنا ملف تحت عنوان '{doc.file_name}'. محتويات هذا الملف المقتطفة:\n\n{content}\n\nالمستخدم يتساءل بخصوص هذا الملف: {caption or 'قم بتلخيص وشرح الكود والملف بشكل متكامل.'}"
            
            await update.message.reply_chat_action("typing")
            response, notes = await self.orchestrator.process_ai_request(user_id, conv_id, instruction)
            
            safe_text = SecurityChecker.sanitize_html_text(response)
            await update.message.reply_text(f"<b>📂 نتيجة تحليل الملف المرفوع:</b>\n\n{safe_text}", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Document Handling failure: {e}")
            await update.message.reply_text(f"❌ فشل معالجة الملف بسبب خطأ غير متوقع: {e}")
        finally:
            # Clean up immediately
            if os.path.exists(temp_dest):
                try:
                    os.remove(temp_dest)
                except:
                    pass

    # Image handling with vision
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        caption = update.message.caption or "اشرح هذه الصورة بالتفصيل وما الذي تحتويه؟"
        
        # Get largest photo size available
        photo_file = update.message.photo[-1]
        
        await update.message.reply_text("👁️ جاري تحميل الصورة ونقلها لنظام الرؤية الحاسوبية المعزز بالذكاء الاصطناعي...")
        
        # Download raw bytes
        img_obj = await context.bot.get_file(photo_file.file_id)
        
        # Keep temp file
        temp_dest = os.path.join(Config.TEMP_DIR, f"{uuid.uuid4()}.jpg")
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        await img_obj.download_to_drive(temp_dest)
        
        try:
            with open(temp_dest, 'rb') as f:
                image_bytes = f.read()
                
            conv_id = self.get_current_conv(user_id)
            await update.message.reply_chat_action("typing")
            
            response, notes = await self.orchestrator.process_ai_request(
                telegram_id=user_id,
                conversation_id=conv_id,
                prompt=caption,
                image_bytes=image_bytes
            )
            
            safe_text = SecurityChecker.sanitize_html_text(response)
            await update.message.reply_text(f"<b>🖼️ نتيجة فحص الصورة ورؤيتها:</b>\n\n{safe_text}", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Photo handling failure: {e}")
            await update.message.reply_text(f"❌ فشل تحليل الصورة بسبب خطأ: {e}")
        finally:
            if os.path.exists(temp_dest):
                try:
                    os.remove(temp_dest)
                except:
                    pass
