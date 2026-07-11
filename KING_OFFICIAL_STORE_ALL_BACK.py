#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KING OFFICIAL STORE BOT
Python 3.10+
Library: pyTelegramBotAPI

Before running:
1) Put your Telegram bot token in BOT_TOKEN.
2) Put both owner Telegram numeric IDs in OWNER_ADMINS.
3) Install: pip install pyTelegramBotAPI
4) Run: python main.py
"""

import html
import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional

import telebot
from telebot import types

# =========================
# REQUIRED CONFIGURATION
# =========================

BOT_TOKEN = os.getenv("8521569602:AAGrCIgramrwypPaT3FYJxvS5RQczY_Irnw")
OWNER_ADMINS = {
    int(x.strip())
    for x in os.getenv("OWNER_ADMINS", "8756340925,8263525850").split(",")
    if x.strip().isdigit()
}

STORE_NAME = "KING Official Store"
PRODUCT_NAME = "BOSS MODZ"
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@KINGSELLERTOP")

# ImgBB direct image URL resolved from:
# https://ibb.co/RGVBp14M
BANNER_URL = os.getenv(
    "BANNER_URL",
    "https://i.ibb.co/kVW9gp6r/file-00000000d2147206be19593dc993f607.png",
)

DB_PATH = os.getenv("DB_PATH", "king_official_store.db")

if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN":
    raise RuntimeError("Please set BOT_TOKEN in main.py or as an environment variable.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
db_lock = threading.RLock()


# =========================
# DATABASE
# =========================

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


db = connect()

PLANS = {
    "1d": {"name": "1 Day", "price": 50},
    "3d": {"name": "3 Days", "price": 150},
    "7d": {"name": "7 Days", "price": 210},
    "15d": {"name": "15 Days", "price": 350},
    "30d": {"name": "30 Days", "price": 630},
}

DEFAULT_TEXTS = {
    "welcome": (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👋 Hi, Welcome to KING!\n\n"
        "😊 {first_name}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 Wallet Balance : ₹{balance}\n"
        "👤 Account Type : {account_type}\n"
        "📦 Total Orders : {total_orders}\n"
        "🎁 Referral Rewards : {referral_rewards}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━"
    ),
    "select_product": (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📦 SELECT PRODUCT\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Choose the product you want to purchase.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━"
    ),
    "select_duration": (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ SELECT DURATION\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please choose your preferred subscription duration.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━"
    ),
    "wallet": (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💰 MY WALLET\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🪙 Current Balance : ₹{balance}\n"
        "➕ Total Deposits : ₹{total_deposits}\n"
        "🛒 Total Spent : ₹{total_spent}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━"
    ),
    "account": (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👤 MY ACCOUNT\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "😊 Name : {first_name}\n"
        "🪪 User ID : <code>{user_id}</code>\n"
        "👤 Account Type : {account_type}\n"
        "💰 Wallet Balance : ₹{balance}\n"
        "📦 Total Orders : {total_orders}\n"
        "👥 Total Referrals : {referral_count}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━"
    ),
    "support": (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📞 SUPPORT CENTER\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Contact our official support:\n"
        "{support_username}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━"
    ),
}

DEFAULT_BUTTONS = {
    "buy": "🛒 Buy",
    "deposit": "💳 Deposit",
    "wallet": "💰 My Wallet",
    "orders": "📦 My Orders",
    "account": "👤 My Account",
    "referral": "🎁 Referral",
    "reseller": "💎 Become Reseller",
    "support": "📞 Support",
    "information": "ℹ️ Information",
    "admin": "👑 Admin Panel",
}


def init_db():
    with db_lock:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT 'User',
                balance INTEGER DEFAULT 0,
                account_type TEXT DEFAULT 'Customer',
                referral_count INTEGER DEFAULT 0,
                referral_rewards INTEGER DEFAULT 0,
                referred_by INTEGER,
                total_deposits INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                joined_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS keys_stock(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                duration TEXT NOT NULL,
                key_value TEXT UNIQUE NOT NULL,
                used INTEGER DEFAULT 0,
                used_by INTEGER,
                used_at TEXT
            );

            CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                duration TEXT NOT NULL,
                base_price INTEGER NOT NULL,
                discount_percent INTEGER DEFAULT 0,
                final_price INTEGER NOT NULL,
                key_value TEXT NOT NULL,
                status TEXT DEFAULT 'Completed',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deposits(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                proof TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS texts(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS buttons(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS admin_logs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        for key, value in DEFAULT_TEXTS.items():
            db.execute("INSERT OR IGNORE INTO texts(key,value) VALUES(?,?)", (key, value))

        for key, value in DEFAULT_BUTTONS.items():
            db.execute("INSERT OR IGNORE INTO buttons(key,value) VALUES(?,?)", (key, value))

        defaults = {
            "referral_target": "15",
            "referral_reward_duration": "1d",
            "reseller_discount": "10",
            "button_color": "#22C55E",
            "information_text": (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "ℹ️ INFORMATION\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Welcome to KING Official Store.\n"
                "Fast digital delivery and reliable customer support.\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🏆 KING Official Store\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
        }
        for key, value in defaults.items():
            db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value))
        db.commit()


# =========================
# HELPERS
# =========================

def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def is_admin(user_id: int) -> bool:
    return user_id in OWNER_ADMINS


def notify_admins(text: str):
    for admin_id in OWNER_ADMINS:
        try:
            bot.send_message(admin_id, text)
        except Exception:
            pass


def log_admin(admin_id: int, action: str):
    with db_lock:
        db.execute(
            "INSERT INTO admin_logs(admin_id,action,created_at) VALUES(?,?,?)",
            (admin_id, action, now()),
        )
        db.commit()


def get_setting(key: str, default: str = "") -> str:
    with db_lock:
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    with db_lock:
        db.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        db.commit()


def get_text(key: str) -> str:
    with db_lock:
        row = db.execute("SELECT value FROM texts WHERE key=?", (key,)).fetchone()
    return row["value"] if row else DEFAULT_TEXTS.get(key, "")


def get_button(key: str) -> str:
    with db_lock:
        row = db.execute("SELECT value FROM buttons WHERE key=?", (key,)).fetchone()
    return row["value"] if row else DEFAULT_BUTTONS.get(key, key)


def get_user(user_id: int):
    with db_lock:
        return db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def ensure_user(tg_user, referred_by: Optional[int] = None):
    existing = get_user(tg_user.id)
    if existing:
        with db_lock:
            db.execute(
                "UPDATE users SET username=?, first_name=? WHERE user_id=?",
                (tg_user.username or "", tg_user.first_name or "User", tg_user.id),
            )
            db.commit()
        return

    valid_referrer = None
    if referred_by and referred_by != tg_user.id and get_user(referred_by):
        valid_referrer = referred_by

    with db_lock:
        db.execute(
            """
            INSERT INTO users(
                user_id,username,first_name,referred_by,joined_at
            ) VALUES(?,?,?,?,?)
            """,
            (
                tg_user.id,
                tg_user.username or "",
                tg_user.first_name or "User",
                valid_referrer,
                now(),
            ),
        )

        if valid_referrer:
            db.execute(
                "UPDATE users SET referral_count=referral_count+1 WHERE user_id=?",
                (valid_referrer,),
            )
            row = db.execute(
                "SELECT referral_count FROM users WHERE user_id=?", (valid_referrer,)
            ).fetchone()
            target = max(1, int(get_setting("referral_target", "15")))
            if row and row["referral_count"] % target == 0:
                db.execute(
                    "UPDATE users SET referral_rewards=referral_rewards+1 WHERE user_id=?",
                    (valid_referrer,),
                )
        db.commit()

    notify_admins(
        "👤 <b>New User Joined</b>\n\n"
        f"Name: {html.escape(tg_user.first_name or 'User')}\n"
        f"Username: @{html.escape(tg_user.username or 'none')}\n"
        f"User ID: <code>{tg_user.id}</code>"
    )

    if valid_referrer:
        try:
            ref = get_user(valid_referrer)
            target = int(get_setting("referral_target", "15"))
            bot.send_message(
                valid_referrer,
                "🎉 New successful referral!\n\n"
                f"Progress: {ref['referral_count']}/{target}",
            )
        except Exception:
            pass


def total_orders(user_id: int) -> int:
    with db_lock:
        return db.execute(
            "SELECT COUNT(*) AS c FROM orders WHERE user_id=?", (user_id,)
        ).fetchone()["c"]


def main_menu(user_id: int):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Two buttons on each row.
    kb.row(get_button("buy"), get_button("deposit"))
    kb.row(get_button("wallet"), get_button("orders"))
    kb.row(get_button("account"), get_button("referral"))
    kb.row(get_button("reseller"), get_button("support"))
    kb.row(get_button("information"))

    # Hidden from normal users; shown only to both full owner admins.
    if is_admin(user_id):
        kb.row(get_button("admin"))

    return kb


def back_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Back")
    return kb


def add_back_button(kb):
    kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="go_home"))
    return kb


def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row("👥 User Manager", "💎 Reseller Manager")
    kb.row("💰 Wallet Manager", "💳 Deposit Requests")
    kb.row("📦 Orders", "🔑 Add Keys")
    kb.row("🎁 Referral Manager", "🎟 Discount Manager")
    kb.row("📝 Text Editor", "🔘 Button Editor")
    kb.row("📢 Broadcast", "📊 Statistics")
    kb.row("🎨 Button Color", "⚙️ Settings")
    kb.row("🔙 Back")
    return kb


def send_home(chat_id: int, user_id: int):
    user = get_user(user_id)
    if not user:
        return

    text = get_text("welcome").format(
        first_name=html.escape(user["first_name"]),
        balance=user["balance"],
        account_type=user["account_type"],
        total_orders=total_orders(user_id),
        referral_rewards=user["referral_rewards"],
    )

    try:
        bot.send_photo(
            chat_id,
            BANNER_URL,
            caption=text,
            reply_markup=main_menu(user_id),
        )
    except Exception:
        bot.send_message(chat_id, text, reply_markup=main_menu(user_id))


def user_is_banned(user_id: int) -> bool:
    user = get_user(user_id)
    return bool(user and user["banned"])


def progress_bar(current: int, target: int) -> str:
    target = max(1, target)
    filled = min(target, current % target)
    if current > 0 and current % target == 0:
        filled = target
    return "█" * filled + "░" * (target - filled)


def reseller_discount_for(user) -> int:
    if user["account_type"] == "Reseller":
        return max(0, min(100, int(get_setting("reseller_discount", "10"))))
    return 0


def final_price(base_price: int, discount: int) -> int:
    return max(0, round(base_price * (100 - discount) / 100))


# =========================
# START / HOME
# =========================

@bot.message_handler(commands=["start"])
def start_handler(message):
    referrer = None
    parts = message.text.split(maxsplit=1)
    if len(parts) == 2:
        token = parts[1].strip()
        if token.startswith("vip_"):
            token = token[4:]
        if token.isdigit():
            referrer = int(token)

    ensure_user(message.from_user, referrer)

    if user_is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Your account is blocked.")
        return

    send_home(message.chat.id, message.from_user.id)


@bot.message_handler(func=lambda m: m.text in ("🔙 Back", "🔙 Back to Menu"))
def back_home(message):
    ensure_user(message.from_user)
    send_home(message.chat.id, message.from_user.id)


@bot.callback_query_handler(func=lambda c: c.data == "go_home")
def inline_go_home(call):
    ensure_user(call.from_user)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    send_home(call.message.chat.id, call.from_user.id)


# =========================
# BUY FLOW
# =========================

@bot.message_handler(func=lambda m: m.text == get_button("buy"))
def buy_handler(message):
    ensure_user(message.from_user)
    if user_is_banned(message.from_user.id):
        return

    notify_admins(
        "🛒 <b>Buy Opened</b>\n\n"
        f"User: @{html.escape(message.from_user.username or 'none')}\n"
        f"ID: <code>{message.from_user.id}</code>"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"🔥 {PRODUCT_NAME}", callback_data="product:boss_modz"))
    add_back_button(kb)
    bot.send_message(message.chat.id, get_text("select_product"), reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "product:boss_modz")
def product_selected(call):
    notify_admins(
        "📦 <b>Product Selected</b>\n\n"
        f"User: @{html.escape(call.from_user.username or 'none')}\n"
        f"ID: <code>{call.from_user.id}</code>\n"
        f"Product: {PRODUCT_NAME}"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)
    # Duration only. No price shown here.
    kb.row(
        types.InlineKeyboardButton("⚡ 1 Day", callback_data="duration:1d"),
        types.InlineKeyboardButton("🔥 3 Days", callback_data="duration:3d"),
    )
    kb.row(
        types.InlineKeyboardButton("💎 7 Days", callback_data="duration:7d"),
        types.InlineKeyboardButton("👑 15 Days", callback_data="duration:15d"),
    )
    kb.row(types.InlineKeyboardButton("🚀 30 Days", callback_data="duration:30d"))
    add_back_button(kb)

    bot.edit_message_text(
        get_text("select_duration"),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("duration:"))
def duration_selected(call):
    duration = call.data.split(":", 1)[1]
    plan = PLANS.get(duration)
    if not plan:
        return

    user = get_user(call.from_user.id)
    discount = reseller_discount_for(user)
    price = final_price(plan["price"], discount)

    with db_lock:
        stock = db.execute(
            "SELECT COUNT(*) AS c FROM keys_stock WHERE duration=? AND used=0",
            (duration,),
        ).fetchone()["c"]

    summary = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 ORDER SUMMARY\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Product : {PRODUCT_NAME}\n"
        f"⏳ Duration : {plan['name']}\n"
        f"💵 Real Price : ₹{plan['price']}\n"
        f"🎟 Discount : {discount}%\n"
        f"💰 Final Price : ₹{price}\n"
        f"🪙 Wallet Balance : ₹{user['balance']}\n"
        f"🔑 Available Stock : {stock}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Confirm Order", callback_data=f"confirm:{duration}"),
        types.InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order"),
    )
    add_back_button(kb)

    notify_admins(
        "⏳ <b>Duration Selected</b>\n\n"
        f"User: @{html.escape(call.from_user.username or 'none')}\n"
        f"ID: <code>{call.from_user.id}</code>\n"
        f"Product: {PRODUCT_NAME}\n"
        f"Duration: {plan['name']}\n"
        f"Final Price: ₹{price}"
    )

    bot.edit_message_text(
        summary,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data == "cancel_order")
def cancel_order(call):
    kb = types.InlineKeyboardMarkup()
    add_back_button(kb)
    bot.edit_message_text(
        "━━━━━━━━━━━━━━━━━━━━\n"
        "❌ ORDER CANCELLED\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Your order has been cancelled successfully.\n"
        "No balance has been deducted.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb,
    )
    notify_admins(
        "❌ <b>Order Cancelled</b>\n\n"
        f"User: @{html.escape(call.from_user.username or 'none')}\n"
        f"ID: <code>{call.from_user.id}</code>"
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm:"))
def confirm_order(call):
    duration = call.data.split(":", 1)[1]
    plan = PLANS.get(duration)
    if not plan:
        return

    user = get_user(call.from_user.id)
    discount = reseller_discount_for(user)
    price = final_price(plan["price"], discount)

    if user["balance"] < price:
        bot.answer_callback_query(call.id, "Insufficient wallet balance.", show_alert=True)
        notify_admins(
            "⚠️ <b>Order Failed: Low Balance</b>\n\n"
            f"User ID: <code>{call.from_user.id}</code>\n"
            f"Required: ₹{price}\n"
            f"Available: ₹{user['balance']}"
        )
        return

    with db_lock:
        key_row = db.execute(
            "SELECT * FROM keys_stock WHERE duration=? AND used=0 ORDER BY id LIMIT 1",
            (duration,),
        ).fetchone()

        if not key_row:
            bot.answer_callback_query(call.id, "This duration is out of stock.", show_alert=True)
            notify_admins(
                "⚠️ <b>Out of Stock</b>\n\n"
                f"Product: {PRODUCT_NAME}\n"
                f"Duration: {plan['name']}"
            )
            return

        try:
            db.execute("BEGIN IMMEDIATE")
            fresh_user = db.execute(
                "SELECT balance FROM users WHERE user_id=?", (call.from_user.id,)
            ).fetchone()

            if not fresh_user or fresh_user["balance"] < price:
                db.rollback()
                bot.answer_callback_query(call.id, "Insufficient balance.", show_alert=True)
                return

            reserved = db.execute(
                """
                UPDATE keys_stock
                SET used=1, used_by=?, used_at=?
                WHERE id=? AND used=0
                """,
                (call.from_user.id, now(), key_row["id"]),
            )

            if reserved.rowcount != 1:
                db.rollback()
                bot.answer_callback_query(call.id, "Please try again.", show_alert=True)
                return

            db.execute(
                """
                UPDATE users
                SET balance=balance-?, total_spent=total_spent+?
                WHERE user_id=?
                """,
                (price, price, call.from_user.id),
            )

            cursor = db.execute(
                """
                INSERT INTO orders(
                    user_id,product_name,duration,base_price,
                    discount_percent,final_price,key_value,status,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    call.from_user.id,
                    PRODUCT_NAME,
                    duration,
                    plan["price"],
                    discount,
                    price,
                    key_row["key_value"],
                    "Completed",
                    now(),
                ),
            )
            order_id = cursor.lastrowid
            db.commit()
        except Exception:
            db.rollback()
            bot.answer_callback_query(call.id, "Order failed. Try again.", show_alert=True)
            return

    success = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎉 PURCHASE SUCCESSFUL\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🧾 Order ID : #{order_id}\n"
        f"📦 Product : {PRODUCT_NAME}\n"
        f"⏳ Duration : {plan['name']}\n"
        f"💰 Amount Paid : ₹{price}\n\n"
        "🔑 Your Product Key\n"
        f"<code>{html.escape(key_row['key_value'])}</code>\n\n"
        "📌 Keep this key private and safe.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    success_kb = types.InlineKeyboardMarkup()
    add_back_button(success_kb)
    bot.edit_message_text(success, call.message.chat.id, call.message.message_id, reply_markup=success_kb)
    bot.answer_callback_query(call.id, "Order completed.")

    notify_admins(
        "✅ <b>New Order Completed</b>\n\n"
        f"Order ID: #{order_id}\n"
        f"User: @{html.escape(call.from_user.username or 'none')}\n"
        f"User ID: <code>{call.from_user.id}</code>\n"
        f"Product: {PRODUCT_NAME}\n"
        f"Duration: {plan['name']}\n"
        f"Base Price: ₹{plan['price']}\n"
        f"Discount: {discount}%\n"
        f"Paid: ₹{price}"
    )


# =========================
# WALLET / ORDERS / ACCOUNT
# =========================

@bot.message_handler(func=lambda m: m.text == get_button("wallet"))
def wallet_handler(message):
    ensure_user(message.from_user)
    user = get_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        get_text("wallet").format(
            balance=user["balance"],
            total_deposits=user["total_deposits"],
            total_spent=user["total_spent"],
        ),
        reply_markup=back_menu(),
    )


@bot.message_handler(func=lambda m: m.text == get_button("orders"))
def orders_handler(message):
    ensure_user(message.from_user)
    with db_lock:
        rows = db.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10",
            (message.from_user.id,),
        ).fetchall()

    if not rows:
        body = "No purchases yet."
    else:
        blocks = []
        for row in rows:
            duration_name = PLANS.get(row["duration"], {"name": row["duration"]})["name"]
            blocks.append(
                f"🧾 Order #{row['id']}\n"
                f"📦 {html.escape(row['product_name'])}\n"
                f"⏳ {duration_name}\n"
                f"💰 ₹{row['final_price']}\n"
                f"🔑 <code>{html.escape(row['key_value'])}</code>\n"
                f"📌 {row['status']}"
            )
        body = "\n\n".join(blocks)

    bot.send_message(
        message.chat.id,
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📦 MY ORDERS\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{body}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=back_menu(),
    )


@bot.message_handler(func=lambda m: m.text == get_button("account"))
def account_handler(message):
    ensure_user(message.from_user)
    user = get_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        get_text("account").format(
            first_name=html.escape(user["first_name"]),
            user_id=user["user_id"],
            account_type=user["account_type"],
            balance=user["balance"],
            total_orders=total_orders(user["user_id"]),
            referral_count=user["referral_count"],
        ),
        reply_markup=back_menu(),
    )


# =========================
# REFERRAL
# =========================

@bot.message_handler(func=lambda m: m.text == get_button("referral"))
def referral_handler(message):
    ensure_user(message.from_user)
    user = get_user(message.from_user.id)
    target = max(1, int(get_setting("referral_target", "15")))
    username = bot.get_me().username
    referral_link = f"https://t.me/{username}?start={message.from_user.id}"
    bar = progress_bar(user["referral_count"], target)

    text = (
        "🎁 ─── REFERRAL PROGRAM ─── 🎁\n\n"
        f"Invite your friends and unlock an exclusive reward after {target} successful referrals!\n\n"
        "🔗 Your KING Store Referral Link:\n"
        f"{referral_link}\n\n"
        "📊 Your Progress:\n"
        f"{bar} {user['referral_count']}/{target} Referrals"
    )

    kb = types.InlineKeyboardMarkup()
    if user["referral_rewards"] > 0:
        kb.add(types.InlineKeyboardButton("🎁 Claim Reward", callback_data="claim_referral_reward"))
    add_back_button(kb)

    bot.send_message(message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "claim_referral_reward")
def claim_referral_reward(call):
    user = get_user(call.from_user.id)
    if not user or user["referral_rewards"] <= 0:
        bot.answer_callback_query(call.id, "No reward is available.", show_alert=True)
        return

    duration = get_setting("referral_reward_duration", "1d")
    plan = PLANS.get(duration, PLANS["1d"])

    with db_lock:
        key_row = db.execute(
            "SELECT * FROM keys_stock WHERE duration=? AND used=0 ORDER BY id LIMIT 1",
            (duration,),
        ).fetchone()

        if not key_row:
            bot.answer_callback_query(call.id, "Reward stock is unavailable.", show_alert=True)
            notify_admins("⚠️ Referral reward stock is empty.")
            return

        db.execute("BEGIN IMMEDIATE")
        reserved = db.execute(
            "UPDATE keys_stock SET used=1, used_by=?, used_at=? WHERE id=? AND used=0",
            (call.from_user.id, now(), key_row["id"]),
        )
        if reserved.rowcount != 1:
            db.rollback()
            bot.answer_callback_query(call.id, "Try again.", show_alert=True)
            return

        db.execute(
            """
            UPDATE users
            SET referral_rewards=referral_rewards-1
            WHERE user_id=? AND referral_rewards>0
            """,
            (call.from_user.id,),
        )
        db.commit()

    bot.send_message(
        call.message.chat.id,
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ REWARD CLAIMED\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎁 Reward : {plan['name']} Key\n"
        f"🔑 <code>{html.escape(key_row['key_value'])}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=back_menu(),
    )

    notify_admins(
        "🎁 <b>Referral Reward Claimed</b>\n\n"
        f"User: @{html.escape(call.from_user.username or 'none')}\n"
        f"ID: <code>{call.from_user.id}</code>\n"
        f"Reward: {plan['name']} Key"
    )


# =========================
# RESELLER
# =========================

@bot.message_handler(func=lambda m: m.text == get_button("reseller"))
def reseller_handler(message):
    ensure_user(message.from_user)
    user = get_user(message.from_user.id)
    discount = int(get_setting("reseller_discount", "10"))

    if user["account_type"] == "Reseller":
        bot.send_message(
            message.chat.id,
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💎 RESELLER ACCOUNT\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Your current reseller discount is {discount}%.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏆 KING Official Store\n"
            "━━━━━━━━━━━━━━━━━━━━",
            reply_markup=back_menu(),
        )
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💎 Request Reseller", callback_data="request_reseller"))
    add_back_button(kb)

    bot.send_message(
        message.chat.id,
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💎 BECOME A RESELLER\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Current reseller discount: {discount}%\n\n"
        "Send a request to the owner admins.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data == "request_reseller")
def request_reseller(call):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"reseller_ok:{call.from_user.id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reseller_no:{call.from_user.id}"),
    )

    notify_admins(
        "💎 <b>New Reseller Request</b>\n\n"
        f"User: @{html.escape(call.from_user.username or 'none')}\n"
        f"ID: <code>{call.from_user.id}</code>",
    )

    for admin_id in OWNER_ADMINS:
        try:
            bot.send_message(admin_id, "Approve or reject:", reply_markup=kb)
        except Exception:
            pass

    bot.answer_callback_query(call.id, "Request sent to owner admins.", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith("reseller_ok:") or c.data.startswith("reseller_no:"))
def reseller_decision(call):
    if not is_admin(call.from_user.id):
        return

    action, raw_user_id = call.data.split(":", 1)
    user_id = int(raw_user_id)

    if action == "reseller_ok":
        with db_lock:
            db.execute("UPDATE users SET account_type='Reseller' WHERE user_id=?", (user_id,))
            db.commit()
        bot.send_message(user_id, "✅ Your account has been upgraded to Reseller.")
        bot.answer_callback_query(call.id, "Reseller approved.")
        log_admin(call.from_user.id, f"Approved reseller {user_id}")
    else:
        bot.send_message(user_id, "❌ Your reseller request was rejected.")
        bot.answer_callback_query(call.id, "Request rejected.")
        log_admin(call.from_user.id, f"Rejected reseller {user_id}")


# =========================
# DEPOSIT
# =========================

@bot.message_handler(func=lambda m: m.text == get_button("deposit"))
def deposit_handler(message):
    ensure_user(message.from_user)
    msg = bot.send_message(
        message.chat.id,
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💳 DEPOSIT BALANCE\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send the amount you want to deposit.\n"
        "Example: <code>500</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=back_menu(),
    )
    bot.register_next_step_handler(msg, deposit_amount_step)


def deposit_amount_step(message):
    try:
        amount = int((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Send a valid positive amount.")
        bot.register_next_step_handler(msg, deposit_amount_step)
        return

    msg = bot.send_message(
        message.chat.id,
        "Send your payment Transaction ID or payment screenshot now.",
    )
    bot.register_next_step_handler(msg, deposit_proof_step, amount)


def deposit_proof_step(message, amount: int):
    proof = message.text or message.caption or "Payment screenshot submitted"

    with db_lock:
        cursor = db.execute(
            """
            INSERT INTO deposits(user_id,amount,proof,status,created_at)
            VALUES(?,?,?,'Pending',?)
            """,
            (message.from_user.id, amount, proof, now()),
        )
        deposit_id = cursor.lastrowid
        db.commit()

    bot.send_message(message.chat.id, "⏳ Your deposit request has been submitted.", reply_markup=back_menu())

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"deposit_ok:{deposit_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"deposit_no:{deposit_id}"),
    )

    for admin_id in OWNER_ADMINS:
        try:
            bot.send_message(
                admin_id,
                "💳 <b>New Deposit Request</b>\n\n"
                f"User ID: <code>{message.from_user.id}</code>\n"
                f"Amount: ₹{amount}\n"
                f"Proof: {html.escape(proof)}",
                reply_markup=kb,
            )
        except Exception:
            pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("deposit_ok:") or c.data.startswith("deposit_no:"))
def deposit_decision(call):
    if not is_admin(call.from_user.id):
        return

    action, raw_id = call.data.split(":", 1)
    deposit_id = int(raw_id)

    with db_lock:
        deposit = db.execute("SELECT * FROM deposits WHERE id=?", (deposit_id,)).fetchone()

        if not deposit or deposit["status"] != "Pending":
            bot.answer_callback_query(call.id, "Already processed.", show_alert=True)
            return

        if action == "deposit_ok":
            db.execute("UPDATE deposits SET status='Approved' WHERE id=?", (deposit_id,))
            db.execute(
                """
                UPDATE users
                SET balance=balance+?, total_deposits=total_deposits+?
                WHERE user_id=?
                """,
                (deposit["amount"], deposit["amount"], deposit["user_id"]),
            )
            db.commit()
            user = get_user(deposit["user_id"])
            bot.send_message(
                deposit["user_id"],
                f"✅ Deposit approved.\n\nAdded: ₹{deposit['amount']}\nNew Balance: ₹{user['balance']}",
            )
            bot.edit_message_text("✅ Deposit approved.", call.message.chat.id, call.message.message_id)
            log_admin(call.from_user.id, f"Approved deposit {deposit_id}")
        else:
            db.execute("UPDATE deposits SET status='Rejected' WHERE id=?", (deposit_id,))
            db.commit()
            bot.send_message(deposit["user_id"], "❌ Your deposit request was rejected.")
            bot.edit_message_text("❌ Deposit rejected.", call.message.chat.id, call.message.message_id)
            log_admin(call.from_user.id, f"Rejected deposit {deposit_id}")


# =========================
# SUPPORT / INFORMATION
# =========================

@bot.message_handler(func=lambda m: m.text == get_button("support"))
def support_handler(message):
    bot.send_message(
        message.chat.id,
        get_text("support").format(support_username=SUPPORT_USERNAME),
        reply_markup=back_menu(),
    )
    notify_admins(
        "📞 <b>Support Opened</b>\n\n"
        f"User: @{html.escape(message.from_user.username or 'none')}\n"
        f"ID: <code>{message.from_user.id}</code>"
    )


@bot.message_handler(func=lambda m: m.text == get_button("information"))
def information_handler(message):
    bot.send_message(message.chat.id, get_setting("information_text"), reply_markup=back_menu())


# =========================
# ADMIN PANEL
# =========================

@bot.message_handler(func=lambda m: m.text == get_button("admin"))
def admin_panel_handler(message):
    if not is_admin(message.from_user.id):
        return

    bot.send_message(
        message.chat.id,
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👑 OWNER ADMIN PANEL\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Both owner admins have full access.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 KING Official Store\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=admin_menu(),
    )


# ---------- ADD KEYS ----------

@bot.message_handler(func=lambda m: m.text == "🔑 Add Keys")
def add_keys_handler(message):
    if not is_admin(message.from_user.id):
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("⚡ 1 Day", callback_data="addkeys:1d"),
        types.InlineKeyboardButton("🔥 3 Days", callback_data="addkeys:3d"),
    )
    kb.row(
        types.InlineKeyboardButton("💎 7 Days", callback_data="addkeys:7d"),
        types.InlineKeyboardButton("👑 15 Days", callback_data="addkeys:15d"),
    )
    kb.row(types.InlineKeyboardButton("🚀 30 Days", callback_data="addkeys:30d"))
    add_back_button(kb)

    bot.send_message(message.chat.id, "Select the duration for the keys.", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("addkeys:"))
def add_keys_duration(call):
    if not is_admin(call.from_user.id):
        return

    duration = call.data.split(":", 1)[1]
    msg = bot.send_message(
        call.message.chat.id,
        f"Send one or multiple keys for <b>{PLANS[duration]['name']}</b>.\n"
        "Put every key on a new line.",
    )
    bot.register_next_step_handler(msg, save_keys_step, duration)


def save_keys_step(message, duration: str):
    if not is_admin(message.from_user.id):
        return

    keys = [line.strip() for line in (message.text or "").splitlines() if line.strip()]
    added = 0
    duplicates = 0

    with db_lock:
        for key in keys:
            try:
                db.execute(
                    "INSERT INTO keys_stock(duration,key_value) VALUES(?,?)",
                    (duration, key),
                )
                added += 1
            except sqlite3.IntegrityError:
                duplicates += 1
        db.commit()

        stock = db.execute(
            "SELECT COUNT(*) AS c FROM keys_stock WHERE duration=? AND used=0",
            (duration,),
        ).fetchone()["c"]

    bot.send_message(
        message.chat.id,
        "✅ Keys Added Successfully\n\n"
        f"Duration: {PLANS[duration]['name']}\n"
        f"Added: {added}\n"
        f"Duplicates: {duplicates}\n"
        f"Available Stock: {stock}",
    )
    log_admin(message.from_user.id, f"Added {added} keys to {duration}")


# ---------- WALLET MANAGER ----------

@bot.message_handler(func=lambda m: m.text == "💰 Wallet Manager")
def wallet_manager(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "Send the user's Telegram numeric ID.")
    bot.register_next_step_handler(msg, wallet_user_step)


def wallet_user_step(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int((message.text or "").strip())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid user ID.")
        return

    user = get_user(user_id)
    if not user:
        bot.send_message(message.chat.id, "❌ User not found.")
        return

    msg = bot.send_message(
        message.chat.id,
        f"Current balance: ₹{user['balance']}\n\n"
        "Send amount to add.\n"
        "Use a negative value to remove balance.\n"
        "Example: <code>500</code> or <code>-100</code>",
    )
    bot.register_next_step_handler(msg, wallet_amount_step, user_id)


def wallet_amount_step(message, user_id: int):
    if not is_admin(message.from_user.id):
        return

    try:
        amount = int((message.text or "").strip())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount.")
        return

    with db_lock:
        db.execute(
            "UPDATE users SET balance=MAX(balance+?,0) WHERE user_id=?",
            (amount, user_id),
        )
        db.commit()

    user = get_user(user_id)
    bot.send_message(message.chat.id, f"✅ New balance: ₹{user['balance']}")
    try:
        bot.send_message(
            user_id,
            "💰 Your wallet balance has been updated by an owner admin.\n\n"
            f"Change: ₹{amount}\n"
            f"New Balance: ₹{user['balance']}",
        )
    except Exception:
        pass

    log_admin(message.from_user.id, f"Changed balance for {user_id} by {amount}")


# ---------- USER MANAGER ----------

@bot.message_handler(func=lambda m: m.text == "👥 User Manager")
def user_manager(message):
    if not is_admin(message.from_user.id):
        return

    msg = bot.send_message(message.chat.id, "Send the user's Telegram numeric ID.")
    bot.register_next_step_handler(msg, user_manager_lookup)


def user_manager_lookup(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int((message.text or "").strip())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid user ID.")
        return

    user = get_user(user_id)
    if not user:
        bot.send_message(message.chat.id, "❌ User not found.")
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("➕ Referrals", callback_data=f"user_ref_add:{user_id}"),
        types.InlineKeyboardButton("➖ Referrals", callback_data=f"user_ref_remove:{user_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("➕ Rewards", callback_data=f"user_reward_add:{user_id}"),
        types.InlineKeyboardButton("➖ Rewards", callback_data=f"user_reward_remove:{user_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("💎 Make Reseller", callback_data=f"user_reseller:{user_id}"),
        types.InlineKeyboardButton("👤 Make Customer", callback_data=f"user_customer:{user_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("🚫 Ban", callback_data=f"user_ban:{user_id}"),
        types.InlineKeyboardButton("✅ Unban", callback_data=f"user_unban:{user_id}"),
    )
    add_back_button(kb)

    bot.send_message(
        message.chat.id,
        f"👤 {html.escape(user['first_name'])}\n"
        f"ID: <code>{user_id}</code>\n"
        f"Type: {user['account_type']}\n"
        f"Balance: ₹{user['balance']}\n"
        f"Referrals: {user['referral_count']}\n"
        f"Rewards: {user['referral_rewards']}\n"
        f"Banned: {'Yes' if user['banned'] else 'No'}",
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("user_"))
def user_manager_action(call):
    if not is_admin(call.from_user.id):
        return

    action, raw_user_id = call.data.split(":", 1)
    user_id = int(raw_user_id)

    with db_lock:
        if action == "user_ref_add":
            db.execute("UPDATE users SET referral_count=referral_count+1 WHERE user_id=?", (user_id,))
        elif action == "user_ref_remove":
            db.execute("UPDATE users SET referral_count=MAX(referral_count-1,0) WHERE user_id=?", (user_id,))
        elif action == "user_reward_add":
            db.execute("UPDATE users SET referral_rewards=referral_rewards+1 WHERE user_id=?", (user_id,))
        elif action == "user_reward_remove":
            db.execute("UPDATE users SET referral_rewards=MAX(referral_rewards-1,0) WHERE user_id=?", (user_id,))
        elif action == "user_reseller":
            db.execute("UPDATE users SET account_type='Reseller' WHERE user_id=?", (user_id,))
        elif action == "user_customer":
            db.execute("UPDATE users SET account_type='Customer' WHERE user_id=?", (user_id,))
        elif action == "user_ban":
            db.execute("UPDATE users SET banned=1 WHERE user_id=?", (user_id,))
        elif action == "user_unban":
            db.execute("UPDATE users SET banned=0 WHERE user_id=?", (user_id,))
        db.commit()

    user = get_user(user_id)
    bot.answer_callback_query(call.id, "Updated successfully.")
    try:
        bot.send_message(user_id, "🔔 Your KING Store account details were updated by an owner admin.")
    except Exception:
        pass

    log_admin(call.from_user.id, f"{action} on user {user_id}")


# ---------- RESELLER MANAGER ----------

@bot.message_handler(func=lambda m: m.text == "💎 Reseller Manager")
def reseller_manager(message):
    if not is_admin(message.from_user.id):
        return

    with db_lock:
        rows = db.execute(
            "SELECT user_id,username,first_name FROM users WHERE account_type='Reseller' ORDER BY joined_at DESC LIMIT 50"
        ).fetchall()

    if not rows:
        body = "No resellers yet."
    else:
        body = "\n".join(
            f"• {html.escape(row['first_name'])} (@{html.escape(row['username'] or 'none')}) — <code>{row['user_id']}</code>"
            for row in rows
        )

    bot.send_message(message.chat.id, f"💎 <b>Resellers</b>\n\n{body}", reply_markup=admin_menu())


# ---------- DISCOUNT MANAGER ----------

@bot.message_handler(func=lambda m: m.text == "🎟 Discount Manager")
def discount_manager(message):
    if not is_admin(message.from_user.id):
        return

    current = get_setting("reseller_discount", "10")
    msg = bot.send_message(
        message.chat.id,
        "🎟 <b>Reseller Discount Manager</b>\n\n"
        f"Current discount: {current}%\n\n"
        "Send any discount from 0 to 100.\n"
        "Example: <code>10</code>, <code>50</code>, or <code>100</code>",
    )
    bot.register_next_step_handler(msg, discount_save_step)


def discount_save_step(message):
    if not is_admin(message.from_user.id):
        return

    try:
        discount = int((message.text or "").strip())
        if not 0 <= discount <= 100:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ Discount must be between 0 and 100.")
        return

    set_setting("reseller_discount", str(discount))
    bot.send_message(message.chat.id, f"✅ Reseller discount changed to {discount}%.", reply_markup=admin_menu())
    log_admin(message.from_user.id, f"Changed reseller discount to {discount}%")


# ---------- REFERRAL MANAGER ----------

@bot.message_handler(func=lambda m: m.text == "🎁 Referral Manager")
def referral_manager(message):
    if not is_admin(message.from_user.id):
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("🎯 Change Target", callback_data="ref_admin_target"),
        types.InlineKeyboardButton("🎁 Reward Duration", callback_data="ref_admin_duration"),
    )
    add_back_button(kb)
    bot.send_message(
        message.chat.id,
        f"Current target: {get_setting('referral_target', '15')}\n"
        f"Reward duration: {PLANS[get_setting('referral_reward_duration', '1d')]['name']}",
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data == "ref_admin_target")
def referral_target_prompt(call):
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "Send the new referral target.")
    bot.register_next_step_handler(msg, referral_target_save)


def referral_target_save(message):
    if not is_admin(message.from_user.id):
        return
    try:
        target = int((message.text or "").strip())
        if target < 1:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ Enter a positive number.")
        return
    set_setting("referral_target", str(target))
    bot.send_message(message.chat.id, f"✅ Referral target changed to {target}.", reply_markup=admin_menu())
    log_admin(message.from_user.id, f"Changed referral target to {target}")


@bot.callback_query_handler(func=lambda c: c.data == "ref_admin_duration")
def referral_duration_prompt(call):
    if not is_admin(call.from_user.id):
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    for code, plan in PLANS.items():
        kb.add(types.InlineKeyboardButton(plan["name"], callback_data=f"ref_reward_duration:{code}"))
    add_back_button(kb)
    bot.send_message(call.message.chat.id, "Select reward key duration.", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ref_reward_duration:"))
def referral_duration_save(call):
    if not is_admin(call.from_user.id):
        return
    duration = call.data.split(":", 1)[1]
    set_setting("referral_reward_duration", duration)
    bot.answer_callback_query(call.id, "Reward duration updated.")
    log_admin(call.from_user.id, f"Changed referral reward duration to {duration}")


# ---------- TEXT EDITOR ----------

@bot.message_handler(func=lambda m: m.text == "📝 Text Editor")
def text_editor(message):
    if not is_admin(message.from_user.id):
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    for key in DEFAULT_TEXTS:
        kb.add(types.InlineKeyboardButton(key.replace("_", " ").title(), callback_data=f"text_edit:{key}"))
    add_back_button(kb)
    bot.send_message(message.chat.id, "Select the text you want to edit.", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("text_edit:"))
def text_edit_prompt(call):
    if not is_admin(call.from_user.id):
        return

    key = call.data.split(":", 1)[1]
    current = get_text(key)

    msg = bot.send_message(
        call.message.chat.id,
        f"Current text for <b>{key}</b>:\n\n"
        f"<pre>{html.escape(current)}</pre>\n\n"
        "Send the new text now.",
    )
    bot.register_next_step_handler(msg, text_save_step, key)


def text_save_step(message, key: str):
    if not is_admin(message.from_user.id):
        return

    new_text = message.text or ""
    if not new_text.strip():
        bot.send_message(message.chat.id, "❌ Text cannot be empty.")
        return

    with db_lock:
        db.execute(
            "INSERT INTO texts(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, new_text),
        )
        db.commit()

    bot.send_message(message.chat.id, "✅ Text updated successfully.", reply_markup=admin_menu())
    log_admin(message.from_user.id, f"Edited text {key}")


# ---------- BUTTON EDITOR ----------

@bot.message_handler(func=lambda m: m.text == "🔘 Button Editor")
def button_editor(message):
    if not is_admin(message.from_user.id):
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    for key in DEFAULT_BUTTONS:
        kb.add(types.InlineKeyboardButton(key.title(), callback_data=f"button_edit:{key}"))
    add_back_button(kb)
    bot.send_message(message.chat.id, "Select the button name you want to edit.", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("button_edit:"))
def button_edit_prompt(call):
    if not is_admin(call.from_user.id):
        return

    key = call.data.split(":", 1)[1]
    current = get_button(key)
    msg = bot.send_message(
        call.message.chat.id,
        f"Current button text:\n<code>{html.escape(current)}</code>\n\n"
        "Send the new button text.",
    )
    bot.register_next_step_handler(msg, button_save_step, key)


def button_save_step(message, key: str):
    if not is_admin(message.from_user.id):
        return

    new_text = (message.text or "").strip()
    if not new_text:
        bot.send_message(message.chat.id, "❌ Button text cannot be empty.")
        return

    with db_lock:
        db.execute(
            "INSERT INTO buttons(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, new_text),
        )
        db.commit()

    bot.send_message(message.chat.id, "✅ Button text updated.", reply_markup=admin_menu())
    log_admin(message.from_user.id, f"Edited button {key}")


# ---------- BUTTON COLOR ----------

@bot.message_handler(func=lambda m: m.text == "🎨 Button Color")
def button_color_handler(message):
    if not is_admin(message.from_user.id):
        return

    current = get_setting("button_color", "#22C55E")
    msg = bot.send_message(
        message.chat.id,
        "🎨 <b>Button Color</b>\n\n"
        f"Saved HEX color: <code>{current}</code>\n\n"
        "Send a new HEX color, for example <code>#22C55E</code>.\n\n"
        "Note: Telegram's normal bot keyboard does not allow bots to force custom button colors. "
        "This value is saved for a future Mini App/Web App interface.",
    )
    bot.register_next_step_handler(msg, button_color_save)


def button_color_save(message):
    if not is_admin(message.from_user.id):
        return

    color = (message.text or "").strip().upper()
    valid = (
        len(color) == 7
        and color.startswith("#")
        and all(ch in "0123456789ABCDEF" for ch in color[1:])
    )
    if not valid:
        bot.send_message(message.chat.id, "❌ Invalid HEX color. Example: #22C55E")
        return

    set_setting("button_color", color)
    bot.send_message(message.chat.id, f"✅ Button color saved: <code>{color}</code>", reply_markup=admin_menu())
    log_admin(message.from_user.id, f"Saved button color {color}")


# ---------- STATISTICS / ORDERS / DEPOSITS ----------

@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def statistics_handler(message):
    if not is_admin(message.from_user.id):
        return

    with db_lock:
        users = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        resellers = db.execute(
            "SELECT COUNT(*) AS c FROM users WHERE account_type='Reseller'"
        ).fetchone()["c"]
        orders = db.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"]
        revenue = db.execute(
            "SELECT COALESCE(SUM(final_price),0) AS s FROM orders"
        ).fetchone()["s"]
        stock = db.execute(
            "SELECT COUNT(*) AS c FROM keys_stock WHERE used=0"
        ).fetchone()["c"]
        pending = db.execute(
            "SELECT COUNT(*) AS c FROM deposits WHERE status='Pending'"
        ).fetchone()["c"]

    bot.send_message(
        message.chat.id,
        "📊 <b>Store Statistics</b>\n\n"
        f"👥 Total Users: {users}\n"
        f"💎 Resellers: {resellers}\n"
        f"📦 Total Orders: {orders}\n"
        f"💰 Total Revenue: ₹{revenue}\n"
        f"🔑 Available Keys: {stock}\n"
        f"💳 Pending Deposits: {pending}",
        reply_markup=admin_menu(),
    )


@bot.message_handler(func=lambda m: m.text == "📦 Orders")
def admin_orders(message):
    if not is_admin(message.from_user.id):
        return

    with db_lock:
        rows = db.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT 20"
        ).fetchall()

    if not rows:
        bot.send_message(message.chat.id, "No orders yet.")
        return

    body = "\n\n".join(
        f"#{row['id']} | User <code>{row['user_id']}</code>\n"
        f"{html.escape(row['product_name'])} — {PLANS[row['duration']]['name']}\n"
        f"Paid: ₹{row['final_price']} | {row['status']}"
        for row in rows
    )
    bot.send_message(message.chat.id, f"📦 <b>Latest Orders</b>\n\n{body}", reply_markup=admin_menu())


@bot.message_handler(func=lambda m: m.text == "💳 Deposit Requests")
def admin_deposits(message):
    if not is_admin(message.from_user.id):
        return

    with db_lock:
        rows = db.execute(
            "SELECT * FROM deposits WHERE status='Pending' ORDER BY id DESC LIMIT 20"
        ).fetchall()

    if not rows:
        bot.send_message(message.chat.id, "No pending deposit requests.")
        return

    for row in rows:
        kb = types.InlineKeyboardMarkup()
        kb.row(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"deposit_ok:{row['id']}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"deposit_no:{row['id']}"),
        )
        bot.send_message(
            message.chat.id,
            f"Deposit #{row['id']}\n"
            f"User: <code>{row['user_id']}</code>\n"
            f"Amount: ₹{row['amount']}\n"
            f"Proof: {html.escape(row['proof'] or '')}",
            reply_markup=kb,
        )


# ---------- BROADCAST ----------

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def broadcast_handler(message):
    if not is_admin(message.from_user.id):
        return

    msg = bot.send_message(message.chat.id, "Send the broadcast message.")
    bot.register_next_step_handler(msg, broadcast_send_step)


def broadcast_send_step(message):
    if not is_admin(message.from_user.id):
        return

    content = message.text or message.caption or ""
    with db_lock:
        users = db.execute("SELECT user_id FROM users").fetchall()

    sent = 0
    failed = 0
    for row in users:
        try:
            bot.send_message(row["user_id"], content)
            sent += 1
        except Exception:
            failed += 1

    bot.send_message(message.chat.id, f"✅ Sent: {sent}\n❌ Failed: {failed}", reply_markup=admin_menu())
    log_admin(message.from_user.id, f"Broadcast sent to {sent}, failed {failed}")


# ---------- SETTINGS ----------

@bot.message_handler(func=lambda m: m.text == "⚙️ Settings")
def settings_handler(message):
    if not is_admin(message.from_user.id):
        return

    bot.send_message(
        message.chat.id,
        "⚙️ <b>Current Settings</b>\n\n"
        f"Product: {PRODUCT_NAME}\n"
        f"Referral Target: {get_setting('referral_target', '15')}\n"
        f"Reseller Discount: {get_setting('reseller_discount', '10')}%\n"
        f"Saved Button Color: {get_setting('button_color', '#22C55E')}\n"
        f"Banner: {BANNER_URL}",
        reply_markup=admin_menu(),
    )


# =========================
# FALLBACK
# =========================

@bot.message_handler(content_types=["text"])
def fallback(message):
    ensure_user(message.from_user)
    if user_is_banned(message.from_user.id):
        return
    bot.send_message(
        message.chat.id,
        "Please select an option from the menu.",
        reply_markup=main_menu(message.from_user.id),
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":
    init_db()
    print("KING OFFICIAL STORE BOT is running...")
    print(f"Owner admins: {sorted(OWNER_ADMINS)}")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
