import os
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import sqlite3
import database
import vacancies

from database import EXPERIENCE_LEVELS, TECH_STACK

database.DB_NAME = "candidates.db"
database.RESUMES_FOLDER = "resumes"
vacancies.VACANCIES_DB_NAME = "vacancies.db"

for db_path in (database.DB_NAME, vacancies.VACANCIES_DB_NAME):
    if os.path.exists(db_path):
        os.remove(db_path)

if os.path.exists(database.RESUMES_FOLDER):
    for file in os.listdir(database.RESUMES_FOLDER):
        os.remove(os.path.join(database.RESUMES_FOLDER, file))
else:
    os.makedirs(database.RESUMES_FOLDER)

database.generate_database_and_resumes()

vacancies.generate_vacancies()

SALARY_RANGES = [
    "50 000–75 000",
    "75 000–100 000",
    "100 000–150 000",
    "150 000–200 000",
]


def fetch_candidates(salary_range=None, experience=None, response=None,
                     languages=None, frameworks=None, apis=None):
    """Получение списка кандидатов из базы данных."""
    connection = sqlite3.connect(database.DB_NAME)
    cursor = connection.cursor()
    query = ("SELECT id, first_name, last_name, experience, "
             "desired_salary, stack, response FROM candidates WHERE 1=1")
    params = []
    if salary_range:
        salary_min, salary_max = map(int,
                                     salary_range.replace(" ", "").split("–"))
        query += " AND desired_salary BETWEEN ? AND ?"
        params.extend([salary_min, salary_max])
    if experience:
        query += " AND experience = ?"
        params.append(experience)
    if response and response != "Все":
        if response == "Ответили":
            query += " AND response IS NOT NULL AND response != ''"
        else:
            query += " AND (response IS NULL OR response = '')"
    for tech_filter, tech_value in zip(["languages", "frameworks", "apis"],
                                       [languages, frameworks, apis]):
        if tech_value:
            query += " AND stack LIKE ?"
            params.append(f"%{tech_value}%")

    cursor.execute(query, params)
    candidates = cursor.fetchall()
    connection.close()
    return candidates


def fetch_vacancies():
    """Получение списка вакансий из базы данных."""
    connection = sqlite3.connect(vacancies.VACANCIES_DB_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT title, experience, salary_range, \
                   tech_stack FROM vacancies")
    vacancies_list = cursor.fetchall()
    connection.close()
    return vacancies_list


def update_candidates():
    """Обновление списка кандидатов."""
    salary_range = salary_var.get()
    experience = experience_var.get()
    response = response_var.get()
    language = languages_var.get()
    framework = frameworks_var.get()
    api = apis_var.get()

    candidates = fetch_candidates(
        salary_range=salary_range if salary_range != "Все" else None,
        experience=experience if experience != "Все" else None,
        response=response if response != "Все" else None,
        languages=language if language != "Все" else None,
        frameworks=framework if framework != "Все" else None,
        apis=api if api != "Все" else None
    )

    for row in candidates_tree.get_children():
        candidates_tree.delete(row)

    for candidate in candidates:
        candidate_id, first_name, last_name, experience, \
            desired_salary, stack, response = candidate
        full_name = f"{first_name} {last_name}"
        candidates_tree.insert(
            "",
            "end",
            values=(full_name, experience, desired_salary, stack, response)
        )
    candidates_tree.bind("<Double-1>", open_resume)


def update_vacancies():
    """Обновление списка вакансий."""
    vacancies = fetch_vacancies()

    for row in vacancies_tree.get_children():
        vacancies_tree.delete(row)

    for vacancy in vacancies:
        title, experience, salary, stack = vacancy
        vacancies_tree.insert(
            "",
            "end",
            values=(title, experience, salary, stack))


def export_resume_to_disk(resume_filename, full_name):
    """Экспорт резюме на диск."""
    from tkinter.filedialog import asksaveasfilename

    save_path = asksaveasfilename(
        initialfile=f"{full_name.replace(' ', '_')}.txt",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if save_path:
        try:
            with open(resume_filename, "r", encoding="utf-8") as src_file:
                content = src_file.read()
            with open(save_path, "w", encoding="utf-8") as dest_file:
                dest_file.write(content)
            messagebox.showinfo("Успех", f"Резюме сохранено в {save_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить резюме: {e}")


def open_resume(event):
    selected_item = candidates_tree.selection()
    if not selected_item:
        return
    candidate = candidates_tree.item(selected_item[0])['values']
    full_name = candidate[0]
    first_name, last_name = full_name.split(" ", 1)

    resume_filename = os.path.join(database.RESUMES_FOLDER,
                                   f"{first_name}_{last_name}.txt")

    if not os.path.exists(resume_filename):
        messagebox.showerror("Ошибка", "Резюме не найдено.")
        return

    with open(resume_filename, "r", encoding="utf-8") as resume_file:
        resume_content = resume_file.read()

    resume_window = tk.Toplevel(root)
    resume_window.title(f"Резюме {full_name}")

    resume_text = tk.Text(resume_window, wrap="word", width=80, height=20)
    resume_text.insert(tk.END, resume_content)
    resume_text.config(state=tk.DISABLED)
    resume_text.pack(padx=10, pady=10)

    acceptance_checkbox = tk.Checkbutton(
        resume_window,
        text="Принять на работу",
        variable=acceptance_var)
    acceptance_checkbox.pack(padx=10, pady=10)

    update_button = tk.Button(
        resume_window,
        text="Обновить статус",
        command=lambda: update_candidate_status(first_name, last_name))
    update_button.pack(padx=10, pady=10)
    export_button = tk.Button(
        resume_window,
        text="Экспортировать резюме",
        command=lambda: export_resume_to_disk(resume_filename, full_name))
    export_button.pack(padx=10, pady=5)
    close_button = tk.Button(
        resume_window,
        text="Закрыть",
        command=resume_window.destroy
    )
    close_button.pack(pady=10)


def update_candidate_status(first_name, last_name):
    """Обновление статуса кандидата в базе данных."""
    response_value = "Принят на работу" if acceptance_var.get() else ""
    connection = sqlite3.connect(database.DB_NAME)
    cursor = connection.cursor()

    try:
        cursor.execute("""
        UPDATE candidates
        SET response = ?
        WHERE first_name = ? AND last_name = ?
        """, (response_value, first_name, last_name))
        cursor.execute("""
        SELECT id FROM candidates WHERE first_name = ? AND last_name = ?
        """, (first_name, last_name))
        candidate_id = cursor.fetchone()

        if candidate_id:
            cursor.execute("""
            INSERT INTO responses (candidate_id, response)
            VALUES (?, ?)
            """, (candidate_id[0], response_value))

        connection.commit()
        messagebox.showinfo(
            "Обновление",
            f"Статус кандидата {first_name} {last_name} обновлен."
        )
    except sqlite3.Error as e:
        connection.rollback()
        messagebox.showerror(
            "Ошибка",
            f"Ошибка при обновлении статуса кандидата: {e}"
        )
    finally:
        connection.close()

    update_candidates()


def show_about():
    try:
        with open("about.txt", "r", encoding="utf-8") as file:
            about_content = file.read()
    except FileNotFoundError:
        about_content = "Файл 'about.txt' не найден."

    about_window = Toplevel()
    about_window.title("О программе")

    text_widget = tk.Text(about_window, wrap="word", height=20, width=60)
    text_widget.insert(tk.END, about_content)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(padx=10, pady=10)

    close_button = tk.Button(
        about_window,
        text="Закрыть",
        command=about_window.destroy
    )
    close_button.pack(pady=10)


root = tk.Tk()
root.title("HR Симулятор")
root.protocol("WM_DELETE_WINDOW", lambda: (root.destroy()))

about_button = tk.Button(root, text="О программе", command=show_about)
about_button.pack(side="bottom", pady=10)

acceptance_var = tk.BooleanVar(value=False)
filter_frame = tk.Frame(root)
filter_frame.pack(pady=10)

tk.Label(filter_frame, text="Желаемая ЗП:").grid(row=0, column=0, padx=5)
salary_var = tk.StringVar(value="Все")
salary_combo = ttk.Combobox(
    filter_frame,
    textvariable=salary_var,
    values=["Все"] + SALARY_RANGES, width=15
)
salary_combo.grid(row=1, column=0, padx=5)

tk.Label(filter_frame, text="Опыт работы:").grid(row=0, column=1, padx=5)
experience_var = tk.StringVar(value="Все")
experience_combo = ttk.Combobox(
    filter_frame,
    textvariable=experience_var,
    values=["Все"] + list(EXPERIENCE_LEVELS),
    width=15
)
experience_combo.grid(row=1, column=1, padx=5)

tk.Label(filter_frame, text="Ваши ответы:").grid(row=0, column=2, padx=5)
response_var = tk.StringVar(value="Все")
response_combo = ttk.Combobox(
    filter_frame,
    textvariable=response_var,
    values=["Все", "Ответили", "Без ответа"], width=15
)
response_combo.grid(row=1, column=2, padx=5)

tk.Label(filter_frame, text="Языки:").grid(row=2, column=0, padx=5)
languages_var = tk.StringVar(value="Все")
languages_combo = ttk.Combobox(
    filter_frame,
    textvariable=languages_var,
    values=["Все"] + TECH_STACK["languages"],
    width=20
)
languages_combo.grid(row=3, column=0, padx=5)

tk.Label(filter_frame, text="Фреймворки:").grid(row=2, column=1, padx=5)
frameworks_var = tk.StringVar(value="Все")
frameworks_combo = ttk.Combobox(
    filter_frame,
    textvariable=frameworks_var,
    values=["Все"] + TECH_STACK["frameworks"],
    width=20
)
frameworks_combo.grid(row=3, column=1, padx=5)

tk.Label(filter_frame, text="API:").grid(row=2, column=2, padx=5)
apis_var = tk.StringVar(value="Все")
apis_combo = ttk.Combobox(
    filter_frame,
    textvariable=apis_var,
    values=["Все"] + TECH_STACK["apis"],
    width=20
)
apis_combo.grid(row=3, column=2, padx=5)

filter_button = tk.Button(
    filter_frame,
    text="Применить фильтры",
    command=update_candidates)
filter_button.grid(row=4, column=0, columnspan=6, pady=10)

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

candidates_frame = tk.Frame(main_frame)
candidates_frame.pack(fill="both", expand=True, pady=(0, 10))
tk.Label(
    candidates_frame,
    text="Список кандидатов",
    font=("Arial", 14)
).pack(pady=5)
candidates_tree = ttk.Treeview(
    candidates_frame,
    columns=("name", "experience", "salary", "stack", "response"),
    show="headings", height=25
)
candidates_tree.heading("name", text="Кандидат")
candidates_tree.heading("experience", text="Опыт")
candidates_tree.heading("salary", text="Желаемая ЗП")
candidates_tree.heading("stack", text="Стэк кандидата")
candidates_tree.heading("response", text="Ваш ответ")
candidates_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)

vacancies_frame = tk.Frame(main_frame)
vacancies_frame.pack(fill="both", expand=True)
tk.Label(
    vacancies_frame,
    text="Список вакансий",
    font=("Arial", 14)
).pack(pady=5)
vacancies_tree = ttk.Treeview(
    vacancies_frame,
    columns=("title", "experience", "salary", "stack"),
    show="headings", height=20
)
vacancies_tree.heading("title", text="Вакансия")
vacancies_tree.heading("experience", text="Опыт")
vacancies_tree.heading("salary", text="Зарплата")
vacancies_tree.heading("stack", text="Стэк")
vacancies_tree.pack()


update_candidates()
update_vacancies()

if __name__ == "__main__":
    root.mainloop()
