import os
import requests
import time
import json
from datetime import datetime

# ===== ТОКЕНЫ =====
MAX_TOKEN = "f9LHodD0cOIlOQST64PdLJilm7jV31nVps-dm6HpLXYakYGm8TTfG3D6UPDqn7UQHYynY1GVvfK7iVeTudbE"
DEEPSEEK_KEY = "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"

# Для отслеживания обработанных сообщений
processed_messages = set()

if not MAX_TOKEN:
    print("❌ Ошибка: нет токена MAX")
    exit(1)

API_URL = "https://platform-api.max.ru"
HEADERS = {
    "Authorization": MAX_TOKEN,
    "Content-Type": "application/json"
}

last_marker = 0
bot_name = "Тестируем"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def ask_deepseek(user_message):
    """Запрос к DeepSeek API"""
    if not DEEPSEEK_KEY:
        log("❌ Ключ DeepSeek не настроен")
        return None
    
    log(f"🤔 Запрос к DeepSeek...")
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": user_message}],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data['choices'][0]['message']['content']
            log(f"✅ Ответ от DeepSeek получен")
            return reply
        else:
            log(f"❌ Ошибка DeepSeek: {response.status_code}")
            return None
            
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return None

def get_bot_info():
    try:
        r = requests.get(f"{API_URL}/me", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            log(f"✅ MAX: {data.get('first_name')} (@{data.get('username')})")
            return True
        else:
            log(f"❌ Ошибка MAX: {r.status_code}")
            return False
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False

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
                log(f"📌 Marker: {last_marker} -> {new_marker}")
                last_marker = new_marker
            
            return updates
        return []
    except Exception as e:
        log(f"⚠️ Ошибка: {e}")
        return []

def send_message(user_id, text):
    if not user_id or not text:
        return False
    
    url = f"{API_URL}/messages?user_id={user_id}"
    
    try:
        r = requests.post(url, headers=HEADERS, json={"text": text})
        return r.status_code == 200
    except:
        return False

def process_updates(updates):
    global processed_messages
    
    if not updates:
        return
    
    for update in updates:
        # Получаем ID сообщения для избежания дубликатов
        message_id = update.get('id')
        
        # Если уже обрабатывали это сообщение - пропускаем
        if message_id in processed_messages:
            continue
            
        if update.get('update_type') == 'message_created' and 'message' in update:
            msg = update['message']
            sender = msg.get('sender', {})
            user_id = sender.get('user_id')
            user_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
            body = msg.get('body', {})
            text = body.get('text', '')
            
            log(f"💬 {user_name}: '{text}'")
            
            if user_id and text:
                # Пробуем DeepSeek
                reply = ask_deepseek(text)
                
                # Если DeepSeek не ответил - используем стандартные фразы
                if not reply:
                    if 'привет' in text.lower():
                        reply = f"Привет, {user_name}! 👋"
                    elif 'как тебя зовут' in text.lower() or 'имя' in text.lower():
                        reply = f"Меня зовут {bot_name} 🤖"
                    elif 'пока' in text.lower() or 'до свидания' in text.lower():
                        reply = f"Пока, {user_name}! 👋"
                    else:
                        reply = f"Ты написал: '{text}'"
                
                # Отправляем ответ
                if send_message(user_id, reply):
                    log(f"✅ Ответ отправлен")
                    # Добавляем ID в обработанные
                    if message_id:
                        processed_messages.add(message_id)
                else:
                    log(f"❌ Ошибка отправки")
                    
        # Очищаем старые ID (чтобы set не рос бесконечно)
        if len(processed_messages) > 100:
            processed_messages = set(list(processed_messages)[-50:])

def main():
    print("\n" + "="*50)
    print("🤖 MAX БОТ + DeepSeek (исправленная версия)")
    print("="*50 + "\n")
    
    # Проверка подключения к MAX
    if not get_bot_info():
        log("❌ Не удалось подключиться к MAX")
        return
    
    # Проверка DeepSeek
    if DEEPSEEK_KEY:
        log(f"✅ DeepSeek ключ загружен")
        # Тестовый запрос к DeepSeek при запуске
        test_reply = ask_deepseek("Тест")
        if test_reply:
            log("✅ DeepSeek отвечает")
        else:
            log("⚠️ DeepSeek не отвечает, но бот будет работать со стандартными ответами")
    else:
        log("ℹ️ DeepSeek не настроен")
    
    log("\n🚀 Бот запущен! Отправь сообщение в MAX")
    log("⏹️ Для остановки нажми Ctrl+C\n")
    
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