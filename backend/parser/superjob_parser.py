import json
import re

import pydantic
import requests
from requests import request
from tqdm import tqdm
from bs4 import BeautifulSoup as bs

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


class SuperJobParser(BaseParser):

    LINK = BaseParser.SUPERJOB_LINK

    def __init__(self) -> None:
        super().__init__(url=self.LINK)

    def _get_vacancies_links(self, text: str) -> list:
        """Получаем список ссылок на вакансии"""
        links = []
        soup = bs(
            request(
                method='GET',
                url=self.LINK,
                headers=self.headers
            ).text, 'html.parser')
        all_links_on_page = soup.find_all('a')
        for link_ in all_links_on_page:
            if ('vakansii' in link_.attrs.get('href') and
                    '.html' in link_.attrs.get('href')):
                links.append(
                    f"https://russia.superjob.ru{link_.attrs.get('href')}"
                )
        return links

    def _get_vacancy_data(self, page: str, link: str) -> Vacancy | None:
        """Получаем информацию по вакансии"""
        soup = bs(page, 'html.parser')
        scripts_json = soup.find_all('script', {'type': 'application/ld+json'})
        data = None
        for script in scripts_json:
            if 'title' in script.text:
                data = json.loads(script.text)
        try:
            if data:
                title = data['title']
                salary_from = None
                salary_to = None
                if data['baseSalary']['value'].get('minValue'):
                    salary_from = data['baseSalary']['value']['minValue']
                if data['baseSalary']['value'].get('maxValue'):
                    salary_to = data['baseSalary']['value']['maxValue']
                exp_obj = soup.select_one('.f-test-address').nextSibling
                text = bs(data['description'], 'html.parser')
                new_text = BaseParser.text_cleaner(Analyzer.html_to_text(text))
                is_remote = True if data.get(
                    'jobLocationType') == 'TELECOMMUTE' else False
                stack_tools = [
                    StackTool(name=i) for i in Analyzer.get_stack_raw_text(
                        new_text)
                ]
                language = Language(
                    name=Analyzer.get_language(title, new_text, stack_tools)
                )
                speciality = Speciality(
                    name=Analyzer.get_speciality(title, new_text)
                )
                experience = Experience(
                    name=Analyzer.get_superjob_experience(exp_obj.text)
                )
                grade = Grade(
                    name=Analyzer.get_grade(title, new_text, experience.name)
                )
                city = City(
                    name=data['jobLocation']['address']['addressLocality']
                )
                company = Company(
                    city=city,
                    name=data['hiringOrganization']['name']
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
                    salary_from=salary_from,
                    salary_to=salary_to,
                    grade=grade,
                    stack=stack_tools,
                )
        except KeyError as e:
            print(e, link)
            return None
        except AttributeError as e:
            print(e, link)
            return None
        except pydantic.ValidationError as e:
            print(e, link)
