import os
import sqlite3
from faker import Faker
import random
import atexit

DB_NAME = "candidates.db"
RESUMES_FOLDER = "resumes"

EXPERIENCE_LEVELS = (
    "без стажа",
    "от 1 года до 3 лет",
    "от 3 до 6 лет",
    "более 6 лет"
)


def cleanup():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    if os.path.exists(RESUMES_FOLDER):
        for file in os.listdir(RESUMES_FOLDER):
            os.remove(os.path.join(RESUMES_FOLDER, file))


atexit.register(cleanup)


def generate_database_and_resumes():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    if os.path.exists(RESUMES_FOLDER):
        for file in os.listdir(RESUMES_FOLDER):
            os.remove(os.path.join(RESUMES_FOLDER, file))
    else:
        os.makedirs(RESUMES_FOLDER)

    fake = Faker("ru_RU")
    fake_en = Faker()
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        middle_name TEXT,
        experience TEXT,
        desired_salary INTEGER,
        email TEXT,
        response TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        response TEXT,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
    )
    """)

    for _ in range(100):
        gender = random.choice(["male", "female"])

        if gender == "male":
            first_name = fake.first_name_male()
            last_name = fake.last_name_male()
            middle_name = fake.middle_name_male()
        else:
            first_name = fake.first_name_female()
            last_name = fake.last_name_female()
            middle_name = fake.middle_name_female()

        experience = random.choice(EXPERIENCE_LEVELS)
        desired_salary = random.randrange(50000, 200001, 5000)
        email = f"{fake_en.user_name()}@example.com"
        response = ""

        cursor.execute("""
        INSERT INTO candidates (
                       first_name,
                       last_name,
                       middle_name,
                       experience,
                       desired_salary,
                       email,
                       response
                    )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            first_name,
            last_name,
            middle_name,
            experience,
            desired_salary,
            email,
            response
        ))

        resume_text = (
            f"Резюме\n\n"
            f"Имя: {first_name} {middle_name} {last_name}\n"
            f"Стаж работы: {experience}\n"
            f"Желаемая зарплата: {desired_salary} рублей\n"
            f"Email: {email}\n"
        )
        with open(os.path.join(
            RESUMES_FOLDER,
            f"{first_name}_{last_name}.txt"
        ), "w", encoding="utf-8") as resume_file:
            resume_file.write(resume_text)

    connection.commit()
    connection.close()
    print("База данных и резюме успешно сгенерированы.")