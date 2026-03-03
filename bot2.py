import requests
import time
import json
import random
from datetime import datetime

# ===== ТОКЕНЫ =====
MAX_TOKEN = "f9LHodD0cOIlOQST64PdLJilm7jV31nVps-dm6HpLXYakYGm8TTfG3D6UPDqn7UQHYynY1GVvfK7iVeTudbE"
DEEPSEEK_KEY = "sk-3f344ee518824cbba12e65ef19dcf341"

# ===== YANDEX SEARCH API =====
YANDEX_API_KEY = "AQVNx0sMrAY0qmV9mq3BloWcmma2IjIzl4RQIzyi"
YANDEX_FOLDER_ID = "b1gjomt75m42u0apaf37"
YANDEX_SEARCH_URL = "https://search-api.cloud.yandex.net/v2/web/search"

API_URL = "https://platform-api.max.ru"
HEADERS = {"Authorization": MAX_TOKEN, "Content-Type": "application/json"}

last_marker = 0
user_conversations = {}
processed_messages = set()

SEARCH_KEYWORDS = ['погода', 'новости', 'курс', 'сегодня', 'сейчас', 
                   'последние', 'актуальные', 'новый', '2025', '2026', 'яндекс']

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def yandex_search(query):
    try:
        log(f"🔍 Поиск в Яндексе: '{query[:50]}...'")
        
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": {"searchQuery": query},
            "maxResultCount": 3,
            "folderId": YANDEX_FOLDER_ID
        }
        
        response = requests.post(YANDEX_SEARCH_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if 'webPages' in data and 'value' in data['webPages']:
                results = []
                for item in data['webPages']['value']:
                    title = item.get('name', '')
                    snippet = item.get('snippet', '')
                    url = item.get('url', '')
                    results.append(f"📌 **{title}**\n{snippet}\n🔗 {url}")
                return "\n\n".join(results)
            return None
        else:
            log(f"❌ Ошибка Yandex API: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Ошибка поиска: {e}")
        return None

def needs_search(query):
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in SEARCH_KEYWORDS)

def send_processing_message(user_id, search_mode=False):
    emojis = ["🧠", "🤔", "💭", "⚙️", "🔄", "⏳"]
    emoji = random.choice(emojis)
    
    if search_mode:
        messages = [
            f"{emoji} Ищу в Яндексе...",
            f"{emoji} Анализирую интернет...",
            f"{emoji} Проверяю актуальные источники...",
            f"{emoji} Собираю информацию..."
        ]
    else:
        messages = [
            f"{emoji} Думаю...",
            f"{emoji} Обрабатываю...",
            f"{emoji} Секундочку..."
        ]
    
    try:
        requests.post(f"{API_URL}/messages?user_id={user_id}", headers=HEADERS, json={"text": random.choice(messages)})
    except:
        pass

def ask_deepseek_with_search(user_id, user_message):
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    user_conversations[user_id].append({"role": "user", "content": user_message})
    
    if len(user_conversations[user_id]) > 10:
        user_conversations[user_id] = user_conversations[user_id][-10:]
    
    try:
        search_required = needs_search(user_message)
        send_processing_message(user_id, search_mode=search_required)
        
        if search_required:
            search_results = yandex_search(user_message)
            if search_results:
                prompt = f"""На основе найденной в интернете информации ответь на вопрос.

Вопрос: {user_message}

Результаты поиска:
{search_results}

Дай точный ответ, укажи источники."""
                
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4000
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data['choices'][0]['message']['content']
                    user_conversations[user_id].append({"role": "assistant", "content": reply})
                    return reply
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": user_conversations[user_id],
                "max_tokens": 4000
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data['choices'][0]['message']['content']
            user_conversations[user_id].append({"role": "assistant", "content": reply})
            return reply
        return None
    except Exception as e:
        log(f"❌ Ошибка: {e}")
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
    except:
        pass
    return []

def send_message(user_id, text):
    try:
        r = requests.post(f"{API_URL}/messages?user_id={user_id}", headers=HEADERS, json={"text": text})
        return r.status_code == 200
    except:
        return False

def has_voice_attachment(body):
    attachments = body.get('attachments', [])
    for att in attachments:
        if att.get('type') == 'audio_message':
            return True
    return False

def main():
    global processed_messages
    
    print("\n" + "="*70)
    print("🤖 MAX БОТ + DeepSeek + Яндекс Поиск")
    print("="*70)
    
    # Проверка MAX
    try:
        r = requests.get(f"{API_URL}/me", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ MAX: {data.get('first_name')}")
    except Exception as e:
        print(f"❌ Ошибка MAX: {e}")
        return
    
    print("\n🚀 Бот запущен локально!")
    print("📱 Отправляй сообщения в MAX\n")
    
    msg_count = 0
    
    try:
        while True:
            updates = get_updates()
            for update in updates:
                msg_id = update.get('id')
                if msg_id and msg_id in processed_messages:
                    continue
                
                if 'message' in update:
                    msg = update['message']
                    user_id = msg.get('sender', {}).get('user_id')
                    body = msg.get('body', {})
                    text = body.get('text', '')
                    
                    if user_id:
                        msg_count += 1
                        
                        if has_voice_attachment(body):
                            log(f"🎤 [{msg_count}] Голосовое от {user_id}")
                            send_message(user_id, "📢 Я пока отвечаю только на текст")
                            processed_messages.add(msg_id)
                            continue
                        
                        if text:
                            log(f"💬 [{msg_count}] '{text[:50]}...'")
                            reply = ask_deepseek_with_search(user_id, text)
                            
                            if reply:
                                send_message(user_id, reply)
                                log(f"✅ Ответ отправлен")
                                processed_messages.add(msg_id)
                            else:
                                if 'привет' in text.lower():
                                    send_message(user_id, "Привет! 👋")
                                else:
                                    send_message(user_id, f"Ты написал: '{text}'")
                                processed_messages.add(msg_id)
            
            if len(processed_messages) > 1000:
                processed_messages = set(list(processed_messages)[-500:])
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n👋 Бот остановлен. Сообщений: {msg_count}")

if __name__ == "__main__":
    main()