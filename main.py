import requests
from terminaltables import AsciiTable
import os
from itertools import count
from dotenv import load_dotenv


def create_table(languages_statistics, title):
    languages_statistics_table = [["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]]
    for language, language_statistics in languages_statistics.items():
        row = [language]
        for characteristic_name, characteristic in language_statistics.items():
            row.append(characteristic)
        languages_statistics_table.append(row)
    return AsciiTable(languages_statistics_table, title).table


def predict_salary(salary_from, salary_to):
    if salary_from and not salary_to:
        expected_salary = salary_from * 1.2
    elif not salary_from and salary_to:
        expected_salary = salary_to * 0.8
    else:
        expected_salary = (salary_from + salary_to) / 2
    return expected_salary


def predict_rub_salary_sj(vacancy):
    salary_to = None
    salary_from = None
    if vacancy["currency"] != "rub":
        return None
    if vacancy["payment_from"]:
        salary_from = vacancy["payment_from"]
    if vacancy["payment_to"]:
        salary_to = vacancy["payment_to"]
    expected_salary = predict_salary(salary_from, salary_to)
    return expected_salary


def predict_rub_salary_hh(vacancy):
    if not vacancy["salary"] or vacancy["salary"]["currency"] != "RUR":
        return None
    salary_from = vacancy["salary"]["from"]
    salary_to = vacancy["salary"]["to"]
    expected_salary = predict_salary(salary_from, salary_to)
    return expected_salary


def get_sj_vacancies(language, sj_secret_key):
    vacancies = []
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        "X-Api-App-Id": sj_secret_key
    }
    for page in count(0):
        params = {
            "keyword": language,
            "catalogues": "Разработка, программирование",
            "town": "Moscow",
            "page": page
        }
        response = requests.get(url, headers=headers, params=params).json()
        response.raise_for_status()
        response = response.json()
        vacancies.extend(response["objects"])
        if not response["more"]:
            break
    return vacancies


def get_sj_language_statistics(language, sj_secret_key):
    salaries = []
    vacancies = get_sj_vacancies(language, sj_secret_key)
    for vacancy in vacancies:
        salary = predict_rub_salary_sj(vacancy)
        if salary:
            salaries.append(salary)
    try:
        average_salary = int(sum(salaries) / len(salaries))
    except ZeroDivisionError:
        average_salary = None
    language_statistics = {
        "vacancies_found": len(vacancies),
        "vacancies_processed": len(salaries),
        "average_salary": average_salary
    }
    return language_statistics


def get_sj_statistics(sj_secret_key):
    sj_statistics = {}
    languages = ["Python", "C#", "Java", "JavaScript", "Ruby", "C++", "PHP", "C"]
    for language in languages:
        sj_statistics[language] = get_sj_language_statistics(language, sj_secret_key)
    return sj_statistics


def get_hh_vacancies(language):
    vacancies = []
    url = "https://api.hh.ru/vacancies/"
    for page in count(0):
        params = {
            "city": "Москва",
            "text": f"Программист {language}",
            "page": page
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        response = response.json()
        vacancies.extend(response["items"])
        if page == response["pages"] - 1:
             break
    return vacancies


def get_hh_language_statistics(language):
    salaries = []
    vacancies = get_hh_vacancies(language)
    for vacancy in vacancies:
        salary = predict_rub_salary_hh(vacancy)
        if salary:
            salaries.append(salary)
    try:
        average_salary = int(sum(salaries) / len(salaries))
    except ZeroDivisionError:
        average_salary = None
    language_statistics = {
        "vacancies_found": len(vacancies),
        "vacancies_processed": len(salaries),
        "average_salary": average_salary
    }
    return language_statistics


def get_hh_statistics():
    hh_statistics = {}
    languages = ["Python", "C#", "Java", "JavaScript", "Ruby", "C++", "PHP", "C"]
    for language in languages:
        hh_statistics[language] = get_hh_language_statistics(language)
    return hh_statistics


def main():
    load_dotenv()
    sj_secret_key = os.getenv("SJ_SECRET_KEY")
    print(create_table(get_sj_statistics(sj_secret_key), "SuperJob"))
    print(create_table(get_hh_statistics(), "HeadHunter"))


if __name__ == "__main__":
    main()