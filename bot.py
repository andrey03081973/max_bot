import os
import requests
import time
import json
from datetime import datetime

# ===== ТОКЕН MAX (ВСТАВЬТЕ ВАШ СЮДА) =====
MAX_TOKEN = "f9LHodD0cOJ2k-bGWVTScflDCCHuYBKvU-T6Y1kgAs07gopFMEm87XOOIuffKERJ-pWGIOkusGWlpoj76lW4"

# ===== КЛЮЧ DeepSeek (если есть) =====
DEEPSEEK_KEY = "sk-1cd90d7386224b6e814d155b1442cf52"  # пока оставьте так, если нет ключа

if not MAX_TOKEN:
    print("❌ Ошибка: не указан токен MAX")
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
    """Запрос к DeepSeek"""
    if not DEEPSEEK_KEY or DEEPSEEK_KEY == "ваш_ключ_deepseek_сюда":
        return None
    
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
            return data['choices'][0]['message']['content']
    except Exception as e:
        log(f"⚠️ Ошибка DeepSeek: {e}")
    
    return None

def get_bot_info():
    """Проверка подключения к MAX"""
    try:
        r = requests.get(f"{API_URL}/me", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            log(f"✅ MAX: {data.get('first_name')} (@{data.get('username')})")
            return True
        else:
            log(f"❌ Ошибка подключения к MAX: {r.status_code}")
            return False
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False

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
            return True
        else:
            log(f"❌ Ошибка отправки: {r.status_code}")
            return False
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False

def process_updates(updates):
    """Обработка входящих сообщений"""
    if not updates:
        return
    
    for update in updates:
        if update.get('update_type') == 'message_created' and 'message' in update:
            msg = update['message']
            
            sender = msg.get('sender', {})
            user_id = sender.get('user_id')
            user_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
            
            body = msg.get('body', {})
            text = body.get('text', '')
            
            log(f"💬 От {user_name}: '{text}'")
            
            if user_id and text:
                # Сначала пробуем DeepSeek
                reply = ask_deepseek(text)
                
                # Если DeepSeek не ответил - используем стандартные фразы
                if not reply:
                    if 'привет' in text.lower():
                        reply = f"Привет, {user_name}! 👋"
                    elif 'как тебя зовут' in text.lower():
                        reply = f"Меня зовут {bot_name} 🤖"
                    elif 'пока' in text.lower():
                        reply = f"Пока, {user_name}! 👋"
                    else:
                        reply = f"Ты написал: '{text}'"
                
                if send_message(user_id, reply):
                    log(f"✅ Ответ отправлен")
                else:
                    log(f"❌ Не удалось отправить ответ")

def main():
    print("\n" + "="*50)
    print("🤖 MAX БОТ + DeepSeek AI")
    print("="*50 + "\n")
    
    # Проверяем подключение к MAX
    if not get_bot_info():
        log("❌ Не удалось подключиться к MAX")
        log("🔧 Проверьте токен в коде")
        return
    
    # Информация о DeepSeek
    if DEEPSEEK_KEY and DEEPSEEK_KEY != "ваш_ключ_deepseek_сюда":
        log("✅ DeepSeek подключен")
    else:
        log("ℹ️ DeepSeek не настроен (бот отвечает стандартно)")
    
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