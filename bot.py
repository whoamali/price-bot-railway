import requests, jdatetime, time, re
from datetime import datetime
import telebot
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import pytz

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not TOKEN or not CHANNEL_ID:
    print("[ERROR] Please check your .env file! Make sure TELEGRAM_TOKEN and CHANNEL_ID are set.")
    exit()

bot = telebot.TeleBot(TOKEN)

IRAN_TZ = pytz.timezone('Asia/Tehran')

def get_persian_date_time():
    now_iran = datetime.now(IRAN_TZ)
    jdate = jdatetime.datetime.fromgregorian(datetime=now_iran)
    return jdate.strftime("%Y/%m/%d"), now_iran.strftime("%H:%M")

def format_price(num):
    return f"{num:,}".replace(",", "٬")

def send_price_message():
    print(f"[{datetime.now(IRAN_TZ).strftime('%H:%M:%S')}] [SEND] Building message...")
    fiat = fetch_fiat_currencies()
    crypto = fetch_crypto()
    if not fiat or not crypto:
        print(f"[{datetime.now(IRAN_TZ).strftime('%H:%M:%S')}] [SEND] FAILED: Incomplete data")
        return False

    update_time_iran = datetime.now(IRAN_TZ).strftime("%H:%M")

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

آخرین بروزرسانی: {fiat['USD']['date']} — {update_time_iran} (به وقت تهران)

کانال رسمی: @istanbuI_exchange"""

    try:
        bot.send_message(CHANNEL_ID, msg, disable_web_page_preview=True)
        print(f"[{datetime.now(IRAN_TZ).strftime('%H:%M:%S')}] [SEND] SUCCESS: Message sent!")
        return True
    except Exception as e:
        print(f"[{datetime.now(IRAN_TZ).strftime('%H:%M:%S')}] [SEND] TELEGRAM ERROR: {e}")
        return False

def main():
    try:
        bot.send_message(CHANNEL_ID, "ربات با موفقیت فعال شد!\nدر حال دریافت اولین بروزرسانی...")
    except Exception as e:
        print(f"[SYSTEM] Welcome failed: {e}")

    while True:
        if send_price_message():
            print(f"[{datetime.now(IRAN_TZ).strftime('%H:%M:%S')}] اولین بروزرسانی با موفقیت ارسال شد!")
            break
        time.sleep(30)

    while True:
        hour_iran = datetime.now(IRAN_TZ).hour
        if 11 <= hour_iran < 23:
            print(f"[{datetime.now(IRAN_TZ).strftime('%H:%M:%S')}] ساعت کاری — خواب ۳۰ دقیقه")
            time.sleep(1800)
            send_price_message()
        else:
            next_wake = datetime.now(IRAN_TZ).replace(hour=11, minute=0, second=0, microsecond=0)
            if next_wake < datetime.now(IRAN_TZ):
                next_wake = next_wake.replace(day=next_wake.day + 1)
            sleep_seconds = (next_wake - datetime.now(IRAN_TZ)).total_seconds()
            print(f"[{datetime.now(IRAN_TZ).strftime('%H:%M:%S')}] خارج از ساعت کاری — خواب تا ساعت ۱۱ صبح ({sleep_seconds/3600:.1f} ساعت)")
            time.sleep(int(sleep_seconds))

if __name__ == "__main__":
    main()
