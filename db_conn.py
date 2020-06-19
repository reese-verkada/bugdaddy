import sqlite3 as sql

class DB:

	def __init__(self):
		#connect to db
		self.conn = sql.connect('db/bugdaddy.db')
		self.conn.execute('pragma foreign_keys=ON')

	def query(self,q,p=()):
		cur = self.conn.cursor()
		cur.execute(q,p)
		return cur.fetchall()
