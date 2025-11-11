import math
import os

import sqlite3
from dotenv import load_dotenv
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import sql_commands as sqlcmds


load_dotenv()


# Constants
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_USERNAME = "@AccountantSharkbot"
DB_CONNECTION = sqlite3.connect("tele_shark.db")
DB_CURSOR = DB_CONNECTION.cursor()
HELP_PATH = os.path.join("resources", "help.txt")
LIMITS_PATH = os.path.join("resources", "limits.txt")


# Functions
def main():
	app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
	app.add_handler(CommandHandler("start", start_command))
	app.add_handler(CommandHandler("help", help_command))
	app.add_handler(CommandHandler("register", register_command))
	app.add_handler(CommandHandler("limitations", limitations_command))
	app.add_handler(MessageHandler(filters.TEXT, handle_message))
	app.add_error_handler(error)
	app.run_polling(poll_interval=3)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Add me to a group chat, give me admin privileges so I can receive and send texts.\nIMPORTANT - make sure that everyone participating registers with '/register'\nUse '/help' to learn how to use me."
    )


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id: int = update.effective_chat.id
    current_username: str = update.effective_user.username
    current_user_id: int = update.effective_user.id

    if current_username == "None":
        await update.message.reply_text("I can't work with username 'None'. Sorry.")

    user_search = DB_CURSOR.execute(sqlcmds.SEARCH_BY_USER_ID, (current_user_id,))
    if user_search.fetchone() is None:
        CURDB_CURSORSOR.execute(
            sqlcmds.INSERT_USERNAME_AND_USER_ID,
            (
                current_user_id,
                current_username,
            ),
        )

    chat_search = DB_CURSOR.execute(sqlcmds.SEARCH_BY_GROUP_ID, (chat_id,))
    if chat_search.fetchone() is None:
        DB_CURSOR.execute(
        	sqlcmds.INSERT_GROUP_ID, 
        	(chat_id,)
        )

    user_groups_search = DB_CURSOR.execute(
        sqlcmds.SEARCH_BY_GROUP_ID_AND_USER_ID,
        (
            current_user_id,
            chat_id,
        ),
    )
    if user_groups_search.fetchone() is None:
        DB_CURSOR.execute(
            sqlcmds.INSERT_USER_ID_AND_GROUP_ID,
            (
                current_user_id,
                chat_id,
            ),
        )
        DB_CONNECTION.commit()
        await update.message.reply_text(
            f"@{current_username}'s record for this group is created."
        )
    else:
        await update.message.reply_text(
            "Your record for this chat is already created, you don't have to do that."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(HELP_PATH, "r") as msg:
    	await update.message.reply_text(msg.read())


async def limitations_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(LIMITS_PATH, "r") as msg:
    	await update.message.reply_text(msg.read())


# Business logic for payment records.
# English def clarifications: Payor in DB means someone who pays. Debtee means someone who a debt is owed to. So if someone paid for the group he is the Payor and also the Debtee.
def paid_for_group(data):
    text_list: list[str] = data["text"].split()

    amount_paid: float = None
    debtors: list[str] = []
    debtors_id: list[int] = []

    # This loop extracts keywords from the text sent by the user to extract useful info.
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

    for debtor in debtors:
        search_debtor_res = DB_CURSOR.execute(sqlcmds.SEARCH_BY_USERNAME, (debtor,))
        parsed_res = search_debtor_res.fetchone()
        print(f"PARSED RESPONSE, SEARCH OF DEBTOR: {parsed_res}")
        if parsed_res is None:
            return "One of these debtors aren't registered. \nWhat did I say about registering?\nGet them to register."
        else:
            debtors_id.append(parsed_res[0])

    for debtor_id in debtors_id:
        DB_CURSOR.execute(
            sqlcmds.INSERT_DEBT,
            (
                int(data["current_user_id"]),
                debtor_id,
                int(data["chat_id"]),
                amount_for_each,
            ),
        )

    print(amount_paid)
    print(debtors)
    print(f"Amount for each: {amount_for_each}")
    DB_CONNECTION.commit()
    return f"I've recorded the payment."


def received_payment(data):
    text_list: list[str] = data["text"].split()
    debtor_username: str = None
    debtor_id: int = None
    debt_paid: float = None
    debtee_username: str = data["current_username"]
    debt_balance: float = None

    for text in text_list:
        if text.startswith("@"):
            debtor_username = text[1:]
        if text.startswith("$"):
            debt_paid = round(float(text[1:]), 2)

    # Get debtor user_id
    debtor_id_search_execute = DB_CURSOR.execute(
    	sqlcmds.SEARCH_BY_GROUP_AND_USERNAME, 
    	(debtor_username,)
    )
    debtor_id_search_res = debtor_id_search_execute.fetchone()
    if debtor_id_search_res is None:
        return f"@{debtor_username} does not exist."

    debtor_id = debtor_id_search_res[0]
    print(debtor_id)

    # Check the debt record, and the amount.
    debt_balance_execute = DB_CURSOR.execute(
        sqlcmds.GET_DEBT_BALANCE,
        (
            data["current_user_id"],
            debtor_id,
            debtor_id,
            data["current_user_id"],
        ),
    )
    curr_debt_balance_res = debt_balance_execute.fetchone()
    curr_balance: int = curr_debt_balance_res[0]
    print(f"CURRENT BALANCE: {curr_balance}")

    # Create payment record of debtor (as payor) to debtee (as payee)
    if curr_balance == 0:
        return f"@{debtor_username} doesn't even owe you money tf?"
    if debt_paid > curr_balance:
        return f"Can you bffr, @{debtor_username}'s debt to you is ${curr_balance} which is lower than ${debt_paid}.\nAre you trying to error me out?"
    insert_debt_payment_execute = DB_CURSOR.execute(
        sqlcmds.INSERT_PAYMENT,
        (
            debtor_id,
            int(data["current_user_id"]),
            int(data["chat_id"]),
            debt_paid,
        ),
    )
    DB_CONNECTION.commit()

    debt_balance_execute = DB_CURSOR.execute(
        sqlcmds.GET_DEBT_BALANCE,
        (
            data["current_user_id"],
            debtor_id,
            debtor_id,
            data["current_user_id"],
        ),
    )
    new_debt_balance_res = debt_balance_execute.fetchone()
    new_balance: int = new_debt_balance_res[0]
    print(f"NEW BALANCE {new_balance}")
    if new_balance == 0:
        return f"Payment recorded.\n@{debtor_username} has cleared all their debts with you."
    return f"Payment recorded.\n@{debtor_username} now owes you ${new_balance}"


def debts(data):
    get_all_user_debts_execute = DB_CURSOR.execute(
        sqlcmds.GET_USER_DEBTS,
        {
            "current_user_id": int(data["current_user_id"]),
            "group_id": int(data["chat_id"]),
        },
    )
    get_all_user_debts_res = get_all_user_debts_execute.fetchall()

    debts_dict = {}
    for row in get_all_user_debts_res:
        print(f"ROW: {row}")
        row_user_id = row[1]
        print(f"ROW USER ID = {row_user_id}")
        get_usernames = DB_CURSOR.execute(
            f"SELECT username FROM Users WHERE user_id={row_user_id}"
        )
        row_username = get_usernames.fetchone()[0]
        print(row_username)
        debts_dict[row_username] = row[0]
    print(debts_dict)

    response_string_list = []
    for key, value in debts_dict.items():
        if value == 0:
            continue
        elif value < 0:
            value *= -1
            response_string_list.append(f"\n- @{key} owes you ${value}")
        else:
            response_string_list.append(f"\n- You owe ${value} to @{key}")
    if len(response_string_list) == 0:
        return "You have no debts nor does anyone owe you money. \nGrats, choom"

    return f"Here you go:\n{''.join(response_string_list)}"


def parse_message(text, chat_id, current_username, current_user_id):

    text = " ".join(
        word if word.startswith("@") else word.lower() for word in text.split()
    )

    data = {
        "text": text,
        "chat_id": chat_id,
        "current_username": current_username,
        "current_user_id": current_user_id,
    }

    if "hello" in text:
        hello_str: str = (
            # f"chat ID: {chat_id}\nUsername: @{current_username}\nUserID: {current_user_id}"
            f"Hi @{current_username}, what's up what's UUUP \n(I'm not a chatbot - I only record debts)"
        )
        return hello_str
    elif "i paid $" in text:
        create_debt_res = paid_for_group(data)
        return create_debt_res
    elif "paid me" in text:
        pay_debt_res = received_payment(data)
        return pay_debt_res
    elif "check" in text:
        res = debts(data)
        return res
    else:
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

    if TELEGRAM_USERNAME in text and \
    		(message_type == "group" or message_type == "supergroup"):
        text: str = text.replace(TELEGRAM_USERNAME, "").strip()
        response: str = parse_message(
            text, chat_id, current_username, current_user_id
        )
   else:
       return

    print("BOT:", response)
    await update.message.reply_text(response)


# Server side errors printing.
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"\nUpdate {update} caused error {context.error}")


if __name__ == "__main__":
    main()


# <leader>xx shows all the linting issues...
# TODO: create function to register users into the db. DONE
# TODO: create function to register group into the db. DONE
# TODO: create function to POST new debt. DONE
# TODO: create function to PUT/UPDATE debt record of one user against another. DONE
# TODO: create function to GET debts owed to user. DONE
# TODO: create function to GET debts owed to others. DONE
# TODO: need to rename Debts table to Transaction Table. DONE
# TODO: need to fix the ability to pay for and to someone outside of the groupchat.
# TODO: needs refactoring of code, some repeated code, need modularization and documentation
