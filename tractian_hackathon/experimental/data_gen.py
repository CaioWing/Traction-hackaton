from datetime import timedelta, datetime
from random import choice
from employee_scheduler import Employee, Task, optimize_schedule_tasks

NUM_EMPLOYEES = 50
NUM_TASKS = 100
MAX_WORKLOAD = 100

EXPERIENCES = [0.5, 0.75, 1]
TIME_DELTA_DAYS = [i for i in range(30)]

if __name__ == '__main__':

    _percent = [0.1, 0.25, 0.5, 0.75, 1]

    employees = [Employee(i, f'Funcionario[{i}]', choice(EXPERIENCES)) for i in range(NUM_EMPLOYEES)]
    
    tasks = [Task(
        f'Task[{i}]',
        MAX_WORKLOAD*choice(_percent),
        choice(EXPERIENCES),
        datetime.now() + timedelta(days = choice(TIME_DELTA_DAYS))) for i in range(NUM_TASKS)]
    
    tasks_and_respective_employees = optimize_schedule_tasks(employees, tasks, MAX_WORKLOAD)
    print(tasks_and_respective_employees)