import sqlite3

connection = sqlite3.connect("tele_shark.db")
cursor = connection.cursor()

drop_user_table = "DROP TABLE IF EXISTS Users"
drop_group_table = "DROP TABLE IF EXISTS Groups"
drop_debt_table = "DROP TABLE IF EXISTS Debts"
drop_transactions_table = "DROP TABLE IF EXISTS Transactions"
drop_user_groups_table = "DROP TABLE IF EXISTS User_Groups"

create_user_table = (
    """CREATE TABLE IF NOT EXISTS Users(user_id INTEGER PRIMARY KEY, username TEXT)"""
)

create_group_table = (
    """CREATE TABLE IF NOT EXISTS Groups(group_id INTEGER PRIMARY KEY)"""
)

create_transactions_table = """CREATE TABLE IF NOT EXISTS Transactions(payment_id INTEGER PRIMARY KEY,payor_id INTEGER,payee_id INTEGER,group_id INTEGER,amount REAL,FOREIGN KEY (payor_id) REFERENCES Users (user_id),FOREIGN KEY (payee_id) REFERENCES Users (user_id))"""

create_user_groups_table = """CREATE TABLE IF NOT EXISTS
User_Groups(user_id INTEGER,group_id INTEGER)"""

commands_list = [
    drop_user_table,
    drop_group_table,
    drop_transactions_table,
    drop_debt_table,
    drop_user_groups_table,
    create_user_table,
    create_group_table,
    create_user_groups_table,
    create_transactions_table,
]

print(commands_list)

for command in commands_list:
    cursor.execute(command)
