import mysql.connector

db = mysql.connector.connect(host = "localhost", user = "root", password = "admin", database = "mydb")


#query = "INSERT INTO review(review_id, ISBN, username, opinion, is_approved) VALUES (1, '001811991-3', 'p', 'tret', 'F');"
#cur = db.cursor()
#cur.execute(query)
#db.commit()
#cur.close()
query = "SELECT review_id FROM review ORDER BY review_id DESC;"
cur = db.cursor()
cur.execute(query)
res = cur.fetchone()
cur.close()
if res is None:
    print("res is none")
else:
    print(res[0])