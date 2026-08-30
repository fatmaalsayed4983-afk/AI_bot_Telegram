from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Keyboards:

    @staticmethod
    def main_menu():

        keyboard = [

            [
                InlineKeyboardButton(
                    "🤖 اختيار الموديل",
                    callback_data="menu_models"
                ),
                InlineKeyboardButton(
                    "💬 المحادثات",
                    callback_data="menu_convs"
                )
            ],

            [
                InlineKeyboardButton(
                    "🧠 الذاكرة",
                    callback_data="menu_memory"
                ),
                InlineKeyboardButton(
                    "🌐 البحث الذكي",
                    callback_data="menu_search_toggle"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔬 Deep Research",
                    callback_data="menu_deep_research"
                ),
                InlineKeyboardButton(
                    "🖼️ توليد الصور",
                    callback_data="menu_img_generate"
                )
            ],

            [
                InlineKeyboardButton(
                    "👨‍💻 وضع البرمجة",
                    callback_data="menu_programmer"
                ),
                InlineKeyboardButton(
                    "⚙️ الإعدادات",
                    callback_data="menu_settings"
                )
            ],

            [
                InlineKeyboardButton(
                    "❤️ حالة النظام",
                    callback_data="menu_health"
                )
            ]

        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def models_menu(current: str):

        def mark(model):
            return " ✅" if current == model else ""

        keyboard = [

            [
                InlineKeyboardButton(
                    f"🔄 تلقائي{mark('auto')}",
                    callback_data="set_model_auto"
                )
            ],

            [
                InlineKeyboardButton(
                    f"🧠 Gemini 3.7 Flash{mark('gemini-3.7-flash')}",
                    callback_data="set_model_gemini-3.7-flash"
                )
            ],

            [
                InlineKeyboardButton(
                    f"⚡ Gemini 3.6 Flash{mark('gemini-3.6-flash')}",
                    callback_data="set_model_gemini-3.6-flash"
                )
            ],

            [
                InlineKeyboardButton(
                    f"🚀 Gemini 3.5 Flash{mark('gemini-3.5-flash')}",
                    callback_data="set_model_gemini-3.5-flash"
                )
            ],

            [
                InlineKeyboardButton(
                    f"💨 Gemini 3.5 Flash-Lite{mark('gemini-3.5-flash-lite')}",
                    callback_data="set_model_gemini-3.5-flash-lite"
                )
            ],

            [
                InlineKeyboardButton(
                    f"🤖 OpenAI GPT-4o-mini{mark('openai')}",
                    callback_data="set_model_openai"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 رجوع",
                    callback_data="back_to_main"
                )
            ]

        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def settings_menu(search_enabled: bool):

        search_status = (
            "مفعّل ✅"
            if search_enabled
            else "معطّل ❌"
        )

        keyboard = [

            [
                InlineKeyboardButton(
                    f"البحث في الإنترنت: {search_status}",
                    callback_data="toggle_setting_search"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 رجوع",
                    callback_data="back_to_main"
                )
            ]

        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def conversation_options(conv_id: str):

        keyboard = [

            [
                InlineKeyboardButton(
                    "🗑️ مسح الرسائل",
                    callback_data=f"clear_conv_{conv_id}"
                ),

                InlineKeyboardButton(
                    "❌ حذف بالكامل",
                    callback_data=f"delete_conv_{conv_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🆕 محادثة جديدة",
                    callback_data="menu_new_conv"
                ),

                InlineKeyboardButton(
                    "🔙 رجوع",
                    callback_data="menu_convs"
                )
            ]

        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_panel():

        keyboard = [

            [
                InlineKeyboardButton(
                    "📊 إحصائيات النظام",
                    callback_data="admin_stats"
                ),

                InlineKeyboardButton(
                    "👥 قائمة الأعضاء",
                    callback_data="admin_users"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 القائمة الرئيسية",
                    callback_data="back_to_main"
                )
            ]

        ]

        return InlineKeyboardMarkup(keyboard)