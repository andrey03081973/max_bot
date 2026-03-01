import requests
import time
import json
from datetime import datetime

# ===== ТОКЕНЫ =====
MAX_TOKEN = "f9LHodD0cOIlOQST64PdLJilm7jV31nVps-dm6HpLXYakYGm8TTfG3D6UPDqn7UQHYynY1GVvfK7iVeTudbE"
DEEPSEEK_KEY = "sk-3f344ee518824cbba12e65ef19dcf341"

API_URL = "https://platform-api.max.ru"
HEADERS = {
    "Authorization": MAX_TOKEN,
    "Content-Type": "application/json"
}

last_marker = 0

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

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
                "messages": [{"role": "user", "content": user_message}]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except:
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
    print("🤖 MAX БОТ")
    print("="*50)
    
    # Проверка MAX
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
    
    print("\n🚀 Бот запущен! Отправь сообщение в MAX\n")
    
    # Простое множество для ID
    processed = set()
    
    try:
        while True:
            updates = get_updates()
            
            for update in updates:
                # Получаем ID
                msg_id = update.get('id')
                
                # Пропускаем, если уже обработали
                if msg_id and msg_id in processed:
                    continue
                
                # Обрабатываем сообщение
                if 'message' in update:
                    msg = update['message']
                    user_id = msg.get('sender', {}).get('user_id')
                    text = msg.get('body', {}).get('text', '')
                    
                    if user_id and text:
                        log(f"📩 Получено: '{text}'")
                        
                        # Пробуем DeepSeek
                        reply = ask_deepseek(text)
                        
                        # Если DeepSeek не сработал
                        if not reply:
                            if 'привет' in text.lower():
                                reply = "Привет! 👋"
                            elif 'как тебя зовут' in text.lower():
                                reply = "Меня зовут Тестируем 🤖"
                            else:
                                reply = f"Ты написал: '{text}'"
                        
                        # Отправляем
                        if send_message(user_id, reply):
                            log(f"✅ Ответ: '{reply[:30]}...'")
                            if msg_id:
                                processed.add(msg_id)
                
                # Очистка (чтобы не занимало много памяти)
                if len(processed) > 100:
                    processed.clear()
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()