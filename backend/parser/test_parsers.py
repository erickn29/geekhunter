from datetime import datetime

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


def main(wright_to_file: bool = True) -> VacanciesList:
    """Функция для тестирования парсеров"""
    print('---run main func---')
    hh_result = test_hh()
    superjob_result = test_superjob()
    date_ = datetime.strftime(datetime.now(), "%d_%m_%Y")
    if wright_to_file:
        with open(
            f'test_hh_{date_}.json',
            'w',
            encoding='utf-8'
        ) as f:
            f.write(hh_result.model_dump_json())
        with open(
                f'test_superjob_{date_}.json',
                'w',
                encoding='utf-8'
        ) as f:
            f.write(superjob_result.model_dump_json())
    print('Test is done!')
    return superjob_result


if __name__ == '__main__':
    main(wright_to_file=True)
