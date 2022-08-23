from rest_framework import status, viewsets
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from users.permissions import IsTeacher
from .serializers import ArticleSerializer, ArticleFileSerializer, SpecialitySerializer
from users.models import Teacher
from .models import Article
from college.models import Speciality, Subject
import json
from .permissions import IsArticleOwner


class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsTeacher()]
        elif self.request.method == 'DELETE':
            return [IsTeacher(), IsArticleOwner()]
        return []

    def update(self, request, *args, **kwargs):
        serializer = ArticleSerializer(instance=self.get_object(), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            response_data = serializer.data

            if 'files' in request.data:
                errors = serializer.instance.update_files(request.data['files'])
                response_data['file_errors'] = errors
                serialized_files = []
                for file in serializer.instance.files.all():
                    serialized_files.append(ArticleFileSerializer(instance=file).data)
                response_data['files'] = serialized_files
            return Response(data=response_data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        # reimplemented to add teacher to data
        data = request.data
        data['teacher'] = request.user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        context = super().get_serializer_context()

        if self.request.method != 'GET':
            context['teacher'] = Teacher.objects.get(pk=self.request.user.id)

        return context


class CreateArticleFileView(CreateAPIView):
    permission_classes = [IsTeacher]
    serializer_class = ArticleFileSerializer
    parser_classes = (FormParser, MultiPartParser)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['teacher'] = Teacher.objects.get(pk=self.request.user.id)
        return context

    def post(self, request, *args, **kwargs):
        # reimplemented to add article to data
        data = request.data
        data['article'] = kwargs['pk']
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpecialitiesView(ListAPIView):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer


class SubjectsView(ListAPIView):
    def get_queryset(self):
        return Subject.objects.filter(year__speciality__id=self.kwargs['speciality_id'],
                                      year__year=self.kwargs['year'])

    def get(self, request, *args, **kwargs):
        response = [subject for subject in self.get_queryset().values('id', 'title')]
        return Response(json.loads(json.dumps(response)), status=status.HTTP_200_OK)


class ArticlesView(ListAPIView):
    def get_queryset(self):
        queryset = Article.objects.filter(speciality_id=self.kwargs['speciality_id'],
                                          year=self.kwargs['year'],
                                          subject_id=self.kwargs['subject_id'])
        if 'teacher' in self.request.GET:
            return queryset.filter(teacher__email=self.request.GET['teacher'])

        if 'subject' in self.request.GET:
            return queryset.filter(teacher__email=self.request.GET['subject'])

        return queryset

    def get(self, request, *args, **kwargs):
        response = [article for article in self.get_queryset().values('id', 'title')]
        return Response(json.loads(json.dumps(response)), status=status.HTTP_200_OK)


class TeachersView(ListAPIView):
    def get_queryset(self):
        return Teacher.objects.filter(subjects__year__year=self.kwargs['year'],
                                      subjects__year__speciality=self.kwargs['speciality_id'],
                                      subjects__in=[self.kwargs['subject_id']])

    def get(self, request, *args, **kwargs):
        response = [teacher for teacher in self.get_queryset().values('first_name', 'last_name', 'email')]
        return Response(json.loads(json.dumps(response)), status=status.HTTP_200_OK)
