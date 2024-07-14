import mysql.connector

def get_sql_connection(): 
    try:
        c = mysql.connector.connect(host='localhost', user='root', password='12345', database='gs')
        return c
    except mysql.connector.Error as err:
        print("Error while connecting to MySQL:", err)
        return None

