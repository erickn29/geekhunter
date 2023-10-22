from datetime import datetime

from parser.getmatch_parser import GetMatchParser
from parser.hh_parser import HHParser
from parser.schema import VacanciesList
from parser.superjob_parser import SuperJobParser


def test_hh() -> VacanciesList:
    """Функция для тестирования парсера hh.ru"""
    print('---run hh parser---')
    parser = HHParser()
    vacancies = parser.get_all_vacancies(test=True, vacancies_count=5)
    parser.vacancies_to_db(vacancies)
    return vacancies


def test_superjob() -> VacanciesList:
    """Функция для тестирования парсера superjob.ru"""
    print('---run superjob parser---')
    parser = SuperJobParser()
    vacancies = parser.get_all_vacancies(test=True, vacancies_count=5)
    parser.vacancies_to_db(vacancies)
    return vacancies


def test_getmatch() -> VacanciesList:
    """Функция для тестирования парсера superjob.ru"""
    print('---run getmatch parser---')
    parser = GetMatchParser()
    vacancies = parser.get_all_vacancies(test=True, vacancies_count=5)
    parser.vacancies_to_db(vacancies)
    return vacancies


def main_test(
        wright_to_file: bool = True,
        hh: bool = False,
        superjob: bool = False,
        getmatch: bool = False
) -> None:
    """Функция для тестирования парсеров"""
    print('---run main func---')
    date_ = datetime.strftime(datetime.now(), "%d_%m_%Y")
    if hh:
        hh_result = test_hh()
        if wright_to_file:
            with open(
                f'test_hh_{date_}.json',
                'w',
                encoding='utf-8'
            ) as f:
                f.write(hh_result.model_dump_json())
    if superjob:
        superjob_result = test_superjob()
        if wright_to_file:
            with open(
                    f'test_superjob_{date_}.json',
                    'w',
                    encoding='utf-8'
            ) as f:
                f.write(superjob_result.model_dump_json())
    if getmatch:
        getmatch_result = test_getmatch()
        if wright_to_file:
            with open(
                    f'test_getmatch_{date_}.json',
                    'w',
                    encoding='utf-8'
            ) as f:
                f.write(getmatch_result.model_dump_json())
    print('Test is done!')


if __name__ == '__main__':
    main_test(True, True, True, True)
