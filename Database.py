import mysql.connector, Key
from mysql.connector import Error

db_host = "us-cdbr-east-04.cleardb.com"
db_username = "bea2e6c2784c72"
db_name = "heroku_2b5704fd7eefb53"


def create_server_connection(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


# connection = create_server_connection("localhost", "root", Key.pw)

def create_database(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Database created successfully")
    except Error as err:
        print(f"Error: '{err}'")


def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")


# create_database_query = "CREATE DATABASE poweatr"
# create_database(connection, create_database_query)

# connection = create_db_connection("localhost", "root", pw, "meetup_db")
# six = 6
# new_meetup_data = f"""
# INSERT INTO minecraft VALUES
# (DEFAULT, {six})
# """
#
# execute_query(connection, new_meetup_data)
