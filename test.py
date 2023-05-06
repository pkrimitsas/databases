import mysql.connector
import datetime
db = mysql.connector.connect(host = "localhost", user = "root", password = "admin", database = "mydb")

query = "SELECT * FROM currently_available;"
cur = db.cursor(buffered=True, dictionary=True)
cur.execute(query)
current = cur.fetchall()
cur.close()
for x in current:
    ISBN = x['ISBN']
    copies = x['current']
    query = "SELECT * FROM now_borrowed WHERE ISBN = %s AND is_returned = 'F';"
    cur = db.cursor(buffered=True, dictionary=True)
    args = (ISBN,)
    cur.execute(query, args)
    res = cur.fetchall()
    cur.close()
    diff = copies - len(res)
    query = "UPDATE currently_available SET current = %s WHERE ISBN = %s;"
    args = (diff, ISBN)
    curr = db.cursor()
    curr.execute(query, args)