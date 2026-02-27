import os
import requests
import time
import json
from datetime import datetime

# ===== КОНФИГУРАЦИЯ =====
TOKEN = os.environ.get("MAX_BOT_TOKEN")
if not TOKEN:
    print("❌ Ошибка: не задан токен в переменных окружения")
    exit(1)
API_URL = "https://platform-api.max.ru"
HEADERS = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}
last_marker = 0
bot_name = "Имя бота"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_updates():
    global last_marker
    try:
        params = {"timeout": 30}
        if last_marker:
            params['marker'] = last_marker
        r = requests.get(f"{API_URL}/updates", headers=HEADERS, params=params, timeout=35)
        if r.status_code == 200:
            data = r.json()
            updates = data.get('updates', [])
            new_marker = data.get('marker', last_marker)
            if new_marker != last_marker:
                last_marker = new_marker
            return updates
    except:
        return []
    return []

def send_message(user_id, text, keyboard=None):
    """Универсальная отправка сообщения"""
    if not user_id or not text:
        return False
    url = f"{API_URL}/messages?user_id={user_id}"
    data = {"text": text}
    if keyboard:
        data["attachments"] = [{"type": "inline_keyboard", "payload": keyboard}]
    try:
        r = requests.post(url, headers=HEADERS, json=data)
        return r.status_code == 200
    except:
        return False

def process_updates(updates):
    if not updates:
        return
    for update in updates:
        # Новое сообщение
        if update.get('update_type') == 'message_created' and 'message' in update:
            msg = update['message']
            sender = msg.get('sender', {})
            user_id = sender.get('user_id')
            user_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
            body = msg.get('body', {})
            text = body.get('text', '')
            
            log(f"💬 {user_name}: '{text}'")
            
            # Здесь ваша логика обработки сообщений
            if user_id and text:
                # Пример: простое эхо с дополнительными командами
                if text.lower() == '/start':
                    reply = f"Привет, {user_name}! Я бот {bot_name}"
                elif text.lower() == '/help':
                    reply = "Доступные команды: /start, /help, привет"
                elif 'привет' in text.lower():
                    reply = f"Привет, {user_name}! 👋"
                else:
                    reply = f"Ты написал: '{text}'"
                
                send_message(user_id, reply)
        
        # Нажатие на кнопку
        elif update.get('update_type') == 'message_callback':
            user_id = update.get('from', {}).get('user_id')
            payload = update.get('payload')
            log(f"🔘 Нажата кнопка: {payload}")
            # Обработка callback

def main():
    print("\n" + "="*50)
    print("🤖 БОТ НА ОСНОВЕ ШАБЛОНА")
    print("="*50 + "\n")
    
    # Проверка подключения
    try:
        r = requests.get(f"{API_URL}/me", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            log(f"✅ Бот: {data.get('first_name')} (@{data.get('username')})")
        else:
            log("❌ Ошибка подключения")
            return
    except:
        log("❌ Ошибка подключения")
        return
    
    log("🚀 Бот запущен и готов к работе!\n")
    
    try:
        while True:
            updates = get_updates()
            if updates:
                process_updates(updates)
            time.sleep(1)
    except KeyboardInterrupt:
        log("\n👋 Бот остановлен")

if __name__ == "__main__":
    main()
