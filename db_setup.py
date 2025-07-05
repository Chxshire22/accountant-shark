import sqlite3

connection = sqlite3.connect("tele_shark.db")
cursor = connection.cursor()

drop_user_table = "DROP TABLE IF EXISTS Users"
drop_group_table = "DROP TABLE IF EXISTS Groups"
drop_debt_table = "DROP TABLE IF EXISTS Debts"
drop_user_groups_table = "DROP TABLE IF EXISTS User_Groups"

create_user_table = (
    """CREATE TABLE IF NOT EXISTS Users(user_id INTEGER PRIMARY KEY, username TEXT)"""
)

create_group_table = (
    """CREATE TABLE IF NOT EXISTS Groups(group_id INTEGER PRIMARY KEY)"""
)

create_debt_table = """CREATE TABLE IF NOT EXISTS Debts(debt_id INTEGER PRIMARY KEY,debtee_id INTEGER,debtor_id INTEGER,group_id INTEGER,amount REAL,FOREIGN KEY (debtee_id) REFERENCES Users (user_id),FOREIGN KEY (debtor_id) REFERENCES Users (user_id))"""

create_user_groups_table = """CREATE TABLE IF NOT EXISTS
User_Groups(user_id INTEGER,group_id INTEGER)"""

commands_list = [
    drop_user_table,
    drop_group_table,
    drop_debt_table,
    drop_user_groups_table,
    create_user_table,
    create_group_table,
    create_user_groups_table,
    create_debt_table,
]

print(commands_list)

for command in commands_list:
    cursor.execute(command)
