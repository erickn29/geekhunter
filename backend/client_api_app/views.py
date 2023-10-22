from datetime import datetime, timedelta

from django.db.models import Q, QuerySet
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import generics
import os
from dotenv import load_dotenv

from parser.run_parsers import main
from client_api_app.models import Vacancy, Language, Experience, Grade, \
    Speciality, StackTool, City
from client_api_app.serializers import VacancySerializer, LanguageSerializer, \
    ExperienceSerializer, GradeSerializer, SpecialitySerializer, \
    StackToolSerializer, CitySerializer


load_dotenv()


@api_view(['POST', ])
def test(request: Request) -> Response:
    """Тестовая"""
    if request.data.get('token') == os.getenv('PARSER_TOKEN'):
        main(True, True, True, True)
        return Response({'test': 'data'})
    return Response({'error': 'token error'})


class VacancyList(generics.ListAPIView):
    """Список актуальных вакансий (размещенных в течение 30 дней)"""

    queryset = Vacancy.objects.get_actual()
    serializer_class = VacancySerializer

    def get_queryset(self) -> QuerySet:
        """G"""
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date()
        queryset = super().get_queryset()
        queryset = queryset.filter(
            Q(date__range=[start_date, end_date]) &
            (
                Q(salary_from__isnull=False) |
                Q(salary_to__isnull=False)
            )
        ).order_by('-date')
        if len(self.request.GET) > 0:
            data = self.request.GET
            if data.get('language'):
                queryset = queryset.filter(language=Language.objects.get(
                    name=str(data.get('language'))))
            if data.get('salary_from'):
                salary_from = data.get('salary_from', 0)
                queryset = queryset.filter(
                    Q(salary_from__gte=int(salary_from)) |
                    Q(salary_from=None, salary_to__gte=salary_from))
            if data.get('location'):
                location = data.get('location')
                queryset = queryset.filter(
                    company__city__name=location)
            if data.get('is_remote') and data.get('is_remote') == 'true':
                queryset = queryset.filter(is_remote=True)
            if data.get('experience'):
                experience = data.get('experience')
                queryset = queryset.filter(experience__name=experience)
            if data.get('speciality'):
                speciality = data.get('speciality')
                queryset = queryset.filter(speciality__name=speciality)
            if data.get('grade'):
                grade = data.get('grade')
                queryset = queryset.filter(grade__name=grade)
        return queryset


class LanguageList(generics.ListAPIView):
    """Список языков программирования"""

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class ExperienceList(generics.ListAPIView):
    """Список градаций опыта"""

    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer


class GradeList(generics.ListAPIView):
    """Список грейдов"""

    queryset = Grade.objects.all()
    serializer_class = GradeSerializer


class SpecialityList(generics.ListAPIView):
    """Список специальностей"""

    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer


class CityList(generics.ListAPIView):
    """Список городов"""

    queryset = City.objects.all()
    serializer_class = CitySerializer


class StackToolList(generics.ListAPIView):
    """Список навыков"""

    queryset = StackTool.objects.all()
    serializer_class = StackToolSerializer
