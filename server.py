from flask import Flask
import threading
import schedule
import time
import subprocess

app = Flask(__name__)


def run_scraper():
    print("Running scraper...")
    subprocess.run(["python", "src/scraper.py", "--notify"])


def schedule_runner():
    schedule.every().day.at("08:00").do(run_scraper)
    while True:
        schedule.run_pending()
        time.sleep(30)


@app.route("/")
def status():
    return "Cardi-sale scraper scheduler is running."


if __name__ == "__main__":
    threading.Thread(target=schedule_runner, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
