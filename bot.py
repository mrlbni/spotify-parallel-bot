import os
import requests
import subprocess
import zipfile
import shutil

BOT_TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

OFFSET_FILE = "offset.txt"
DOWNLOAD_DIR = "downloads"
ZIP_FILE = "playlist.zip"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_offset():
    if not os.path.exists(OFFSET_FILE):
        return 0
    return int(open(OFFSET_FILE).read().strip())


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))


def send_message(chat_id, text):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


def send_zip(chat_id, path):
    with open(path, "rb") as f:
        requests.post(
            f"{API}/sendDocument",
            data={"chat_id": chat_id},
            files={"document": f}
        )


def download_playlist(url):

    cmd = [
        "spotdl",
        url,
        "--cookie-file",
        "cookies.txt",
        "--threads",
        "6",
        "--output",
        f"{DOWNLOAD_DIR}/{{artist}} - {{title}}.mp3"
    ]

    subprocess.run(cmd)


def zip_playlist():

    with zipfile.ZipFile(ZIP_FILE, "w") as zipf:

        for file in os.listdir(DOWNLOAD_DIR):

            path = os.path.join(DOWNLOAD_DIR, file)

            zipf.write(path, file)

    shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)


def process_updates():

    offset = get_offset()

    r = requests.get(f"{API}/getUpdates?offset={offset}")
    updates = r.json()["result"]

    for u in updates:

        offset = u["update_id"] + 1

        if "message" not in u:
            continue

        msg = u["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if text.startswith("/start"):

            send_message(chat_id,
                "🎵 Send Spotify playlist or track link")

        elif "spotify.com" in text:

            send_message(chat_id,
                "⚡ Downloading playlist (parallel mode)...")

            try:

                download_playlist(text)

                send_message(chat_id,"📦 Creating ZIP...")

                zip_playlist()

                send_zip(chat_id, ZIP_FILE)

                os.remove(ZIP_FILE)

                send_message(chat_id,"✅ Done")

            except Exception as e:

                send_message(chat_id,f"❌ Error: {e}")

    save_offset(offset)


if __name__ == "__main__":
    process_updates()
