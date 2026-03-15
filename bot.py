import os
import time
import requests
import subprocess

BOT_TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

DOWNLOAD_DIR = "downloads"
OFFSET_FILE = "offset.txt"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_offset():
    if not os.path.exists(OFFSET_FILE):
        return 0
    return int(open(OFFSET_FILE).read())


def save_offset(offset):
    open(OFFSET_FILE, "w").write(str(offset))


def send_message(chat, text):

    r = requests.post(API + "/sendMessage", json={
        "chat_id": chat,
        "text": text
    })

    return r.json()["result"]["message_id"]


def edit_message(chat, msg_id, text):

    requests.post(API + "/editMessageText", json={
        "chat_id": chat,
        "message_id": msg_id,
        "text": text
    })


def send_audio(chat, path):

    with open(path, "rb") as f:

        requests.post(
            API + "/sendAudio",
            data={"chat_id": chat},
            files={"audio": f}
        )


def download_spotify(url):

    subprocess.run([
        "spotdl",
        url,
        "--cookie-file",
        "cookies.txt",
        "--threads",
        "4",
        "--output",
        f"{DOWNLOAD_DIR}/{{artist}} - {{title}}.mp3"
    ])


def check_updates():

    offset = get_offset()

    r = requests.get(API + "/getUpdates", params={"offset": offset})
    updates = r.json()["result"]

    for u in updates:

        offset = u["update_id"] + 1

        if "message" not in u:
            continue

        msg = u["message"]
        chat = msg["chat"]["id"]
        text = msg.get("text", "")

        if text.startswith("/start"):

            send_message(chat,"🎵 Send Spotify link")

        elif "spotify.com" in text:

            msg_id = send_message(chat,"⏳ Starting download...")

            edit_message(chat,msg_id,"⬇️ Downloading music...")

            download_spotify(text)

            files = os.listdir(DOWNLOAD_DIR)

            total = len(files)
            count = 0

            for f in files:

                path = os.path.join(DOWNLOAD_DIR,f)

                edit_message(chat,msg_id,
                f"📤 Uploading {count+1}/{total}")

                send_audio(chat,path)

                os.remove(path)

                count += 1

            edit_message(chat,msg_id,"✅ Finished")

    save_offset(offset)


if __name__ == "__main__":

    start = time.time()

    while time.time() - start < 240:

        try:
            check_updates()
        except Exception as e:
            print(e)

        time.sleep(5)
