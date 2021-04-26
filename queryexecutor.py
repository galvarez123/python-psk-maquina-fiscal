import mysql.connector as connection
import configparser as parser
#from pathlib import Path
import os
import logging


config_file = parser.ConfigParser()
#p = Path(os.path.dirname(__file__)).parent
config_file.read('prueba.conf')


DB_HOST = config_file.get('PRODUCCION', 'HOST')
DB_USER = config_file.get('PRODUCCION', 'USER')
DB_PASS = config_file.get('PRODUCCION', 'PASS')
DB_NAME = config_file.get('PRODUCCION', 'NAME')
print(DB_HOST)
print(DB_NAME)

def run_query(query):
    logging.info(query)
    print(query)
    conn = connection.MySQLConnection(user=DB_USER, password=DB_PASS, host=DB_HOST, database=DB_NAME,
                           charset='latin1',                           use_unicode=True

                           )  # Conectar a la base de datos
    #encode = "utf-8"
    cursor = conn.cursor()  # Crear un cursor

    cursor.execute(query)  # Ejecutar una consulta
    if query.upper().startswith('SELECT'):
        data = ()
        row = cursor.fetchone()
        while row is not None:
            data += row
            row = cursor.fetchone()
    else:
        conn.commit()
        data = cursor.rowcount
    cursor.close()
    conn.close()
    print(data)
    return data




def get_conection():


    conn = connection.MySQLConnection(user= DB_USER , password = DB_PASS , host=DB_HOST  ,database=DB_NAME )  # Conectar a la base de datos
    return conn