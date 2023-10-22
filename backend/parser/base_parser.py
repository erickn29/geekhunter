import time
from typing import NoReturn

import requests.exceptions
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError
from psycopg2 import DataError
from requests import request
from tqdm import tqdm

from client_api_app.models import Company, StackTool, Speciality, Experience, \
    Grade, Language, City, Vacancy
from . import schema


# from tqdm import tqdm


# from vacancies_app.models import *
# from .analyzer import Analyzer


class BaseParser:
    """Базовый класс для парсеров ресурсов"""

    HH_LINK = 'https://hh.ru/search/vacancy?area=113&employment=full&excluded_text=%D0%BC%D0%B5%D0%BD%D0%B5%D0%B4%D0%B6%D0%B5%D1%80%2C%D0%B2%D0%BE%D0%B4%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%2C%D0%BF%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%BA%D0%B0%2C%D0%BF%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%BA%D0%B8&search_field=name&search_field=description&only_with_salary=true&text=python+OR+php+OR+c%2B%2B+OR+c%23+OR+javascript+OR+java&no_magic=true&L_save_area=true&search_period=1&items_on_page=20&hhtmFrom=vacancy_search_list'  # noqa: E501
    HABR_LINK = 'https://career.habr.com/vacancies/rss?currency=RUR&s[]=2&s[]=3&s[]=82&s[]=4&s[]=5&s[]=72&s[]=1&s[]=6&s[]=77&s[]=83&s[]=86&s[]=73&s[]=8&s[]=9&s[]=85&s[]=7&s[]=75&sort=relevance&type=all&with_salary=true'  # noqa: E501
    SUPERJOB_LINK = 'https://russia.superjob.ru/vacancy/search/?keywords=c%23%2Cpython%2Cjavascript%2Cphp%2Cc%2B%2B%2Cjava&payment_value=20000&period=1&payment_defined=1&click_from=facet'  # noqa: E501
    GETMATCH_LINK = 'https://getmatch.ru/vacancies?sa=150000&l=moscow&l=remote&l=saints_p&pa=3d&s=landing_ca_header'  # noqa: E501
    PROGLIB_LINK = 'https://proglib.io/vacancies/all?direction=Programming&workType=fulltime&workPlace=all&experience=100&salaryFrom=500&page=1'  # noqa: E501
    STOP_WORDS = (
        '1C', '1С', '1с', '1c', 'машинист', 'водитель', 'таксист', 'курьер',
        'охранник', 'поддержки', 'поддержку', 'оператор', 'поддержка',
        'маркетолог', 'онлайн-поддержки', 'менеджер', 'инженер-проектировщик'
    )
    sleep_time = 0.5
    course_rate = 100

    LINK = None
    PAGE_ATTR = None

    def __init__(self, url: str) -> NoReturn:
        """Стандартный конструктор класса"""
        self.url = url
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',  # noqa: E501
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'accept-encoding': 'gzip,deflate,br',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'  # noqa: E501
        }
        self.source_name = self.url.split("/")[2]

    def _get_main_page_html(self) -> str | NoReturn:
        """Метод возвращает ответ начальной страницы ресурса"""
        try:
            response = request(
                method='GET', url=self.url, headers=self.headers
            )
            if response.ok:
                return response.text
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException from e

    def _get_num_pages(self, text: str) -> int:
        """Метод возвращает количество страниц с вакансиями.

        Определяется отдельно в каждом классе парсера.
        """
        return 0

    def _get_pages(self, text: str, attr: str) -> list[str]:
        """Метод возвращает список страниц(URL) с вакансиями"""
        print(f'Получаем список страниц(URL) с вакансиями {self.source_name}')
        num_pages = self._get_num_pages(text)
        page_list = []
        if num_pages > 0:
            for page in tqdm(range(num_pages)):
                url = self.url + f'&{attr}={page}'
                page_list.append(url)
            return page_list
        return [self.url, ]

    def _get_vacancies_links(self, pages: list[str]) -> list[str]:
        """Получаем список ссылок на вакансии.

        Определяется отдельно в каждом классе парсера.
        """
        pass

    def _get_vacancy_page_text(self, link: str) -> str | None:
        """Метод возвращает страницу вакансии"""
        try:
            response = request(method='GET', url=link, headers=self.headers)
            if response.ok:
                return response.text
        except requests.exceptions.RequestException:
            print(f'Ошибка запроса к {link}')
            return None

    def _get_vacancy_data(self, page: str, link: str) -> schema.Vacancy | None:
        """Метод возвращает информацию о вакансии"""
        pass

    @staticmethod
    def string_cleaner(string: str) -> str:
        """Метод очищает строку от некоторых символов"""
        return string.strip().replace('  ', '').replace('\n', ' ').replace(
            '\t', '').replace('\xa0', ' ').replace('город ', '').replace(
            'деревня ', '').replace('г. ', '')

    @staticmethod
    def text_cleaner(string: str) -> str:
        """Метод очищает строку от символов и html"""
        mapping = {
            ord(','): None,
            ord('.'): None,
            ord(':'): None,
            ord(';'): None,
            ord('\''): None,
            ord('\"'): None,
            ord('•'): None,
            ord('('): None,
            ord(')'): None,
        }
        return string.translate(mapping).replace(
            '<p>', '').replace(
            '</p>', '').replace(
            '<br>', '')

    @staticmethod
    def rm_punctuations(string: str) -> str:
        """Метод очищает строку от знаков пунктуации"""
        try:
            punctuations = (
                '.', ',', ':', ';', '\'', '\"', '(', ')', '[', ']'
            )
            for p in punctuations:
                string = string.replace(p, '')
            return string.replace('-', ' ')
        except AttributeError as e:
            print(e)
            return ''

    def get_all_vacancies(
            self, *,
            print_vacancy: bool = False,
            test: bool = False,
            vacancies_count: int = 5
    ) -> schema.VacanciesList:
        """Метод возвращает все найденные вакансии.

        Получает вакансии с первой и последней страницы в случае теста
        """
        vacancies = schema.VacanciesList()
        main_page_html = self._get_main_page_html()
        pages_list = self._get_pages(main_page_html, self.PAGE_ATTR)
        vacancy_links = self._get_vacancies_links(
            pages_list if not test else [pages_list[0], pages_list[-1]]
        )
        try:
            if test:
                v_count = vacancies_count
                vacancy_links = vacancy_links[:v_count] +\
                    vacancy_links[-1 * v_count:]
            for link in tqdm(vacancy_links):
                vacancy_page = self._get_vacancy_page_text(link)
                vacancy_data = self._get_vacancy_data(vacancy_page, link)
                if vacancy_data:
                    vacancies.data.append(vacancy_data)
                    time.sleep(self.sleep_time)
                    if print_vacancy:
                        print(vacancy_data)
        except IndexError as e:
            print(e)
        return vacancies

    def vacancies_to_db(self, vacancies: schema.VacanciesList) -> NoReturn:
        """Метод добавляет вакансии в БД"""
        for vacancy in tqdm(vacancies.data):
            if vacancy and not (
                set(vacancy.title.lower().split()) &
                set(self.STOP_WORDS)
            ):
                try:
                    print(vacancy)
                    city_obj = City.objects.get_or_create(
                        name=vacancy.company.city.name
                    )[0]
                    speciality_obj = Speciality.objects.get_or_create(
                        name=vacancy.speciality.name
                    )[0]
                    experience_obj = Experience.objects.get_or_create(
                        name=vacancy.experience.name
                    )[0]
                    grade_obj = Grade.objects.get_or_create(
                        name=vacancy.grade.name
                    )[0]
                    language_obj = Language.objects.get_or_create(
                        name=vacancy.language.name
                    )[0]
                    company_obj = Company.objects.get_or_create(
                        name=vacancy.company.name,
                        city=city_obj,
                    )[0]
                    vacancy_obj, created = Vacancy.objects.get_or_create(
                        title=vacancy.title,
                        company=company_obj,
                        is_remote=vacancy.is_remote,
                        salary_from=vacancy.salary_from,
                        salary_to=vacancy.salary_to,
                        speciality=speciality_obj,
                        experience=experience_obj,
                        grade=grade_obj,
                        link=vacancy.link,
                        language=language_obj,
                    )
                    if created:
                        for obj in (
                            city_obj,
                            speciality_obj,
                            experience_obj,
                            grade_obj,
                            language_obj
                        ):
                            obj.count += 1
                            obj.save()
                        if vacancy.stack:
                            for stack in vacancy.stack:
                                stack_obj = StackTool.objects.get_or_create(
                                    name=stack.name,
                                )[0]
                                stack_obj.count += 1
                                stack_obj.save()
                                vacancy_obj.stack.add(stack_obj)
                except MultipleObjectsReturned as e:
                    print(e)
                except IntegrityError as e:
                    print(e)
                except AttributeError as e:
                    print(e)
                except IndexError as e:
                    print(e)
                except TypeError as e:
                    print(e)
                except Vacancy.DoesNotExist as e:
                    print(e)
                except DataError as e:
                    print(e)

