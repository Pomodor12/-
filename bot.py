import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
import sqlite3
from datetime import datetime, timedelta

TOKEN = 7999077800:AAGAlfz6ho1xAP2spR8k_18rGy4CPdWRo3k7999077800:AAGAlfz6ho1xAP2spR8k_18rGy4CPdWRo3k

GROUP_A = -5012773570

NOTIFY_GROUPS = [
    -1001111111111,
]

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect("events.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_event(title, date, time):
    conn = sqlite3.connect("events.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO events(title, date, time) VALUES (?, ?, ?)", (title, date, time))
    conn.commit()
    conn.close()

@dp.message(F.chat.id == GROUP_A)
async def handle_event_input(message: Message):
    text = message.text.strip()
    try:
        lines = text.split("\n")
        title = lines[0].replace("Событие:", "").strip()
        date = lines[1].replace("Дата:", "").strip()
        time = lines[2].replace("Время:", "").strip()
        add_event(title, date, time)
        await message.reply(f"Добавлено событие: {title} {date} {time}")
    except Exception:
        await message.reply("Неверный формат. Пример:\nСобытие: Имя\nДата: 2025-12-05\nВремя: 18:00")

@dp.message(Command("list"))
async def list_events(message: Message):
    conn = sqlite3.connect("events.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM events")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await message.answer("Событий нет.")
        return
    text = "\n".join([f"{r[0]}. {r[1]} — {r[2]} {r[3]}" for r in rows])
    await message.answer(text)

@dp.message(Command("delete"))
async def delete_event(message: Message):
    try:
        event_id = int(message.text.split()[1])
        conn = sqlite3.connect("events.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        await message.answer("Удалено.")
    except:
        await message.answer("Используй: /delete ID")

async def reminder_worker():
    while True:
        now = datetime.now()
        target = now + timedelta(days=1)
        date_str = target.strftime("%Y-%m-%d")

        conn = sqlite3.connect("events.db")
        cur = conn.cursor()
        cur.execute("SELECT title, date, time FROM events WHERE date = ?", (date_str,))
        events = cur.fetchall()
        conn.close()

        for title, date, time in events:
            for chat_id in NOTIFY_GROUPS:
                await bot.send_message(
                    chat_id,
                    f"Напоминание! Завтра событие:\n«{title}» в {time}"
                )

        await asyncio.sleep(86400)

async def weekly_digest_worker():
    while True:
        now = datetime.now()
        if now.weekday() == 0:
            start_date = now.date()
            end_date = start_date + timedelta(days=7)

            conn = sqlite3.connect("events.db")
            cur = conn.cursor()
            cur.execute("""
                SELECT title, date, time FROM events
                WHERE date >= ? AND date < ?
                ORDER BY date, time
            """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
            events = cur.fetchall()
            conn.close()

            if events:
                text = "📅 Мероприятия на неделю:\n\n"
                for title, date, time in events:
                    text += f"• {title} — {date} {time}\n"
            else:
                text = "На эту неделю мероприятий нет."

            for chat_id in NOTIFY_GROUPS:
                await bot.send_message(chat_id, text)

        await asyncio.sleep(86400)

@dp.message(Command("getid"))
async def get_id(message: Message):
    await message.reply(f"Chat ID: {message.chat.id}")

async def main():
    init_db()
    asyncio.create_task(reminder_worker())
    asyncio.create_task(weekly_digest_worker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

