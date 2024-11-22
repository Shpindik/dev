import os
import atexit
import random
import sqlite3


from database import EXPERIENCE_LEVELS, TECH_STACK

VACANCIES_DB_NAME = "vacancies.db"
SALARY_RANGES = [
    "До 75 000",
    "До 100 000",
    "До 150 000",
    "До 200 000",
]


def cleanup():
    if os.path.exists(VACANCIES_DB_NAME):
        os.remove(VACANCIES_DB_NAME)


atexit.register(cleanup)


def generate_random_stack():
    languages = random.choice(TECH_STACK["languages"])
    frameworks = random.choice(TECH_STACK["frameworks"])
    apis = random.choice(TECH_STACK["apis"])
    return f"{languages}, {frameworks}, {apis}"


def generate_vacancies():
    connection = sqlite3.connect(VACANCIES_DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            salary_range TEXT NOT NULL,
            experience TEXT NOT NULL,
            tech_stack TEXT NOT NULL
        )
    """)

    cursor.execute("DELETE FROM vacancies")

    num_vacancies = random.randint(3, 5)
    for _ in range(num_vacancies):
        salary_range = random.choice(SALARY_RANGES)
        experience = random.choice(EXPERIENCE_LEVELS)
        tech_stack = generate_random_stack()
        title = f"Разработчик {tech_stack.split(', ')[0]}"
        cursor.execute("INSERT INTO vacancies (title, salary_range, \
                       experience, tech_stack) VALUES (?, ?, ?, ?)",
                       (title, salary_range, experience, tech_stack))

    connection.commit()
    connection.close()
    print(f"Сгенерировано {num_vacancies} вакансий.")


generate_vacancies()
