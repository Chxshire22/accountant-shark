import sqlite3

connection = sqlite3.connect("tele_shark.db")
cursor = connection.cursor()

def test():
    user_search = cursor.execute(f"SELECT * FROM Users WHERE user_id='chxsire22';")
    if user_search.fetchone() is None:
        cursor.execute(f"INSERT INTO Users (user_id, username) VALUES (11111,'chxshire22');")

    chat_search = cursor.execute(f"SELECT * FROM Groups WHERE group_id='22222222';")
    if chat_search.fetchone() is None:
        cursor.execute(f"INSERT INTO Groups (group_id) VALUES (22222222);")
    user_groups_search = cursor.execute(f"SELECT * FROM User_Groups WHERE user_id=11111 AND group_id=22222222;")
    if user_groups_search.fetchone() is None:
        cursor.execute(f"INSERT INTO User_Groups (user_id,group_id) VALUES (11111, 22222222);")
        # need to commit transaction to make sure the update takes 
        connection.commit()
test()
