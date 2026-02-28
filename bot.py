import requests
import time
import json
from datetime import datetime

# ===== ТОКЕНЫ =====
MAX_TOKEN = "f9LHodD0cOIlOQST64PdLJilm7jV31nVps-dm6HpLXYakYGm8TTfG3D6UPDqn7UQHYynY1GVvfK7iVeTudbE"
DEEPSEEK_KEY = "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"

API_URL = "https://platform-api.max.ru"
HEADERS = {
    "Authorization": MAX_TOKEN,
    "Content-Type": "application/json"
}

last_marker = 0
processed_ids = set()  # для отслеживания обработанных сообщений

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_deepseek():
    """Тест подключения к DeepSeek при запуске"""
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Привет"}]
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def ask_deepseek(user_message):
    """Запрос к DeepSeek"""
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
                "max_tokens": 300
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            log(f"DeepSeek ошибка: {response.status_code}")
            return None
    except Exception as e:
        log(f"DeepSeek исключение: {e}")
        return None

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
        return []
    except:
        return []

def send_message(user_id, text):
    try:
        r = requests.post(f"{API_URL}/messages?user_id={user_id}", headers=HEADERS, json={"text": text})
        return r.status_code == 200
    except:
        return False

def main():
    print("\n" + "="*50)
    print("🤖 MAX БОТ ЗАПУЩЕН")
    print("="*50)
    
    # Проверка подключения к MAX
    try:
        r = requests.get(f"{API_URL}/me", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ MAX: {data.get('first_name')}")
        else:
            print(f"❌ Ошибка MAX: {r.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Проверка DeepSeek
    if DEEPSEEK_KEY and test_deepseek():
        print("✅ DeepSeek: работает")
        use_deepseek = True
    else:
        print("⚠️ DeepSeek: не работает (будут стандартные ответы)")
        use_deepseek = False
    
    print("\n🚀 Бот слушает сообщения...\n")
    
    while True:
        try:
            updates = get_updates()
            for update in updates:
                # Пропускаем уже обработанные
                if update.get('id') in processed_ids:
                    continue
                
                if 'message' in update:
                    msg = update['message']
                    user_id = msg.get('sender', {}).get('user_id')
                    text = msg.get('body', {}).get('text', '')
                    
                    if user_id and text:
                        # Логируем
                        print(f"\n📩 Получено: '{text}'")
                        
                        # Получаем ответ
                        reply = None
                        if use_deepseek:
                            reply = ask_deepseek(text)
                        
                        # Если DeepSeek не ответил
                        if not reply:
                            if 'привет' in text.lower():
                                reply = f"Привет! 👋"
                            elif 'как тебя зовут' in text.lower():
                                reply = f"Меня зовут Тестируем 🤖"
                            else:
                                reply = f"Ты написал: '{text}'"
                        
                        # Отправляем
                        if send_message(user_id, reply):
                            print(f"✅ Ответ: '{reply[:50]}...'")
                            processed_ids.add(update.get('id'))
                        else:
                            print(f"❌ Ошибка отправки")
            
            # Очистка старых ID (чтобы не копить)
            if len(processed_ids) > 1000:
                processed_ids = set(list(processed_ids)[-500:])
                
        except Exception as e:
            print(f"⚠️ Ошибка в цикле: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    main()