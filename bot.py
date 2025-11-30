import requests, jdatetime, time, re
from datetime import datetime
import telebot
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Get token and channel from .env
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not TOKEN or not CHANNEL_ID:
    print("[ERROR] Please check your .env file! Make sure TELEGRAM_TOKEN and CHANNEL_ID are set.")
    exit()

bot = telebot.TeleBot(TOKEN)

iran_tz = pytz.timezone('Asia/Tehran')
def now_iran():
    return datetime.now(iran_tz)

def get_persian_date_time():
    now = jdatetime.datetime.now()
    time_iran = now_iran().strftime("%H:%M")
    return now.strftime("%Y/%m/%d"), time_iran

def format_price(num):
    return f"{num:,}".replace(",", "٬")

def fetch_fiat_currencies():
    print(f"[{now_iran().strftime('%H:%M:%S')}] [FIAT] Fetching currencies from tgju.org...")
    try:
        response = requests.get("https://www.tgju.org/currency", headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="data-table market-table market-section-right active")
        if not table:
            print(f"[{now_iran().strftime('%H:%M:%S')}] [FIAT] ERROR: Table not found!")
            return None

        rows = table.find("tbody").find_all("tr")
        results = {}
        date_p, time_p = get_persian_date_time()

        for row in rows:
            th = row.find("th")
            if not th: continue
            text = th.get_text(strip=True)
            clean_text = re.sub(r"[\s\u200C\u200D\u202F]", "", text)

            price_cell = row.find("td", class_="nf")
            if not price_cell: continue
            price = int("".join(filter(str.isdigit, price_cell.get_text())))

            if clean_text == "دلار":
                code = "USD"
            elif "یورو" in text:
                code = "EUR"
            elif "پوند" in text:
                code = "GBP"
            elif "کانادا" in clean_text:
                code = "CAD"
            elif "یوان" in text or "چین" in text:
                code = "CNY"
            elif "لیر" in text or "ترکیه" in text:
                code = "TRY"
            else:
                continue

            if code not in results:
                results[code] = {"date": date_p, "time": time_p, "price": price}
                print(f"[{now_iran().strftime('%H:%M:%S')}] [FIAT] Found {code}: {format_price(price)} IRR")

        required = ["USD", "EUR", "GBP", "CAD", "CNY", "TRY"]
        if all(c in results for c in required):
            print(f"[{now_iran().strftime('%H:%M:%S')}] [FIAT] SUCCESS: All 6 currencies fetched!")
            return results
        else:
            missing = [c for c in required if c not in results]
            print(f"[{now_iran().strftime('%H:%M:%S')}] [FIAT] Missing: {missing}")
            return None

    except Exception as e:
        print(f"[{now_iran().strftime('%H:%M:%S')}] [FIAT] EXCEPTION: {e}")
        return None

def fetch_crypto():
    try:
        data = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=15).json()
        btc = round(float(data["bitcoin"]["usd"]), 2)
        eth = round(float(data["ethereum"]["usd"]), 2)
        print(f"[{now_iran().strftime('%H:%M:%S')}] [CRYPTO] Bitcoin: ${format_price(int(btc))} | Ethereum: ${format_price(int(eth))}")
        d, t = get_persian_date_time()
        return {"BTC": {"price": btc, "date": d, "time": t}, "ETH": {"price": eth, "date": d, "time": t}}
    except Exception as e:
        print(f"[{now_iran().strftime('%H:%M:%S')}] [CRYPTO] FAILED: {e}")
        return None

def send_price_message():
    print(f"[{now_iran().strftime('%H:%M:%S')}] [SEND] Building message...")
    fiat = fetch_fiat_currencies()
    crypto = fetch_crypto()
    if not fiat or not crypto:
        print(f"[{now_iran().strftime('%H:%M:%S')}] [SEND] FAILED: Incomplete data")
        return False

    msg = f"""قیمت لحظه‌ای بازار — بروزرسانی خودکار
صرافی استانبول
بامجوز رسمی بانک مرکزی

دلار آمریکا : {format_price(fiat['USD']['price'])} ریال
یورو : {format_price(fiat['EUR']['price'])} ريال
پوند انگلیس : {format_price(fiat['GBP']['price'])} ريال
دلار کانادا : {format_price(fiat['CAD']['price'])} ريال
یوان چین : {format_price(fiat['CNY']['price'])} ريال
لیر ترکیه : {format_price(fiat['TRY']['price'])} ريال

بیت‌کوین : {format_price(int(crypto['BTC']['price']))} دلار
اتریوم : {format_price(int(crypto['ETH']['price']))} دلار

آخرین بروزرسانی: {fiat['USD']['date']} — {fiat['USD']['time']}

کانال رسمی: @istanbuI_exchange"""

    try:
        bot.send_message(CHANNEL_ID, msg, disable_web_page_preview=True)
        print(f"[{now_iran().strftime('%H:%M:%S')}] [SEND] SUCCESS: Message sent to channel!")
        return True
    except Exception as e:
        print(f"[{now_iran().strftime('%H:%M:%S')}] [SEND] TELEGRAM ERROR: {e}")
        return False

def main():
    print("="*90)
    print("           TELEGRAM LIVE PRICE BOT — FINAL SECURE VERSION")
    print("               Settings loaded from .env file")
    print("        First run = instant update | Then every 30 min (11 AM - 11 PM)")
    print("="*90)

    # Welcome message
    try:
        bot.send_message(CHANNEL_ID, "Bot activated successfully!\nFetching first price update...")
        print(f"[{now_iran().strftime('%H:%M:%S')}] [SYSTEM] Welcome message sent")
    except Exception as e:
        print(f"[{now_iran().strftime('%H:%M:%S')}] [SYSTEM] Welcome failed: {e}")

    # First update — keep trying until success
    attempt = 0
    while True:
        attempt += 1
        print(f"\n[{now_iran().strftime('%H:%M:%S')}] [SYSTEM] First update attempt #{attempt}")
        if send_price_message():
            print(f"[{now_iran().strftime('%H:%M:%S')}] [SYSTEM] FIRST UPDATE SUCCESSFUL! Bot is running smoothly.")
            break
        print(f"[{now_iran().strftime('%H:%M:%S')}] [SYSTEM] Failed — retrying in 30 seconds...")
        time.sleep(30)

    while True:
        hour = now_iran().hour
        if 11 <= hour < 23:
            print(f"[{now_iran().strftime('%H:%M:%S')}] [LOOP] Working hours — next update in 30 minutes")
            time.sleep(1800)
            send_price_message()
        else:
            print(f"[{now_iran().strftime('%H:%M:%S')}] [LOOP] Outside working hours — sleeping until 11 AM")
            time.sleep(300)

if __name__ == "__main__":
    main()
