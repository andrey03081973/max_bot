import os
import requests
import time
import json
from datetime import datetime

# ===== ТОКЕНЫ =====
MAX_TOKEN = os.environ.get("MAX_BOT_TOKEN")
# ВСТАВЬТЕ ВАШ КЛЮЧ DeepSeek СЮДА (в кавычки)
DEEPSEEK_KEY = "sk-1cd90d7386224b6e814d155b1442cf52"

if not MAX_TOKEN:
    print("❌ Ошибка: нет MAX_BOT_TOKEN")
    exit(1)

API_URL = "https://platform-api.max.ru"
HEADERS = {
    "Authorization": MAX_TOKEN,
    "Content-Type": "application/json"
}

last_marker = 0
bot_name = "Тестируем"

def log(msg):
    """Красивое логирование"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def ask_deepseek(user_message):
    """
    Отправляет запрос в DeepSeek и возвращает ответ
    """
    if not DEEPSEEK_KEY:
        log("❌ Нет ключа DeepSeek")
        return None
    
    try:
        log(f"🤔 Запрос в DeepSeek: '{user_message[:50]}...'")
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты полезный ассистент. Отвечай кратко и по делу."},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data['choices'][0]['message']['content']
            log(f"✅ Ответ получен от DeepSeek")
            return reply
        else:
            log(f"❌ Ошибка DeepSeek: {response.status_code}")
            log(f"   {response.text}")
            return None
            
    except Exception as e:
        log(f"❌ Ошибка при запросе к DeepSeek: {e}")
        return None

def get_bot_info():
    """Проверка подключения к MAX"""
    try:
        r = requests.get(f"{API_URL}/me", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            log(f"✅ MAX: {data.get('first_name')} (@{data.get('username')})")
            return data
    except Exception as e:
        log(f"❌ Ошибка: {e}")
    return None

def get_updates():
    """Получение новых сообщений"""
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
        elif r.status_code == 204:
            return []
        else:
            log(f"⚠️ Ошибка получения обновлений: {r.status_code}")
            return []
    except Exception as e:
        log(f"⚠️ Ошибка: {e}")
        return []

def send_message(user_id, text):
    """Отправка сообщения в MAX"""
    if not user_id or not text:
        return False
    
    url = f"{API_URL}/messages?user_id={user_id}"
    
    try:
        r = requests.post(url, headers=HEADERS, json={"text": text})
        if r.status_code == 200:
            log(f"✅ Сообщение отправлено")
            return True
        else:
            log(f"❌ Ошибка отправки: {r.status_code}")
            log(f"   {r.text}")
            return False
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False

def process_updates(updates):
    """Обработка входящих сообщений"""
    if not updates:
        return
    
    # Диагностика ключа DeepSeek
    if DEEPSEEK_KEY:
        log(f"🔑 DeepSeek ключ: {DEEPSEEK_KEY[:10]}...")
    else:
        log("❌ DeepSeek ключ не найден")
    
    for update in updates:
        if update.get('update_type') == 'message_created' and 'message' in update:
            msg = update['message']
            
            # Данные отправителя
            sender = msg.get('sender', {})
            user_id = sender.get('user_id')
            user_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
            
            # Текст сообщения
            body = msg.get('body', {})
            text = body.get('text', '')
            
            log(f"💬 От {user_name}: '{text}'")
            
            if user_id and text:
                # Пробуем получить ответ от DeepSeek
                reply = None
                
                if DEEPSEEK_KEY:
                    reply = ask_deepseek(text)
                    if reply:
                        log("✅ Использую ответ DeepSeek")
                
                # Если DeepSeek не ответил - используем простые ответы
                if not reply:
                    log("ℹ️ Использую стандартный ответ")
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
                else:
                    log(f"❌ Не удалось отправить ответ")

def main():
    print("\n" + "="*50)
    print("🤖 MAX БОТ + DeepSeek AI")
    print("="*50 + "\n")
    
    # Проверяем MAX
    if not get_bot_info():
        log("❌ Не удалось подключиться к MAX")
        return
    
    # Проверяем DeepSeek
    if DEEPSEEK_KEY:
        log("✅ DeepSeek ключ загружен")
        # Проверим, что ключ не пустой
        if len(DEEPSEEK_KEY) < 10:
            log("⚠️ Ключ DeepSeek выглядит подозрительно коротким")
    else:
        log("ℹ️ DeepSeek не настроен (бот будет отвечать стандартно)")
    
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