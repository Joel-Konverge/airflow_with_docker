from airflow.models import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup


from datetime import datetime

default_args={"start_date":datetime(2022,5,5)}

with DAG('trigger_rule',schedule_interval='@daily',default_args=default_args,catchup=False) as dag:
    task_1=BashOperator(
        task_id='task_1',
        bash_command='exit 0'
    )

    with TaskGroup('parallel_tasks1') as parallel_tasks1:
        task_2=BashOperator(
            task_id='task_2',
            bash_command="sleep 1",
            trigger_rule='all_success'

        )

        task_3=BashOperator(
            task_id='task_3', 
            bash_command="sleep 1",           
            trigger_rule='all_failed'
        )
                
    task_4=BashOperator(
        task_id='task_4',
        bash_command="sleep 1",
        trigger_rule='none_skipped'
    )

    with TaskGroup('parallel_tasks2') as parallel_tasks2:
        task_5=BashOperator(
            task_id='task_5',
            bash_command='sleep 1',
            trigger_rule='one_failed'

        )

        task_6=BashOperator(
            task_id='task_6',
            bash_command='sleep 1',
            trigger_rule='none_failed'
        )

    task_7=BashOperator(
    task_id='task_7',
    bash_command="sleep 1",
    trigger_rule='all_done'
    )

           


    task_1 >> parallel_tasks1 >> task_4 >> parallel_tasks2 >> task_7
