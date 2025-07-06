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

this was built over the weekend without the help of AI.
see /limitations
think it can be better? (it can)
well... talk is easy, send patches
        """
    )


async def limitations_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
I have serious limitations.

For example, telegram users can only tag their friends via usernames "eg @user1"
But usernames are not unique, and are not immutable. 

User IDs are immutable and unique, but discord users don't know their friends' user ID and it is not intuitive to use. 

At the moment there are syntax issues which I ignore. You can input the wrong records easily.

Expect bugs. Report them on my AccountantShark thread on https://forum.bladerunners.net
            """
    )


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

    search_debtor_sql = "SELECT * FROM Users WHERE username=?;"
    for debtor in debtors:
        search_debtor_res = cursor.execute(search_debtor_sql, (debtor,))
        parsed_res = search_debtor_res.fetchone()
        print(f"PARSED RESPONSE, SEARCH OF DEBTOR: {parsed_res}")
        if parsed_res is None:
            return "One of these debtors aren't registered. \nWhat did I say about registering?\nGet them to register."
        else:
            debtors_id.append(parsed_res[0])

    insert_debt_sql = "INSERT INTO Transactions (payor_id, payee_id, group_id, amount) VALUES (?,?,?,?);"
    for debtor_id in debtors_id:
        cursor.execute(
            insert_debt_sql,
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
    connection.commit()
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
    debtor_id_search_sql = "SELECT * FROM Users WHERE username=?;"
    debtor_id_search_execute = cursor.execute(debtor_id_search_sql, (debtor_username,))
    debtor_id_search_res = debtor_id_search_execute.fetchone()
    if debtor_id_search_res is None:
        return f"@{debtor_username} does not exist."

    debtor_id = debtor_id_search_res[0]
    print(debtor_id)

    # Check the debt record, and the amount.
    debt_balance_sql = "SELECT (COALESCE((SELECT SUM(amount) FROM Transactions WHERE payor_id=? AND payee_id=?),0) - COALESCE((SELECT SUM(amount) from Transactions WHERE payor_id=? AND payee_id=?),0));"

    debt_balance_execute = cursor.execute(
        debt_balance_sql,
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
    insert_debt_payment_sql = "INSERT INTO Transactions (payor_id, payee_id,group_id,amount) VALUES (?,?,?,?);"
    insert_debt_payment_execute = cursor.execute(
        insert_debt_payment_sql,
        (
            debtor_id,
            int(data["current_user_id"]),
            int(data["chat_id"]),
            debt_paid,
        ),
    )
    connection.commit()

    debt_balance_execute = cursor.execute(
        debt_balance_sql,
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
    # Get all transactions other users made to user where groupid is chatid and payeeid is userid, sum amount grouped by other usersid, deduct all transactions made to other users where payorid is userid, groupid is chatid, and sum amount grouped by other usersid.
    get_all_user_debts_sql = "SELECT * FROM Transactions WHERE payee_id=?"
    get_all_user_debts_execute = cursor.execute(
        get_all_user_debts_sql, (int(data["current_user_id"]),)
    )

    return "You owe this much: $10000000"


def owed():
    # Check Debts table for all debtee_id == current_user_id group by debtor_id AND group_id
    # If none, return that the user has no debts owed
    # Create list of dicts with each dict name as debtor_username and one kv pair debt: int.
    # Create a string to input the list of debtors and debt owed
    # Return that string
    return


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
            f"chat ID: {chat_id}\nUsername: @{current_username}\nUserID: {current_user_id}"
        )
        return hello_str
    elif "i paid $" in text:
        create_debt_res = paid_for_group(data)
        return create_debt_res
    elif "paid me" in text:
        pay_debt_res = received_payment(data)
        return pay_debt_res
    elif "how much do i owe" in text:
        res = debts(data)
        return res
    elif "owes me" in text:
        return "this user owes you"
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

    if message_type == "group" or message_type == "supergroup":
        if BOT_USERNAME in text:
            text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = parse_message(
                text, chat_id, current_username, current_user_id
            )
        else:
            return
    else:
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
    app.add_handler(CommandHandler("limitations", limitations_command))

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
# TODO: create function to POST new debt. DONE
# TODO: create function to PUT/UPDATE debt record of one user against another. DONE
# TODO: create function to GET debts owed to user.
# TODO: create function to GET debts owed to others.
# TODO: need to rename Debts table to Transaction Table.
