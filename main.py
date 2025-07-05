import math
import sqlite3
from typing import Final

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# TELEGRAM
TOKEN: Final = "7691516733:AAF8xN3UuK55jte-Yv1mbRilgxzUwNcd9rE"
BOT_USERNAME: Final = "@AccountantSharkbot"

# DB Connection
connection = sqlite3.connect("tele_shark.db")
cursor = connection.cursor()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I start automatically, but make sure that everyone participating registers with '/register'\nUse '/help' to learn how to use me."
    )


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id: int = update.effective_chat.id
    current_username: str = update.effective_user.username
    current_user_id: int = update.effective_user.id

    user_search_sql = "SELECT * FROM Users WHERE user_id=?;"
    user_search = cursor.execute(user_search_sql, (current_user_id,))
    if user_search.fetchone() is None:
        sql = "INSERT INTO Users (user_id, username) VALUES (?,?);"
        cursor.execute(
            sql,
            (
                current_user_id,
                current_username,
            ),
        )

    chat_search_sql = "SELECT * FROM Groups WHERE group_id=?;"
    chat_search = cursor.execute(chat_search_sql, (chat_id,))
    if chat_search.fetchone() is None:
        sql = "INSERT INTO Groups (group_id) VALUES (?);"
        cursor.execute(sql, (chat_id,))

    user_groups_search_sql = "SELECT * FROM User_Groups WHERE user_id=? AND group_id=?;"
    user_groups_search = cursor.execute(
        user_groups_search_sql,
        (
            current_user_id,
            chat_id,
        ),
    )
    if user_groups_search.fetchone() is None:
        sql = "INSERT INTO User_Groups (user_id,group_id) VALUES (?, ?);"
        cursor.execute(
            sql,
            (
                current_user_id,
                chat_id,
            ),
        )
        connection.commit()
        await update.message.reply_text(
            f"@{current_username}'s record for this group is created."
        )
    else:
        await update.message.reply_text(
            "Your record for this chat is already created, you don't have to do that."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
What do I do?  I record payments made by users, for their friends in the group chat.

Due to Telegram's security measures I need everyone participating to do /register.

Paid for your friend/s? - 
Send me the information in this format: '@AccountantShark I paid $89 for @user1 @user2 @user3.'
This will record the amount spent, and split it between the different users.

Got paid what you're owed? -
Send "@AccountantShark @user paid me $X" 
I'll check if they exist, owe you that much or more, then deduct it from the balance.
The debt is cleared once the debt is 0. 

DO NOT tag me when clearing debt, your debtor will do it as above 

Not sure how much you owe? -
Send "@AccountantShark how much do I owe?"
I'll tell you who you owe and how much.

Not sure who owes you? -
Send "@AccountantShark who owes me?"
I'll tell you who owes you and how much. 

want to build useful bots or contribute to the project? connect with us on https://forum.bladerunners.net
think it can be better? (it can)
well... talk is easy, send patches
        """
    )


# Business logic for payment records.

nums = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def paid_for_group(data):
    print(data["text"].split())
    text_list: list[str] = data["text"].split()

    amount_paid: float = None
    debtors: list[str] = []
    debtors_id: list[int] = []

    # This loop extracts keywords from the text sent by the user to extract useful info.
    #
    for text in text_list:
        if text.startswith("$"):
            amount_paid = round(float(text[1:]), 2)

        if text.startswith("@"):
            debtors.append(text[1:])

    if amount_paid is None:
        return "Yeah...how much tho? Try that again\nLost? Get /help"
    if len(debtors) == 0:
        return "Yeah...for whom tho? Try that again\nLost? Get /help"

    amount_for_each: float = round(amount_paid / len(debtors), 2)

    search_debtor_ids_sql = "SELECT * FROM Users WHERE username=?;"
    for debtor in debtors:
        search_debtor_res = cursor.execute(search_debtor_ids_sql, (debtor,))
        if search_debtor_res is None:
            return "One of these debtors aren't registered. \nWhat did I say about registering?\nGet them to register."
        else:
            debtors_id.append(search_debtor_res[0])

    insert_debt_sql = (
        "INSERT INTO Debts (debtee_id, debtor_id, group_id, amount) VALUES (?,?,?,?);"
    )
    for debtor_id in debtors_id:
        cursor.execute(
            insert_debt_sql,
            (
                data["current_user_id"],
                debtor_id,
                data["chat_id"],
                amount_for_each,
            ),
        )

    print(amount_paid)
    print(debtors)
    print(f"Amount for each: {amount_for_each}")
    return f"You paid {amount_paid}"


def received_payment():
    return


def debts():
    return


def owed():
    return


def parse_message(text, chat_id, current_username, current_user_id):
    if BOT_USERNAME in text:
        text: str = text.replace(BOT_USERNAME, "").strip()
    text: str = text.lower()

    data = {
        "text": text,
        "chat_id": chat_id,
        "current_username": current_username,
        "current_user_id": current_user_id,
    }

    if "hello" in text:
        hello_str: str = (
            f"chat ID: {chat_id}\nUsername: @{current_username}\nUserID: {current_user_id}"
        )
        return hello_str
    if "i paid" in text:
        res = paid_for_group(data)
        # print(f"PROCESSED TEXT: {text}")
        return res
    if "paid me" in text:
        return "okay, debt cleared"
    if "how much do i owe" in text:
        return "you owe ..."
    if "owes me" in text:
        return "this user owes you"
    return "Sorry I don't understand"


# messages should be parsed in handle_mesage function
# the functions should produce their own strings as a feedback, incl errors to users.
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Checks if it is a group chat
    message_type: str = update.message.chat.type

    # Data from the text message
    text: str = update.message.text
    chat_id: int = update.effective_chat.id
    current_username: str = update.effective_user.username
    current_user_id: int = update.effective_user.id

    # Debugging purposes
    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    print(f"{current_username}")

    response: str = parse_message(text, chat_id, current_username, current_user_id)

    print("BOT:", response)
    await update.message.reply_text(response)


# Server side errors printing.
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"\nUpdate {update} caused error {context.error}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # COMMANDS forward slashes for specific commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("register", register_command))

    # MESSAGES
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # ERRORS
    app.add_error_handler(error)

    # POLLING
    print("polling.")
    app.run_polling(poll_interval=3)


# <leader>xx shows all the linting issues...
# TODO: create function to register users into the db. DONE
# TODO: create function to register group into the db. DONE
# TODO: create function to POST new debt
# TODO: create function to PUT/UPDATE debt record of one user against another.
# TODO: create function to GET debts owed to user.
# TODO: create function to GET debts owed to others.
