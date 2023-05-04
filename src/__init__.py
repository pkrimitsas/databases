from flask import Flask
import mysql.connector

app = Flask(__name__)

app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = 'admin'
app.config["MYSQL_DB"] = 'mydb'
app.config["SECRET_KEY"] = 'test1'

db = mysql.connector.connect(host = "localhost", user = "root", password = "admin", database = "mydb")

from src import routing