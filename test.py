import mysql.connector
import datetime
db = mysql.connector.connect(host = "localhost", user = "root", password = "admin", database = "mydb")


query = "SELECT is_student FROM user WHERE username = 'p';"
cur = db.cursor(buffered=True, dictionary=True)
cur.execute(query)
is_student = cur.fetchone()

print(is_student)
