import re

import pydantic
import requests
from requests import request
from tqdm import tqdm
from bs4 import BeautifulSoup

from .base_parser import BaseParser
from .analyzer import Analyzer
from .schema import (
    StackTool,
    Language,
    City,
    Speciality,
    Experience,
    Grade,
    Company,
    Vacancy
)


class HHParser(BaseParser):
    """Парсер для hh.ru"""

    LINK = BaseParser.HH_LINK
    PAGE_ATTR = 'page'
    MAX_LINK_LENGTH = 200

    def __init__(self) -> None:
        super().__init__(url=self.LINK)

    def _get_num_pages(self, text: str) -> int:
        """Метод возвращает количество страниц с вакансиями"""
        counter = 0
        if text:
            elements_list = re.findall(r'pager-page-wrapper-\d+-\d+', text)
            if elements_list:
                for el in tqdm(elements_list):
                    last_el = int(el.split('-')[-1]) + 1
                    if last_el > counter:
                        counter = last_el
        return counter

    def _get_vacancies_links(self, pages: list[str]) -> list[str]:
        """Получаем список ссылок на вакансии"""
        links_list = []
        watched = []
        print(f'\nСобираем ссылки на вакансии со страниц {self.source_name}')
        for page in tqdm(pages):
            try:
                response = request(
                    method='GET', url=page, headers=self.headers
                )
                if response.ok:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    blocks = soup.find_all('div', {'class': 'serp-item'})
                    for block in blocks:
                        block_title = block.find_all_next(
                            'a', {'data-qa': 'serp-item__title'}
                        )[0].text
                        block_salary = block.find_all_next(
                            'span',
                            {'data-qa': 'vacancy-serp__vacancy-compensation'}
                        )[0].text
                        block_company = block.find_all_next(
                            'a',
                            {'data-qa': 'vacancy-serp__vacancy-employer'}
                        )[0].text
                        block_link = block.find_all_next(
                            'a',
                            {'data-qa': 'serp-item__title'}
                        )[0]['href']
                        watched.append(
                            (block_title, block_salary, block_company)
                        )
                        if len(watched) > 1 and (
                            (block_title, block_salary, block_company)
                            not in watched[:-1]
                        ) and not (
                            set(
                                block_title.lower().split()
                            ) & set(self.STOP_WORDS)
                        ) and len(block_link) < self.MAX_LINK_LENGTH:
                            links_list.append(block_link)
            except requests.exceptions.RequestException:
                print(f'Не смог обработать страницу {page}')
        return links_list

    def _get_title(self, soup: BeautifulSoup) -> str | None:
        """Метод возвращает заголовок вакансии"""
        if soup.find('h1', {'data-qa': "vacancy-title"}):
            return self.string_cleaner(
                soup.find('h1', {'data-qa': "vacancy-title"}).text
            )
        return None

    def _get_text(self, soup: BeautifulSoup) -> str | None:
        """Метод возвращает текст вакансии"""
        if soup.find('div', {'class': "vacancy-description"}):
            return self.string_cleaner(
                soup.find('div', {'class': "vacancy-description"}).text
            )
        return soup.text

    @staticmethod
    def _get_speciality(title: str, text: str) -> str | None:
        """Метод возвращает специальность"""
        return Analyzer.get_speciality(title=title, text=text)

    def _get_experience(self, soup: BeautifulSoup) -> str | None:
        """Метод возвращает требуемый опыт"""
        if soup.find('span', {'data-qa': "vacancy-experience"}):
            return Analyzer.get_experience(
                self.string_cleaner(
                    soup.find('span', {'data-qa': "vacancy-experience"}).text
                )
            )
        return None

    def _get_language(
            self,
            title: str, text: str, stack: list | None
    ) -> str | None:
        """Метод возвращает требуемый язык"""
        return Analyzer.get_language(
            title=title,
            text=self.rm_punctuations(text),
            stack=stack
        )

    def _get_grade(self, title: str, text: str, experience: str) -> str | None:
        """Метод возвращает требуемый грейд"""
        return Analyzer.get_grade(
            title=self.rm_punctuations(title),
            text=self.rm_punctuations(text),
            experience=experience
        )

    def _get_company_name(self, soup: BeautifulSoup) -> str | None:
        """Метод возвращает название компании"""
        if soup.find('div', {'class': "vacancy-company-details"}):
            return self.string_cleaner(
                soup.find(
                    'div', {'class': "vacancy-company-details"}
                ).text
            )
        return None

    def _get_company_city(self, soup: BeautifulSoup) -> str | None:
        """Метод возвращает адрес компании"""
        if soup.find('p', {'data-qa': "vacancy-view-location"}):
            return self.string_cleaner(
                soup.find(
                    'p', {'data-qa': "vacancy-view-location"}
                ).text
            ).split(',')[0]
        if soup.find('span', {'data-qa': "vacancy-view-raw-address"}):
            return self.string_cleaner(
                soup.find(
                    'span', {'data-qa': "vacancy-view-raw-address"}
                ).text
            ).split(',')[0]
        return None

    def _get_is_remote(self, soup: BeautifulSoup) -> bool:
        """Метод возвращает возможность удаленной работы"""
        if soup.find('p', {'data-qa': "vacancy-view-employment-mode"}):
            remote_section = self.string_cleaner(
                soup.find(
                    'p', {'data-qa': "vacancy-view-employment-mode"}
                ).text
            ).lower()
            if 'удаленная работа' in remote_section:
                return True
        return False

    @staticmethod
    def _get_stack(soup: BeautifulSoup) -> list[StackTool] | None:
        """Метод возвращает стек навыков"""
        if soup.find('div', {'class': "bloko-tag-list"}):
            stack_not_clear = soup.find_all(
                'div', {'class': "bloko-tag bloko-tag_inline"}
            )
            return [StackTool(name=i.text) for i in stack_not_clear]
        return None

    def _get_salary(
            self, soup: BeautifulSoup
    ) -> tuple[int | None, int | None]:
        """Метод возвращает зарплату"""
        salary_from: int | None = None
        salary_to: int | None = None
        salary = self.string_cleaner(
            soup.find('div', {'data-qa': 'vacancy-salary'}).text
        ).replace('на руки', '').replace('до вычета налогов', '')
        if 'руб' in salary or '₽' in salary:
            if 'от' in salary and 'до' not in salary:
                salary_from = int(
                    ''.join([i for i in salary if i.isdigit()])
                )
            if 'до' in salary and 'от' not in salary:
                salary_to = int(
                    ''.join([i for i in salary if i.isdigit()])
                )
            if 'от' in salary and 'до' in salary:
                salary_list = salary.split('до')
                salary_from = int(
                    ''.join([i for i in salary_list[0] if i.isdigit()])
                )
                salary_to = int(
                    ''.join([i for i in salary_list[1] if i.isdigit()])
                )
        if '$' in salary or '€' in salary:
            if 'от' in salary and 'до' not in salary:
                salary_from = int(
                    ''.join([i for i in salary if i.isdigit()])
                ) * self.course_rate
            if 'до' in salary and 'от' not in salary:
                salary_to = int(
                    ''.join([i for i in salary if i.isdigit()])
                ) * self.course_rate
            if 'от' in salary and 'до' in salary:
                salary_list = salary.split('до')
                salary_from = int(
                    ''.join([i for i in salary_list[0] if i.isdigit()])
                ) * self.course_rate
                salary_to = int(
                    ''.join([i for i in salary_list[1] if i.isdigit()])
                ) * self.course_rate
        return salary_from, salary_to

    def _get_vacancy_data(self, page: str, link: str) -> Vacancy | None:
        """Метод возвращает информацию о вакансии"""
        if page:
            try:
                soup = BeautifulSoup(page, 'html.parser')
                title = self._get_title(soup)
                text = self._get_text(soup)
                stack = self._get_stack(soup)
                salary = self._get_salary(soup)
                is_remote = self._get_is_remote(soup)

                language = Language(
                    name=self._get_language(
                        title=title,
                        text=text,
                        stack=stack
                    )
                )
                stack_tools = self._get_stack(soup)
                speciality = Speciality(
                    name=self._get_speciality(title=title, text=text)
                )
                experience = Experience(
                    name=self._get_experience(soup)
                )
                grade = Grade(
                    name=self._get_grade(
                        title=title,
                        text=text,
                        experience=experience.name)
                )
                city = City(
                    name=self._get_company_city(soup)
                )
                company = Company(
                    city=city,
                    name=self._get_company_name(soup)
                )
                return Vacancy(
                    title=title,
                    text=text,
                    link=link,
                    speciality=speciality,
                    experience=experience,
                    language=language,
                    company=company,
                    is_remote=is_remote,
                    salary_from=salary[0],
                    salary_to=salary[1],
                    grade=grade,
                    stack=stack_tools,
                )
            except IndexError as e:
                print(e, link)
            except ValueError as e:
                print(e, link)
            except TypeError as e:
                print(e, link)
            except pydantic.ValidationError as e:
                print(e, link)
        return None
