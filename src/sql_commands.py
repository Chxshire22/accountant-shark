
# Search Commands
SEARCH_BY_USERNAME = "SELECT * FROM Users WHERE username=?;"
SEARCH_BY_USER_ID = "SELECT * FROM Users WHERE user_id=?;"
SEARCH_BY_GROUP_ID = "SELECT * FROM Groups WHERE group_id=?;"
SEARCH_BY_GROUP_AND_USERNAME = "SELECT * FROM User_Groups WHERE username=?;"
SEARCH_BY_GROUP_ID_AND_USER_ID = "SELECT * FROM User_Groups WHERE user_id=? AND group_id=?;"


# Get Commands
GET_DEBT_BALANCE = "SELECT (COALESCE((SELECT SUM(amount) FROM Transactions WHERE payor_id=? AND payee_id=?),0) - COALESCE((SELECT SUM(amount) from Transactions WHERE payor_id=? AND payee_id=?),0));"
GET_USER_DEBTS = "SELECT COALESCE(debts_table.debts_owing, 0) - COALESCE(debts_paid_table.debts_paid, 0) AS net_balance, COALESCE(debts_table.payor_id, debts_paid_table.payee_id) AS user_id FROM (SELECT payor_id, COALESCE(SUM(amount), 0) AS debts_owing FROM Transactions WHERE payee_id = :current_user_id AND group_id = :group_id GROUP BY payor_id) AS debts_table LEFT JOIN (SELECT payee_id, COALESCE(SUM(amount), 0) AS debts_paid FROM Transactions WHERE payor_id = :current_user_id AND group_id = :group_id GROUP BY payee_id) AS debts_paid_table ON debts_table.payor_id = debts_paid_table.payee_id UNION SELECT -COALESCE(debts_paid_table.debts_paid, 0) AS net_balance,debts_paid_table.payee_id AS user_id FROM (SELECT payee_id, COALESCE(SUM(amount), 0) AS debts_paid FROM Transactions WHERE payor_id = :current_user_id AND group_id = :group_id GROUP BY payee_id) AS debts_paid_table LEFT JOIN (SELECT payor_id, COALESCE(SUM(amount), 0) AS debts_owing FROM Transactions WHERE payee_id = :current_user_id AND group_id = :group_id GROUP BY payor_id) AS debts_table ON debts_paid_table.payee_id = debts_table.payor_id WHERE debts_table.payor_id IS NULL;"


# Insert Commands
INSERT_USERNAME_AND_USER_ID = "INSERT INTO Users (user_id, username) VALUES (?,?);"
INSERT_GROUP_ID = "INSERT INTO Groups (group_id) VALUES (?);"
INSERT_USER_ID_AND_GROUP_ID = "INSERT INTO User_Groups (user_id,group_id) VALUES (?, ?);"
INSERT_DEBT = "INSERT INTO Transactions (payor_id, payee_id, group_id, amount) VALUES (?,?,?,?);"
INSERT_PAYMENT = "INSERT INTO Transactions (payor_id, payee_id,group_id,amount) VALUES (?,?,?,?);"

