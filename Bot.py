import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURATION
# =========================

BOT_TOKEN = os.getenv("8836757551:AAH0SKf3pWmFv6434DNcvzibZf3nDTJ--wU")

# Your Telegram admin username
ADMIN_USERNAME = "@TrustSelling_Bot"

PRODUCTS = {
    "android_gmail": {
        "name": "Android Gmail",
        "price": 30,
    },
    "iphone_gmail": {
        "name": "iPhone Gmail",
        "price": 50,
    },
    "facebook": {
        "name": "Facebook Account",
        "price": 10,
    },
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Sell Gmail", callback_data="sell_menu")],
        [InlineKeyboardButton("Sell Facebook Account", callback_data="facebook")],
        [InlineKeyboardButton("Rate", callback_data="rates")],
        [InlineKeyboardButton("My Orders", callback_data="orders")],
        [InlineKeyboardButton("Contact Admin", callback_data="admin")],
    ]

    await update.message.reply_text(
        "Welcome to Gmail Marketing\n\n"
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# SELL MENU
# =========================

async def sell_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Android Gmail — 30 TK", callback_data="android_gmail")],
        [InlineKeyboardButton("iPhone Gmail — 30 TK", callback_data="iphone_gmail")],
        [InlineKeyboardButton("Facebook Account — 10 TK", callback_data="facebook")],
        [InlineKeyboardButton("Back", callback_data="home")],
    ]

    await query.edit_message_text(
        "Select the product you want to sell:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# PRODUCT SELECTION
# =========================

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = query.data
    product = PRODUCTS.get(product_id)

    if not product:
        return

    context.user_data["product"] = product_id

    keyboard = [
        [InlineKeyboardButton("1", callback_data="qty_1"),
         InlineKeyboardButton("5", callback_data="qty_5"),
         InlineKeyboardButton("10", callback_data="qty_10")],
        [InlineKeyboardButton("Custom Quantity", callback_data="custom_qty")],
        [InlineKeyboardButton("Back", callback_data="sell_menu")],
    ]

    await query.edit_message_text(
        f"Product: {product['name']}\n"
        f"Rate: {product['price']} TK each\n\n"
        "Select quantity:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# QUANTITY
# =========================

async def quantity_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quantity = int(query.data.split("_")[1])
    context.user_data["quantity"] = quantity

    await show_order_summary(query, context)


async def custom_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["waiting_quantity"] = True

    await query.edit_message_text(
        "Please type the quantity.\n\n"
        "Example: 25"
    )


async def receive_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_quantity"):
        return

    try:
        quantity = int(update.message.text)

        if quantity <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text("Please enter a valid quantity.")
        return

    context.user_data["quantity"] = quantity
    context.user_data["waiting_quantity"] = False

    await send_order_summary(update, context)


# =========================
# ORDER SUMMARY
# =========================

async def show_order_summary(query, context):
    product_id = context.user_data["product"]
    quantity = context.user_data["quantity"]

    product = PRODUCTS[product_id]
    total = product["price"] * quantity

    keyboard = [
        [InlineKeyboardButton("Confirm Order", callback_data="confirm_order")],
        [InlineKeyboardButton("Cancel", callback_data="sell_menu")],
    ]

    await query.edit_message_text(
        f"Order Summary\n\n"
        f"Product: {product['name']}\n"
        f"Rate: {product['price']} TK\n"
        f"Quantity: {quantity}\n"
        f"Total: {total} TK\n\n"
        "Press Confirm Order to submit.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def send_order_summary(update, context):
    product_id = context.user_data["product"]
    quantity = context.user_data["quantity"]

    product = PRODUCTS[product_id]
    total = product["price"] * quantity

    keyboard = [
        [InlineKeyboardButton("Confirm Order", callback_data="confirm_order")],
        [InlineKeyboardButton("Cancel", callback_data="sell_menu")],
    ]

    await update.message.reply_text(
        f"Order Summary\n\n"
        f"Product: {product['name']}\n"
        f"Rate: {product['price']} TK\n"
        f"Quantity: {quantity}\n"
        f"Total: {total} TK",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# CONFIRM ORDER
# =========================

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user

    product_id = context.user_data.get("product")
    quantity = context.user_data.get("quantity")

    if not product_id or not quantity:
        await query.edit_message_text("Order information not found.")
        return

    product = PRODUCTS[product_id]
    total = product["price"] * quantity

    order_id = f"{user.id}-{int(update.effective_message.date.timestamp())}"

    admin_message = (
        "NEW SELL ORDER\n\n"
        f"Order ID: {order_id}\n"
        f"User: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'No username'}\n"
        f"Telegram ID: {user.id}\n\n"
        f"Product: {product['name']}\n"
        f"Quantity: {quantity}\n"
        f"Rate: {product['price']} TK\n"
        f"Total: {total} TK"
    )

    # Admin notification is sent to the bot admin chat.
    # Set ADMIN_CHAT_ID as an environment variable.
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")

    if admin_chat_id:
        try:
            await context.bot.send_message(
                chat_id=int(admin_chat_id),
                text=admin_message,
            )
        except Exception as e:
            logging.error(f"Admin notification failed: {e}")

    await query.edit_message_text(
        f"Order submitted successfully.\n\n"
        f"Order ID: {order_id}\n"
        f"Product: {product['name']}\n"
        f"Quantity: {quantity}\n"
        f"Total: {total} TK\n\n"
        f"Contact Admin: {ADMIN_USERNAME}"
    )

    context.user_data.setdefault("orders", []).append({
        "order_id": order_id,
        "product": product["name"],
        "quantity": quantity,
        "total": total,
    })


# =========================
# RATES
# =========================

async def rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = "Current Rates\n\n"

    for product in PRODUCTS.values():
        text += f"{product['name']} — {product['price']} TK\n"

    keyboard = [
        [InlineKeyboardButton("Back", callback_data="home")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# MY ORDERS
# =========================

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    orders = context.user_data.get("orders", [])

    if not orders:
        text = "You don't have any orders yet."
    else:
        text = "My Orders\n\n"

        for order in orders[-10:]:
            text += (
                f"Order: {order['order_id']}\n"
                f"Product: {order['product']}\n"
                f"Quantity: {order['quantity']}\n"
                f"Total: {order['total']} TK\n\n"
            )

    keyboard = [
        [InlineKeyboardButton("Back", callback_data="home")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# ADMIN
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Contact Admin", url="https://t.me/TrustSelling_Bot")],
        [InlineKeyboardButton("Back", callback_data="home")],
    ]

    await query.edit_message_text(
        f"Admin: {ADMIN_USERNAME}\n\n"
        "For order-related support, contact the admin.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# HOME
# =========================

async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Sell Gmail", callback_data="sell_menu")],
        [InlineKeyboardButton("Sell Facebook Account", callback_data="facebook")],
        [InlineKeyboardButton("Rate", callback_data="rates")],
        [InlineKeyboardButton("My Orders", callback_data="orders")],
        [InlineKeyboardButton("Contact Admin", callback_data="admin")],
    ]

    await query.edit_message_text(
        "Gmail Marketing\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# CALLBACK ROUTER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "home":
        await home(update, context)

    elif data == "sell_menu":
        await sell_menu(update, context)

    elif data in PRODUCTS:
        await product_selected(update, context)

    elif data.startswith("qty_"):
        await quantity_selected(update, context)

    elif data == "custom_qty":
        await custom_quantity(update, context)

    elif data == "confirm_order":
        await confirm_order(update, context)

    elif data == "rates":
        await rates(update, context)

    elif data == "orders":
        await my_orders(update, context)

    elif data == "admin":
        await admin(update, context)


# =========================
# MAIN
# =========================

def main():
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        raise ValueError(
            "Please set your Telegram BOT_TOKEN first."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity)
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
