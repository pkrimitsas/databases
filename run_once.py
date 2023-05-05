import mysql.connector

db = mysql.connector.connect(host = "localhost", user = "root", password = "admin", database = "mydb")
query = "SELECT ISBN, copies FROM book;"
cur = db.cursor(buffered=True, dictionary=True)
cur.execute(query);
res = cur.fetchall()
cur.close()
for book in res:
    query = 'INSERT INTO currently_available(ISBN, current) VALUES (%s, %s);'
    args = (book['ISBN'], book['copies'])
    cur = db.cursor()
    cur.execute(query, args)
    cur.close()
db.commit()
db.close()