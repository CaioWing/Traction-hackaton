from collections import namedtuple
from typing import List, Tuple
from datetime import datetime
from random import choice

MAX_WORKLOAD = 100

class Employee:
    def __init__(self, id, name, experience, current_workload=0):
        self.id = id
        self.name = name
        self.experience = experience
        self.current_workload = current_workload
        self.history: List[datetime.date] = []  # Store history of assigned tasks

    def add_workload(self, workload, task_name):
        self.current_workload += workload
        self.history.append((task_name, datetime.now().date()))

    def reset_workload(self):
        self.current_workload = 0

class Task:
    def __init__(self, name, workload, required_experience: float, date):
        self.name = name
        self.workload = workload
        self.required_experience = required_experience
        self.date = date
    
    def __str__(self) -> str:
        return f'(Task: {self.name}, required experience: {self.required_experience}, limit date: {self.date}).'

def fetch_employees(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, experience, current_workload FROM employees")
    return [Employee(*row) for row in cursor.fetchall()]

def fetch_tasks(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT name, workload, required_experience FROM tasks")
    return [Task(name, workload, required_experience) for name, workload, required_experience in cursor.fetchall()]

def record_history(connection, employee_id, task: Task):
    cursor = connection.cursor()
    cursor.execute("INSERT INTO history (employee_id, task_name, date) VALUES (?, ?, ?)",
                   (employee_id, task.name, task.date))
    connection.commit()
    print(f"{employee_id} history updated. {task} added")

def _is_last_task_done_on_weekend(date: datetime.date) -> bool:
    return datetime.date.weekday > 4

def _select_employees_for_task_by_experience(employees: List[Employee], experience_required: float) -> List[Employee]:
    return [emp for emp in employees if emp.experience >= experience_required]

def _select_employees_under_max_workload(employees: List[Employee], task_workload, max_workload) -> List[Employee]:
    return [emp for emp in employees if emp.current_workload + task_workload < max_workload]


def get_suitable_employees_for_task(employees: List[Employee], task, max_workload: float) -> List[Employee]:
        
    suitable_employees = [emp for emp in _select_employees_under_max_workload(
        _select_employees_for_task_by_experience(employees, task.required_experience),
        task.workload,
        max_workload) ]
    
    for emp in suitable_employees:
        if emp.history:
            if _is_last_task_done_on_weekend(emp.history[-1]): suitable_employees.remove(emp)

    exp_weight = 0.2
    workload_weight = 1 - exp_weight

    return sorted(suitable_employees, key = lambda emp: exp_weight*emp.experience + workload_weight*emp.current_workload)


def optimize_schedule_tasks(employees: List[Employee], tasks: List[Task], max_workload: float) -> List[Tuple[Task, Employee]]:
    
    task_employee = []

    for task in tasks:
        # Get suitable employees based on current_workload and experience
        suitable_employees = get_suitable_employees_for_task(employees, task, max_workload)
        
        if suitable_employees:
            selected_employee = suitable_employees.pop(0)
            task_employee.append((task, selected_employee))
            selected_employee.add_workload(task.workload, task.name)
            print(f"Assigned task '{task.name}' to {selected_employee.name} on {datetime.now().date()}")
    
    return task_employee

if __name__ == '__main__':
    
    num_emp = 100
    max_workload = 100
    exp = [0.5, 0.75, 1]
    wload = [max_workload * choice([0.1, 0.25, 0.5, 0.75, 1]) for _ in range(num_emp)]

    employees = [Employee(i, f'Emp[{i}]', choice(exp)) for i in range(num_emp)]
    tasks = [Task(f'Task[{i}]', max_workload*choice(exp), choice(exp)) for i in range(20)]

    task_employee = optimize_schedule_tasks(employees, tasks, max_workload)
    # record_history(connection, selected_employee.id, task.name)