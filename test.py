import mysql.connector

db = mysql.connector.connect(host = "localhost", user = "root", password = "admin", database = "mydb")

query = "DELETE FROM reservations;"
cur = db.cursor()
cur.execute(query)
db.commit()
cur.close()