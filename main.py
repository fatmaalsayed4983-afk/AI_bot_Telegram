import sys
import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Adjust python path if executed differently
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import Config
from app.core.logging_config import setup_logging
from app.database.db_manager import DBManager
from app.ai.orchestrator import Orchestrator
from app.bot.middleware import BotMiddleware
from app.bot.handlers import Handlers

setup_logging()
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing database layer...")
    db = DBManager()
    
    logger.info("Starting AI orchestrator and services...")
    orchestrator = Orchestrator(db)
    
    logger.info("Loading bot middlewares...")
    middleware = BotMiddleware(db)
    
    logger.info("Configuring telegram bot application event loops...")
    handlers = Handlers(db, orchestrator, middleware)
    
    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN missing inside environment parameters!")
        print("Error: Please supply TELEGRAM_BOT_TOKEN in your env parameters.")
        sys.exit(1)
        
    app = ApplicationBuilder().token(token).build()
    
    # Register command route handlers
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))
    app.add_handler(CommandHandler("new", handlers.new_conv_cmd))
    app.add_handler(CommandHandler("models", handlers.models_cmd))
    app.add_handler(CommandHandler("settings", handlers.settings_cmd))
    app.add_handler(CommandHandler("memory", handlers.memory_cmd))
    app.add_handler(CommandHandler("image", handlers.image_cmd))
    app.add_handler(CommandHandler("research", handlers.research_cmd))
    app.add_handler(CommandHandler("code", handlers.code_cmd))
    app.add_handler(CommandHandler("clear", handlers.clear_cmd))
    app.add_handler(CommandHandler("health", handlers.health_cmd))
    app.add_handler(CommandHandler("admin", handlers.admin_cmd))
    
    # Handle custom command delete memory
    app.add_handler(MessageHandler(filters.Regex(r'^/del_mem_\d+$'), handlers.delete_memory_via_cmd))
    
    # Callback Query (Buttons clicking events)
    app.add_handler(CallbackQueryHandler(handlers.handle_callbacks))
    
    # Content analysis routes
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handlers.handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    
    logger.info("Bot polling system active. Ready to process queries...")
    app.run_polling()

if __name__ == "__main__":
    main()
