import os
import requests
import time
import json
from datetime import datetime

TOKEN = os.environ.get("MAX_BOT_TOKEN")
if not TOKEN:
    print("❌ Ошибка: нет токена")
    exit(1)

API_URL = "https://platform-api.max.ru"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}
last_marker = 0

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

def send_message(user_id, text):
    if not user_id:
        return False
    try:
        r = requests.post(f"{API_URL}/messages?user_id={user_id}", 
                          headers=HEADERS, 
                          json={"text": text})
        return r.status_code == 200
    except:
        return False

def main():
    log("🚀 Бот запущен")
    while True:
        updates = get_updates()
        if updates:
            for update in updates:
                if 'message' in update:
                    msg = update['message']
                    user_id = msg.get('sender', {}).get('user_id')
                    text = msg.get('body', {}).get('text', '')
                    if user_id and text:
                        send_message(user_id, f"Привет! Ты написал: {text}")
        time.sleep(1)

if __name__ == "__main__":
    main()