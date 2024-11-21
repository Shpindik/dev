import os
import tkinter as tk
from tkinter import ttk
import sqlite3
import database

from database import EXPERIENCE_LEVELS


database.DB_NAME = "candidates.db"
database.RESUMES_FOLDER = "resumes"
if os.path.exists(database.DB_NAME):
    os.remove(database.DB_NAME)
if os.path.exists(database.RESUMES_FOLDER):
    for file in os.listdir(database.RESUMES_FOLDER):
        os.remove(os.path.join(database.RESUMES_FOLDER, file))
else:
    os.makedirs(database.RESUMES_FOLDER)

# Генерация базы данных и резюме
database.generate_database_and_resumes()


SALARY_RANGES = [
    "50 000–75 000",
    "75 000–100 000",
    "100 000–150 000",
    "150 000–200 000",
]


def get_experience_priority(experience):
    if experience == EXPERIENCE_LEVELS[0]:
        return 1
    elif experience == EXPERIENCE_LEVELS[1]:
        return 2
    elif experience == EXPERIENCE_LEVELS[2]:
        return 3
    elif experience == EXPERIENCE_LEVELS[3]:
        return 4
    return 0


def fetch_candidates(salary_range=None, experience=None, response=None):
    connection = sqlite3.connect(database.DB_NAME)
    cursor = connection.cursor()

    query = ("SELECT id, first_name, last_name, experience, "
             "desired_salary, response FROM candidates WHERE 1=1")
    params = []

    if salary_range:
        salary_min, salary_max = map(
            int,
            salary_range.replace(" ", "").split("–")
        )
        query += " AND desired_salary BETWEEN ? AND ?"
        params.extend([salary_min, salary_max])
    if experience:
        query += " AND experience = ?"
        params.append(experience)
    if response and response != "Все":
        if response == "Есть отклики":
            query += " AND response IS NOT NULL AND response != ''"
        else:
            query += " AND (response IS NULL OR response = '')"

    cursor.execute(query, params)
    candidates = cursor.fetchall()
    connection.close()
    return candidates


def open_resume(candidate_id):
    connection = sqlite3.connect(database.DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT first_name,last_name FROM candidates WHERE id = ?",
        (candidate_id,))
    candidate = cursor.fetchone()
    if not candidate:
        return
    first_name, last_name = candidate
    resume_path = os.path.join(
        database.RESUMES_FOLDER,
        f"{first_name}_{last_name}.txt"
    )
    resume_window = tk.Toplevel(root)
    resume_window.title("Резюме")
    with open(resume_path, "r", encoding="utf-8") as file:
        resume_text = file.read()

    resume_label = tk.Text(resume_window, wrap="word", width=70, height=10)
    resume_label.insert("1.0", resume_text)
    resume_label.config(state="disabled")
    resume_label.pack(pady=5)

    response_label = tk.Label(resume_window,
                              text="Обратная связь с кандидатом:")
    response_label.pack(anchor="w", padx=10, pady=5)

    response_display = tk.Label(resume_window, text="", wraplength=700,
                                justify="left", font=("Arial", 10, "italic"))
    response_display.pack(pady=5, padx=10)

    response_entry = tk.Text(resume_window, width=50, height=5)
    response_entry.pack(pady=5, padx=10)

    def send_response():
        response_text = response_entry.get("1.0", "end-1c")
        if response_text.strip():
            response_display.config(text="Ваш ответ отправлен кандидату.")
            save_response_to_db(candidate_id, response_text)
            update_candidates()

    send_button = tk.Button(
        resume_window,
        text="Отправить",
        command=send_response
    )
    send_button.pack(pady=10)
    connection.close()


def save_response_to_db(candidate_id, response_text):
    connection = sqlite3.connect(database.DB_NAME)
    cursor = connection.cursor()
    cursor.execute("UPDATE candidates SET response = ? WHERE id = ?",
                   (response_text, candidate_id))
    connection.commit()
    connection.close()
    update_resume(candidate_id, response_text)


def update_resume(candidate_id, response_text):
    connection = sqlite3.connect(database.DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT first_name, last_name, experience, desired_salary, "
        "email FROM candidates WHERE id = ?", (candidate_id,))
    candidate = cursor.fetchone()

    if candidate:
        first_name, last_name, experience, desired_salary, email = candidate

        resume_text = (
            f"Резюме\n\n"
            f"Имя: {first_name} {last_name}\n"
            f"Стаж работы: {experience}\n"
            f"Желаемая зарплата: {desired_salary} рублей\n"
            f"Email: {email}\n"
            f"Ответ: {response_text}\n"
        )

        resume_file_path = os.path.join(
            database.RESUMES_FOLDER, f"{first_name}_{last_name}.txt")
        with open(resume_file_path, "w", encoding="utf-8") as resume_file:
            resume_file.write(resume_text)

    connection.close()


def update_candidates():
    salary_range = salary_var.get()
    experience = experience_var.get()
    response = response_var.get()

    candidates = fetch_candidates(
        salary_range=salary_range if salary_range != "Все" else None,
        experience=experience if experience != "Все" else None,
        response=response if response != "Все" else None
    )

    candidates = sorted(candidates, key=lambda x: x[4])

    if experience != "Все":
        candidates = sorted(candidates, key=lambda x: (
            -get_experience_priority(x[3]),
            x[4]
        ))

    for row in tree.get_children():
        tree.delete(row)

    for candidate in candidates:
        candidate_id, first_name, last_name, experience, \
            desired_salary, response = candidate
        full_name = f"{first_name} {last_name}"

        tree.insert("", "end", values=(
            full_name, experience, desired_salary, response),
                    tags=(candidate_id,))


root = tk.Tk()
root.title("HR Симулятор")
root.protocol("WM_DELETE_WINDOW", lambda: (root.destroy()))

welcome_frame = tk.Frame(root)
welcome_frame.pack(pady=30)

welcome_label = tk.Label(
    welcome_frame,
    text="Привет! Это симулятор кадрового агента по приему на работу\n"
         "Тебе предстоит найти лучшего кандидата",
    font=("Arial", 14),
    justify="center"
)
welcome_label.pack(pady=20)


filter_frame = tk.Frame(root)
filter_frame.pack(pady=10)

tk.Label(filter_frame, text="Желаемая ЗП:").grid(row=0, column=0)
salary_var = tk.StringVar(value="Все")
salary_combo = ttk.Combobox(filter_frame, textvariable=salary_var,
                            values=["Все"] + SALARY_RANGES)
salary_combo.grid(row=0, column=1)

tk.Label(filter_frame, text="Опыт работы:").grid(row=0, column=2)
experience_var = tk.StringVar(value="Все")
experience_combo = ttk.Combobox(filter_frame, textvariable=experience_var,
                                values=["Все"] + list(EXPERIENCE_LEVELS))
experience_combo.grid(row=0, column=3)

tk.Label(filter_frame, text="Ваши ответы:").grid(row=1, column=0)
response_var = tk.StringVar(value="Все")
response_combo = ttk.Combobox(filter_frame, textvariable=response_var,
                              values=["Все", "Ответили", "Без ответа"])
response_combo.grid(row=1, column=1)

filter_button = tk.Button(filter_frame, text="Применить фильтры",
                          command=update_candidates)
filter_button.grid(row=1, column=2)

tree = ttk.Treeview(
    root, columns=("name", "experience", "salary", "response"),
    show="headings",
    height=25
)
tree.heading("name", text="Кандидат")
tree.heading("experience", text="Опыт")
tree.heading("salary", text="Желаемая ЗП")
tree.heading("response", text="Ваш ответ на резюме")


tree.pack(pady=20)


def on_item_double_click(event):
    item = tree.selection()[0]
    candidate_id = tree.item(item, "tags")[0]
    open_resume(candidate_id)


tree.bind("<Double-1>", on_item_double_click)

update_candidates()

root.mainloop()
