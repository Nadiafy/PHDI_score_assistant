import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, BotCommand
from aiogram.filters import Command
from dotenv import load_dotenv

# Import the logic that already exists in the FastAPI app
from nutrition_service import parse_food_log, get_nutritional_data, map_to_phdi
from phdi_logic import calculate_phdi_score

from database import async_session_maker
from models import User, DailyLog
from auth import verify_telegram_link_token
from sqlalchemy.future import select

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Bot and Dispatcher
# Since we will be running this alongside FastAPI, we initialize it without passing the token yet if it's not set
bot = None
if TELEGRAM_BOT_TOKEN:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

dp = Dispatcher()

# Commands : 
@dp.message(Command("start"))
async def send_welcome(message: Message):
    """
    This handler will be called when user sends `/start` command
    """
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        token = args[1]
        user_id = verify_telegram_link_token(token)
        if user_id:
            if user_id == "00000000-0000-0000-0000-000000000000":
                await message.answer("✅ (Dev Mode) Successfully connected your Web account with Telegram!")
                return
            try:
                async with async_session_maker() as session:
                    result = await session.execute(select(User).where(User.id == user_id))
                    user = result.scalars().first()
                    if user:
                        user.telegram_id = message.from_user.id
                        await session.commit()
                        await message.answer("✅ Successfully connected your Web account with Telegram!")
                        return
                    else:
                        await message.answer("❌ Could not find an associated Web account.")
                        return
            except Exception as e:
                print(f"Database error during Telegram link: {e}")
                await message.answer("❌ Database connection failed. Please log in with the Dev Bypass, or ensure PostgreSQL is running.")
                return
        await message.answer("❌ Invalid or expired connection link.")
        return

    welcome_text = (
        "Welcome to the PHDI Score Bot! 🍎🥦\n\n"
        "I can help you log your meals and calculate your Planetary Health Diet Index (PHDI) score.\n\n"
        "Just send me what you ate. For example:\n"
        "👉 <i>I had 2 boiled eggs and a slice of whole wheat bread for breakfast.</i>\n\n"
        "💡 Type /help at any time for tips on how to use this bot!"
    )
    await message.answer(welcome_text, parse_mode="HTML")


@dp.message(Command("help"))
async def send_help(message: Message):
    """
    This handler will be called when user sends `/help` command
    """
    help_text = (
        "<b>What is PHDI Score Bot?</b> 🌱\n"
        "This bot helps you track your diet's environmental impact based on the Planetary Health Diet Index (PHDI).\n\n"
        "<b>How to use it?</b> 📝\n"
        "1. Simply type what you ate as a single message.\n"
        "2. Include quantities and food types (e.g., '150g' or 'a bowl of').\n"
        "3. Wait a moment while I analyze the ingredients and calculate your score.\n\n"
        "<b>Examples of good input:</b>\n"
        "• <i>150g of grilled chicken breast and a bowl of mixed greens</i>\n"
        "• <i>A bowl of oatmeal with a handful of almonds and half an apple</i>\n"
        "• <i>2 boiled eggs and a slice of whole wheat bread</i>\n\n"
        "The closer your score is to 150, the better your diet is for both you and the planet! 🌍💚"
    )
    await message.answer(help_text, parse_mode="HTML")


@dp.message()
async def process_food_log(message: Message):
    """
    This handler will process any other text message as a food log
    """
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    user_text = message.text
    print("user_text:",user_text)
    
    await message.answer("⏳ Calculating PHDI...")
    
    try:
        from crud import upsert_daily_log, get_user_by_telegram_id
        # 1. Parse log using the Gemini parser from nutrition_service
        items = await asyncio.to_thread(parse_food_log, user_text)
        print("items:",items)
        # 2. Get nutrition and mapping
        enriched_items = []
        for item in items:
            nutri = await asyncio.to_thread(get_nutritional_data, item["food_item"], item["quantity_g"])
            item.update(nutri)
            enriched_items.append(item)
            
        # 3. Aggregate to PHDI categories
        percentages = map_to_phdi(enriched_items)
        
        # 4. Calculate score
        result = calculate_phdi_score(percentages)
        
        # 5. DB Upsert
        user = None
        try:
            async with async_session_maker() as session:
                user = await get_user_by_telegram_id(session, message.from_user.id)
                if user:
                    await upsert_daily_log(
                        db=session,
                        user_id=user.id,
                        log_text=user_text,
                        total_score=result['total_score'],
                        component_scores=result['component_scores'],
                        source='telegram'
                    )
        except Exception as e:
            print(f"Skipping DB upsert due to error: {e}")
        
        # 6. Format the response
        response_text = format_response(enriched_items, result)
        if not user:
            response_text += "\n\n<i>⚠️ To save this score to your history, link your Telegram account from the Web Dashboard Profile!</i>"
        
        print(f"\nbot_response:\n{response_text}\n")
        await message.answer(response_text, parse_mode="HTML")

    except ValueError as e:
        await message.answer(str(e))
    except Exception as e:
        error_text = f"Sorry, I couldn't process that. Make sure to describe your meal clearly.\n\nError: {str(e)}"
        print("error_text:",error_text)
        await message.answer(error_text)


# Format the response
def format_response(items: list, result: dict) -> str:
    """Formats the calculation result into a readable HTML message for Telegram"""
    
    # Format the parsed items
    items_text = "<b>📝 Parsed Items:</b>\n"
    for item in items:
        food_name = str(item.get('food_item', 'Unknown')).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        category_name = str(item.get('phdi_category', 'other')).replace('_', ' ').title()
        items_text += f"• {food_name} ({item.get('quantity_g', 0)}g) - <i>{category_name}</i>\n"
    
    # Format the component scores
    scores_text = "\n<b>📊 Component Scores:</b>\n"
    for category, score in result.get("component_scores", {}).items():
        max_score = 5 if "ratio" in category else 10
        addon = ""
        if score == 0:
            if category in ["red_meat", "chicken_and_substitutes", "animal_fats", "added_sugars"]:
                addon = " (Over the planetary limit!)"
            elif category in ["nuts_and_peanuts", "legumes", "fruits", "total_vegetables", "whole_cereals"]:
                addon = " (Below the recommended intake!)"
            else:
                addon = " (Needs improvement!)"
                
        scores_text += f"• {category.replace('_', ' ').title()}: {score}/{max_score}{addon}\n"

    # Overall Score
    total_score = result.get("total_score", 0)
    score_text = f"\n<b>🌍 Total PHDI Score: {total_score}/150</b>\n"
    
    # Add a little feedback based on the score
    if total_score > 120:
        score_text += "🌟 Fantastic! Your meal is perfectly aligned with the Planetary Health Diet."
    elif total_score > 75:
        score_text += "👍 Good job! You are making steps towards a sustainable diet."
    else:
        score_text += "🥗 Room for improvement! Try incorporating more plant-based foods."

    return f"{items_text}{scores_text}{score_text}"


async def start_telegram_bot():
    """
    Starts the Telegram bot polling mechanism.
    This function will be launched as an asyncio task by the FastAPI app.
    """
    if bot is None:
        print("TELEGRAM_BOT_TOKEN is not set. Telegram Bot will NOT start.")
        return
        
    print("Starting Telegram Bot Polling...")
    
    # Set the menu commands so users can just click them
    await bot.set_my_commands([
        BotCommand(command="start", description="Start interacting with the bot"),
        BotCommand(command="help", description="Get tips on how to use the bot")
    ])
    
    # Drop any pending updates so the bot doesn't process old messages on startup
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
