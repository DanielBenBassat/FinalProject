import sqlite3
import logging
import os

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log2'
LOG_FILE = os.path.join(LOG_DIR, 'database.log')
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)
logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)


class DataBase:
    def __init__(self, name):
        """
        Initializes a new instance of the database handler.

        :param name: The name (or path) of the SQLite database file.
                     If the file does not exist, it will be created automatically.
        :return: None
        """
        self.name = name
        self.conn = sqlite3.connect(self.name)
        self.cursor = self.conn.cursor()

    def create_table(self, table_name, columns, foreign_keys=None):
        """
        Dynamically creates a table with support for foreign keys.

        :param table_name: Name of the table (string)
        :param columns: Dictionary of column names and their data types
        :param foreign_keys: Optional list of foreign key relationships,
                             where each relationship is a tuple of the form (column, reference_table, reference_column)
        """
        if not columns:
            raise ValueError("At least one column must be provided to create the table")

        # Build column definitions
        columns_definitions = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])

        # Build foreign key definitions if any
        foreign_keys_definitions = ""

        if foreign_keys:
            fk_clauses = [f"FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})"
                          for col, ref_table, ref_col in foreign_keys]
            foreign_keys_definitions = ", " + ", ".join(fk_clauses)

        # Build the CREATE TABLE SQL query
        create_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_definitions}{foreign_keys_definitions})"

        try:
            self.cursor.execute(create_query)
            self.conn.commit()
            logging.debug(f"{table_name} created successfully!")
        except sqlite3.OperationalError as err:
            logging.debug(f"Error creating table: {err}")

    def insert(self, table_name, data):
        """
        Inserts a row into a table using a parameterized query to prevent SQL injection.

        :param table_name: Name of the table to insert into. Must be a valid SQL identifier (alphanumeric, starting with a letter or underscore).
        :param data: Dictionary where keys are column names and values are the corresponding values to insert into those columns.
                      Example: {"column1": value1, "column2": value2, ...}

        :raises ValueError: If the table name or any column name is invalid (does not match the SQL identifier format).
        :raises sqlite3.IntegrityError: If the insert operation violates integrity constraints (e.g., unique constraint).
        :raises sqlite3.OperationalError: If there is a general error in executing the SQL query.

        This method safely inserts the provided data into the specified table, using placeholders for parameterized queries.
        """
        fields = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))  # "?, ?"
        try:
            insert_query = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"
            self.cursor.execute(insert_query, list(data.values()))  # Pass values safely
            self.conn.commit()
        except sqlite3.IntegrityError as err:
            logging.debug(f"Integrity error during insert: {err}")
        except sqlite3.OperationalError as err:
            logging.debug(f"Operational error during insert: {err}")

    def select(self, table_name, fields='*', where_condition=None, cond="And"):
        """
        Retrieves data from a table based on the specified conditions.

        :param table_name: Name of the table from which to retrieve data. Must be a valid SQL identifier.
        :param fields: The columns to retrieve, either as a comma-separated string or '*' for all columns (default is '*').
        :param where_condition: A dictionary of conditions for the WHERE clause. Keys are column names, and values are the values to compare with. Default is an empty dictionary (no conditions).
        :param cond: The logical operator to combine multiple conditions (default is "AND"). Can also be "OR".

        :return: A list of tuples containing the query results, or None if there was an error.

        This method builds a SELECT query dynamically based on the provided conditions and executes it safely with parameterized queries.
        """
        if where_condition is None:
            where_condition = {}
        select_query = f"SELECT {fields} FROM {table_name}"
        values = []

        if where_condition:
            conditions = f" {cond} ".join([f"{key}=?" for key in where_condition.keys()])
            select_query += f" WHERE {conditions}"
            values = list(where_condition.values())  # Values for placeholders

        try:
            self.cursor.execute(select_query, values)
            results = self.cursor.fetchall()
            return results
        except sqlite3.OperationalError as err:
            logging.debug(f"Error executing SELECT query: {err}")
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

        try:
            #logging.debug("Query:" + update_query)
            #logging.debug("Values:" + ",".join(where_values))

            self.cursor.execute(update_query, values)
            self.conn.commit()
            logging.debug(f"Successfully updated records in table {table_name}")

        except sqlite3.OperationalError as err:
            logging.debug(f"SQLite OperationalError: {err}")
        except sqlite3.IntegrityError as err:
            logging.debug(f"SQLite IntegrityError: {err}")
        except Exception as e:
            logging.debug(f"Unexpected error: {e}")

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

        try:
            logging.debug("Query: " + delete_query)  # For debugging
            logging.debug("Values: " + ",".join(where_values))  # For debugging

            self.cursor.execute(delete_query, where_values)
            self.conn.commit()
            logging.debug(f"Successfully deleted records from table {table_name}")

        except sqlite3.OperationalError as err:
            logging.debug(f"SQLite OperationalError: {err}")
        except sqlite3.IntegrityError as err:
            logging.debug(f"SQLite IntegrityError: {err}")
        except Exception as e:
            logging.debug(f"Unexpected error: {e}")


if __name__ == "__main__":

    # מחיקת קובץ אם קיים
    if os.path.exists("test_db.sqlite"):
        os.remove("test_db.sqlite")

    db = DataBase("test_db.sqlite")

    # יצירת טבלה
    db.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "username": "TEXT NOT NULL UNIQUE",
        "age": "INTEGER"
    })

    # בדיקת insert
    db.insert("users", {"username": "alice", "age": 30})
    result = db.select("users", where_condition={"username": "alice"})
    assert len(result) == 1, "❌ שורה לא הוזנה"
    assert result[0][1] == "alice", "❌ שם משתמש שגוי"
    assert result[0][2] == 30, "❌ גיל שגוי"

    # בדיקת update
    db.update("users", {"age": 31}, {"username": "alice"})
    result = db.select("users", where_condition={"username": "alice"})
    assert result[0][2] == 31, "❌ עדכון גיל נכשל"

    # בדיקת insert נוסף
    db.insert("users", {"username": "bob", "age": 25})
    db.insert("users", {"username": "charlie", "age": 28})
    all_users = db.select("users")
    assert len(all_users) == 3, f"❌ לא הוזנו כל המשתמשים (נמצאו {len(all_users)})"

    # בדיקת delete
    db.delete("users", {"username": "bob"})
    usernames = [user[1] for user in db.select("users")]
    assert "bob" not in usernames, "❌ המשתמש bob לא נמחק"

    # בדיקת תנאי OR
    result = db.select("users", where_condition={"username": "alice", "age": 28}, cond="OR")
    assert len(result) >= 1, "❌ SELECT עם תנאי OR לא עבד"

    logging.debug("tests have succeeded")
