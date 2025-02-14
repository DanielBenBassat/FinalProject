import sqlite3

"""
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
age INTEGER NOT NULL
);
"""


class DataBase:
    def __init__(self, name):
        self.name = name
        # חיבור למסד הנתונים (אם לא קיים – ייווצר אוטומטית)
        self.conn = sqlite3.connect(self.name)
        # יצירת אובייקט לביצוע שאילתות
        self.cursor = self.conn.cursor()

    def create_table(self, create_query):
        try:
            self.cursor.execute(create_query)
            self.conn.commit()
        except sqlite3.OperationalError as err:
            print(err)

    def insert(self, table_name, data):
        fields = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))  # "?, ?"

        try:
            insert_query = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"
            self.cursor.execute(insert_query, tuple(data.values()))  # Pass values safely
            self.conn.commit()
        except sqlite3.IntegrityError as error:
            print(error)


if __name__ == '_main_':
    db = DataBase('my_db.db')
    query = """
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
age INTEGER NOT NULL
);
"""
    db.create_table(query)
    data1 = {"name": "dani", "age": 17}
    db.insert("users", data1)