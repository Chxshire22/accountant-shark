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
    chatID: int = update.effective_chat.id
    currentUsername: str = update.effective_user.username
    currentUserID: int = update.effective_user.id

    user_search_sql = "SELECT * FROM Users WHERE user_id=?;"
    user_search = cursor.execute(user_search_sql,(currentUserID,))
    if user_search.fetchone() is None:
        sql = "INSERT INTO Users (user_id, username) VALUES (?,?);"
        cursor.execute(sql, (currentUserID, currentUsername,))

    chat_search_sql = "SELECT * FROM Groups WHERE group_id=?;"
    chat_search = cursor.execute(chat_search_sql, (chatID,))
    if chat_search.fetchone() is None:
        sql = "INSERT INTO Groups (group_id) VALUES (?);"
        cursor.execute(sql, (chatID,))
    
    user_groups_search_sql = "SELECT * FROM User_Groups WHERE user_id=? AND group_id=?;"
    user_groups_search = cursor.execute(user_groups_search_sql, (currentUserID,chatID,))
    if user_groups_search.fetchone() is None:
        sql = "INSERT INTO User_Groups (user_id,group_id) VALUES (?, ?);"
        cursor.execute(sql, (currentUserID,chatID,))
        connection.commit()
        await update.message.reply_text(f"@{currentUsername}'s record for this group is created.")
    else:
        await update.message.reply_text("Your record for this chat is already created, you don't have to do that.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
What do I do?  I record payments made by users, for their friends in the group chat.

Paid for your friend/s? - 
Send me the information in this format: 'I paid $89 for @user1 @user2 @user3.'
This will record the amount spent, and split it between the different users.

Got paid what you're owed? -
Send me this, "@user paid me $X" 
I'll check if they exist, owe you that much or more, then deduct it from the balance.
The debt is cleared once the debt is 0. 

Not sure how much you owe? -
Send me this, "How much do I owe?"
I'll tell you who you owe and how much.

Not sure who owes you? -
Send me this, "Who owes me?"
I'll tell you who owes you and how much. 

want to build useful bots? connect with us on https://forum.bladerunner.net
        """
    )


# Responses


# need to pass groupchat-id, current user-id,
def handle_response(text: str, chatID, currentUsername, currentUserID):
    processed: str = text.lower()
    if "hello" in processed:
        hello_str = (
            f"chat ID: {chatID}\nUsername: @{currentUsername}\nUserID: {currentUserID}"
        )
        return hello_str
    if "i paid" in processed:
        return "your payment was recorded."
    if "paid me" in processed:
        return "okay, debt cleared"
    if "how much do i owe" in processed:
        return "you owe ..."
    if "owes me" in processed:
        return "this user owes you"
    return "I don't understand you, send 'help' for instructions on how to interact with me"


# messages should be parsed in handle_mesage function
# the functions should produce their own strings as a feedback, incl errors to users. 
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    chatID: int = update.effective_chat.id
    currentUsername: str = update.effective_user.username
    currentUserID: int = update.effective_user.id

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    print(f"{currentUsername}")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            # parse the message text 
            # once message text is parsed, find out whether to pass info into payment creation, debt payment, table lookup for debts owing or debts owed. 
            response: str = handle_response(
                new_text, chatID, currentUsername, currentUserID
            )
        else:
            return
    else:
        response: str = handle_response(text, chatID, currentUsername, currentUserID)

    print("BOT:", response)
    await update.message.reply_text(response)


# Server side errors printing.
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


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


# Business logic for payment records.
def paid_for_group():
    return


def received_payment():
    return


def debts():
    return


def owed():
    return


# <leader>xx shows all the linting issues...
#TODO: create function to register users into the db. DONE
#TODO: create function to register group into the db. DONE
#TODO: create function to POST new debt
#TODO: create function to PUT/UPDATE debt record of one user against another. 
#TODO: create function to GET debts owed to user.
#TODO: create function to GET debts owed to others.

