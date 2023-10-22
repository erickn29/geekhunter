
import pydantic
from requests import request
from bs4 import BeautifulSoup as bs  # noqa: N813

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


class GetMatchParser(BaseParser):
    """Парсер для GetMatch"""

    LINK = BaseParser.GETMATCH_LINK
    PAGE_ATTR = 'p'

    def __init__(self) -> None:
        super().__init__(url=self.LINK)

    def _get_num_pages(self, text: str) -> int:
        """Метод возвращает количество страниц с вакансиями"""
        soup = bs(text, 'html.parser')
        pagination_buttons = soup.find_all('div',
                                           {'class': 'b-pagination-page'})
        if pagination_buttons:
            return int(len(pagination_buttons) / 2)
        return 1

    def _get_vacancies_links(self, pages: list[str]) -> list[str]:
        """Получаем список ссылок на вакансии"""
        links = []
        for link in pages:
            soup = bs(
                request(method='GET', url=link, headers=self.headers).text,
                'html.parser')
            vacancy_cards = soup.find_all('div', {'class': 'b-vacancy-card'})
            for card in vacancy_cards:
                card_obj = bs(str(card), 'html.parser')
                link = card_obj.find('a')  # noqa: PLW2901
                links.append(f'https://getmatch.ru{link.get("href")}')
        return links

    def _get_salary(self, soup: bs) -> tuple[int | None, int | None]:
        """Метод возвращает зарплату"""
        salary_from: int | None = None
        salary_to: int | None = None
        salary_string = soup.find_all('h3')[0].text.replace('≈', '')
        if '—' in salary_string:
            salary_list = salary_string.split('—')
            salary_from = int(salary_list[0].replace(' ', ''))
            salary_to = int(
                salary_list[1].replace('₽/мес на руки', '').replace(
                    '$/мес на руки', '').replace('€/мес на руки',
                                                 '').replace(' ',
                                                             '').replace(
                    '\u200d', ''))
            if '$' in salary_string or '€' in salary_string:
                salary_from = salary_from * self.course_rate
                salary_to = salary_to * self.course_rate
        if 'от' in salary_string:
            salary_string = salary_string.replace(' ', '')
            number = ''
            for c in salary_string:
                if c.isdigit():
                    number += c
            salary_from = int(number)
            if '$' in salary_string or '€' in salary_string:
                salary_from = int(number) * self.course_rate
        return salary_from, salary_to

    def _get_company_city(self, soup: bs) -> str | None:
        """Метод возвращает адрес компании"""
        if soup.find('span', {'class': 'b-vacancy-locations--first'}):
            return soup.find('span', {
                'class': 'b-vacancy-locations--first'}).text.replace(
                '\"', '').replace('📍 ', '').replace(',', '').split(' ')[0]
        return 'Москва'

    def _get_language(
            self,
            title: str, text: str, stack: list | None
    ) -> str | None:
        """Метод возвращает требуемый язык"""
        return Analyzer.get_language(
            title=self.rm_punctuations(title),
            text=self.rm_punctuations(text),
            stack=stack
        )

    def _get_vacancy_data(self, page: str, link: str) -> Vacancy | None:
        """Метод возвращает информацию о вакансии"""
        if page:
            try:
                soup = bs(page, 'html.parser')
                text = soup.find('section', {'class': 'b-vacancy-description'})
                new_text = Analyzer.html_to_text(text)
                title = soup.find('h1').text
                salary = self._get_salary(soup)
                exp_obj = soup.find('div', text='Уровень').nextSibling.text
                experience = Experience(
                    name=Analyzer.get_getmatch_experience(exp_obj)
                )
                speciality = Speciality(
                    name=Analyzer.get_speciality(title, new_text)
                )
                stack_obj = bs(str(soup.find('div', {
                    'class': 'b-vacancy-stack-container'})), 'html.parser')
                stack_tags = stack_obj.find_all('span', {'class': 'g-label'})
                stack_tools = []
                for obj in stack_tags:
                    stack_tools.append(StackTool(name=obj.text))
                city = City(
                    name=self._get_company_city(soup)
                )
                company = Company(
                    city=city,
                    name=soup.find_all('h2')[0].text.replace('в ', '')
                )
                is_remote = bool(
                    'Полная удалёнка' in soup.text or 'Можно удалённо из РФ' in
                    soup.text
                )
                grade = Grade(name='Middle')
                if soup.find('div', text='Уровень').nextSibling:
                    grade.name = soup.find(
                        'div', text='Уровень').nextSibling.text
                language = Language(
                    name=self._get_language(
                        title, new_text, stack_tools
                    )
                )
                return Vacancy(
                    title=title,
                    text=new_text,
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
            except AttributeError as e:
                print(e)
            except ValueError as e:
                print(e)
            except pydantic.ValidationError as e:
                print(e, link)
        return None

