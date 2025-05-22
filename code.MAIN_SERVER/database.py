import sqlite3
import logging


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

        # יצירת אובייקט לביצוע שאילתות
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
            print(f"{table_name} created successfully!")
        except sqlite3.OperationalError as err:
            print(f"Error creating table: {err}")

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
            print(f"Integrity error during insert: {err}")
        except sqlite3.OperationalError as err:
            print(f"Operational error during insert: {err}")

    def select(self, table_name, fields='*', where_condition={}, cond="And"):
        """
        Retrieves data from a table based on the specified conditions.

        :param table_name: Name of the table from which to retrieve data. Must be a valid SQL identifier.
        :param fields: The columns to retrieve, either as a comma-separated string or '*' for all columns (default is '*').
        :param where_condition: A dictionary of conditions for the WHERE clause. Keys are column names, and values are the values to compare with. Default is an empty dictionary (no conditions).
        :param cond: The logical operator to combine multiple conditions (default is "AND"). Can also be "OR".

        :return: A list of tuples containing the query results, or None if there was an error.

        This method builds a SELECT query dynamically based on the provided conditions and executes it safely with parameterized queries.
        """
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
            print(f"Error executing SELECT query: {err}")
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
            print("🔹 Query:", update_query)  # For debugging
            print("🔹 Values:", values)  # For debugging

            self.cursor.execute(update_query, values)
            self.conn.commit()
            print(f"✅ Successfully updated records in table {table_name}")

        except sqlite3.OperationalError as err:
            print(f"❌ SQLite OperationalError: {err}")
        except sqlite3.IntegrityError as err:
            print(f"❌ SQLite IntegrityError: {err}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

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
            print("🔹 Query:", delete_query)  # For debugging
            print("🔹 Values:", where_values)  # For debugging

            self.cursor.execute(delete_query, where_values)
            self.conn.commit()
            print(f"✅ Successfully deleted records from table {table_name}")

        except sqlite3.OperationalError as err:
            print(f"❌ SQLite OperationalError: {err}")
        except sqlite3.IntegrityError as err:
            print(f"❌ SQLite IntegrityError: {err}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

