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

    def create_table(self, table_name, columns, foreign_keys=None):
        """
        יוצר טבלה באופן דינמי עם תמיכה במפתח זר

        :param table_name: שם הטבלה (מחרוזת)
        :param columns: מילון של שמות עמודות וסוגי הנתונים שלהן
        :param foreign_keys: רשימה של קשרי מפתח זר (אופציונלי), כל קשר הוא tuple עם (עמודה, טבלת_יעד, עמודת_יעד)
        """
        if not columns:
            raise ValueError("יש לספק לפחות עמודה אחת ליצירת הטבלה")

        # בניית הגדרת עמודות
        columns_definitions = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])

        # בניית הגדרת מפתחות זרים אם יש
        foreign_keys_definitions = ""
        #col = foreign_keys[0]
        #ref_table = foreign_keys[1]
        #ref_col = foreign_keys[2]
        if foreign_keys:
            fk_clauses = [f"FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})"
                          for col, ref_table, ref_col in foreign_keys]
            foreign_keys_definitions = ", " + ", ".join(fk_clauses)

        # בניית שאילתת יצירת טבלה
        create_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_definitions}{foreign_keys_definitions})"

        try:
            self.cursor.execute(create_query)
            self.conn.commit()
            print(f"✅ הטבלה '{table_name}' נוצרה בהצלחה!")
        except sqlite3.OperationalError as err:
            print(f"❌ שגיאה ביצירת הטבלה: {err}")

    def insert(self, table_name, data):
        fields = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))  # "?, ?"

        try:
            insert_query = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"
            self.cursor.execute(insert_query, list(data.values()))  # Pass values safely
            self.conn.commit()
        except sqlite3.IntegrityError as error:
            print(error)

    def select(self, table_name, fields='*', where_condition={}):

        select_query = f"SELECT {fields} FROM {table_name}"

        values = []
        if where_condition != {}:
            conditions = " AND ".join([f"{key}=?" for key in where_condition.keys()])
            select_query += f" WHERE {conditions}"
            values = list(where_condition.values())  # Values for placeholders

        try:
            print(select_query)
            print(values)
            self.cursor.execute(select_query, values)
            results = self.cursor.fetchall()
            return results
        except sqlite3.OperationalError as err:
            print(err)
            return None

    def update(self, table_name, updates, where):
        """
        Updates records in a given table.

        :param table_name: The name of the table to update.
        :param updates: A dictionary of column-value pairs to update.
        :param where: A dictionary specifying the WHERE condition.
        """
        if not updates:
            raise ValueError("No fields to update provided.")

        if not where:
            raise ValueError("WHERE condition is required to avoid updating all rows!")

        # Construct SET clause
        set_clause = ", ".join([f"{key}=?" for key in updates.keys()])
        set_values = list(updates.values())

        # Construct WHERE clause
        where_clause = " AND ".join([f"{key}=?" for key in where.keys()])
        where_values = list(where.values())

        # Full query
        update_query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        values = set_values + where_values  # Combine update values and WHERE values

        print("🔹 Query:", update_query)  # For debugging
        print("🔹 Values:", values)  # For debugging

        self.cursor.execute(update_query, values)
        self.conn.commit()

    def delete(self, table_name, where):
        """
        Deletes records from a given table.
        :param table_name: The name of the table to delete from.
        :param where: A dictionary specifying the WHERE condition.
        """
        if not where:
            raise ValueError("WHERE condition is required to prevent deleting all rows!")

        # Construct WHERE clause
        where_clause = " AND ".join([f"{key}=?" for key in where.keys()])
        where_values = list(where.values())

        # Full query
        delete_query = f"DELETE FROM {table_name} WHERE {where_clause}"

        print("🔹 Query:", delete_query)  # For debugging
        print("🔹 Values:", where_values)  # For debugging

        self.cursor.execute(delete_query, where_values)
        self.conn.commit()

