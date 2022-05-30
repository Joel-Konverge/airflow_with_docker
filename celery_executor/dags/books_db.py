from airflow.models import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import json


from datetime import datetime
import os
import pandas as pd
import sqlite3

dag_path=os.getcwd()

default_args={"start_date":datetime(2022,5,5)}


def _process_books(ti):
    books=ti.xcom_pull(task_ids=["get_books"])
    if not books:
        raise Exception("Book not found")
    data=books[0]
    books_list=[]
    for i in data["books"]:
        books_list.append({"Book Title":i["title"],"ISBN No.":i["isbn13"],"Price":i["price"]})
    return books_list


def _save_books(ti):
    books_data=ti.xcom_pull(task_ids=["process_books"])
    if not books_data:
        raise Exception("Books not found")
    for i in books_data:
        df=pd.DataFrame(i)
        df.to_csv(f"{dag_path}/data/books_data.csv",index=False,mode='w',header=True)    


def _store_books():
    conn=sqlite3.connect("/usr/local/airflow/db/airflow.db")
    c=conn.cursor()
    c.execute('''
                CREATE TABLE IF NOT EXISTS books_db(
                    book_title TEXT NOT NULL,
                    isbn_no INTEGER NOT NULL,
                    price INTEGER NOT NULL
                    );
                ''')
    records=pd.read_csv(f"{dag_path}/data/books_data.csv")
    records.to_sql('books_db',conn,if_exists='replace',index=False)


with DAG(dag_id="book_db",schedule_interval="@daily",default_args=default_args,catchup=False) as dag:
    check_api=HttpSensor(
        task_id="check_api",
        http_conn_id="book_api",
        endpoint="new"
    )

    get_books=SimpleHttpOperator(
        task_id="get_books",
        http_conn_id="book_api",
        endpoint="new",
        method='GET',
        response_filter=lambda response: json.loads(response.text),
        log_response=True
    )

    process_books=PythonOperator(
        task_id="process_books",
        python_callable=_process_books
    )

    save_books=PythonOperator(
        task_id="save_books",
        python_callable=_save_books
    )

    store_books=PythonOperator(
        task_id="store_books",
        python_callable=_store_books
    )

check_api >> get_books >> process_books >> save_books >> store_books