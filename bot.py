import os
import time
import requests
import subprocess
import zipfile

BOT_TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

DOWNLOAD_DIR = "downloads"
OFFSET_FILE = "offset.txt"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_offset():
    if not os.path.exists(OFFSET_FILE):
        return 0
    return int(open(OFFSET_FILE).read().strip())


def save_offset(offset):
    open(OFFSET_FILE, "w").write(str(offset))


def send_message(chat, text):
    requests.post(API + "/sendMessage", json={
        "chat_id": chat,
        "text": text
    })


def send_file(chat, path):
    with open(path, "rb") as f:
        requests.post(
            API + "/sendDocument",
            data={"chat_id": chat},
            files={"document": f}
        )


def download_playlist(url):

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


def zip_files():

    zipname = "playlist.zip"

    with zipfile.ZipFile(zipname, "w") as zipf:
        for f in os.listdir(DOWNLOAD_DIR):
            path = os.path.join(DOWNLOAD_DIR, f)
            zipf.write(path, f)

    return zipname


def check_messages():

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

            send_message(chat,
            "🎵 Send Spotify playlist or track link")

        elif "spotify.com" in text:

            send_message(chat, "⚡ Downloading playlist...")

            download_playlist(text)

            send_message(chat, "📦 Creating ZIP...")

            zipname = zip_files()

            send_file(chat, zipname)

            send_message(chat, "✅ Finished")

    save_offset(offset)


if __name__ == "__main__":

    start = time.time()

    # run bot for 4 minutes
    while time.time() - start < 240:

        try:
            check_messages()
        except Exception as e:
            print(e)

        time.sleep(5)
