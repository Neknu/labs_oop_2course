from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.contrib.auth.models import User
from django_filters import rest_framework as filters

from .models import Category, Capital, Investor, Entrepreneur, Expert, Project, Rating
from .serializer import CategorySerializer, CapitalSerializer, InvestorSerializer, ExpertSerializer, \
    EntrepreneurSerializer, ProjectSerializer, RatingSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)


class CapitalViewSet(viewsets.ModelViewSet):
    queryset = Capital.objects.all()
    serializer_class = CapitalSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)


class InvestorViewSet(viewsets.ModelViewSet):
    queryset = Investor.objects.all()
    serializer_class = InvestorSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(detail=False, methods=['GET'])
    def get_queryset(self):
        investors = Investor.objects.all()
        if 'capitals' in self.request.data:
            capitals = self.request.data['capitals']
            if capitals:
                investors = investors.filter(capital__in=capitals)

        if 'categories' in self.request.data:
            categories = self.request.data['categories']
            if categories:
                investor_list = []
                for investor in investors:
                    if not investor.categories.all():
                        investor_list.append(investor.id)
                        continue
                    for category in investor.categories.all():
                        if category.id in categories:
                            investor_list.append(investor.id)
                            break
                investors = Investor.objects.filter(id__in=investor_list)

        return investors

    @action(detail=True, methods=['GET'])
    def find_projects(self, request, pk=None):
        investor = Investor.objects.get(id=pk)
        projects = Project.objects.filter(capital=investor.capital, investor=None)

        project_list = []
        for project in projects:
            for category in project.categories.all():
                if category in investor.categories.all():
                    project_list.append(project.id)
                    break
        projects = Project.objects.filter(id__in=project_list)

        # sort by avg_rating
        projects = sorted(projects.all(), key=lambda t: t.avg_rating())

        if projects:
            serializer = ProjectSerializer(projects, many=True)
            response = {'message': 'Projects found', 'result': serializer.data}
            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'Projects not found'}
            return Response(response, status=status.HTTP_204_NO_CONTENT)


class EntrepreneurViewSet(viewsets.ModelViewSet):
    queryset = Entrepreneur.objects.all()
    serializer_class = EntrepreneurSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)


class ExpertViewSet(viewsets.ModelViewSet):
    queryset = Expert.objects.all()
    serializer_class = ExpertSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)


class ProjectFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Project
        fields = ('name', )


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticatedOrReadOnly,)
    # filter_backends = (DjangoFilterBackend, )
    # filterset_class = ProjectFilter

    @action(detail=False, methods=['GET'])
    def get_queryset(self):
        projects = Project.objects.all()
        if 'capitals' in self.request.data:
            capitals = self.request.data['capitals']
            if capitals:
                projects = projects.filter(capital__in=capitals)

        if 'categories' in self.request.data:
            categories = self.request.data['categories']
            if categories:
                project_list = []
                for project in projects:
                    if not project.categories.all():
                        project_list.append(project.id)
                        continue
                    for category in project.categories.all():
                        if category.id in categories:
                            project_list.append(project.id)
                            break
                projects = Project.objects.filter(id__in=project_list)

        return projects

    @action(detail=True, methods=['GET'])
    def find_investors(self, request, pk=None):
        project = Project.objects.get(id=pk)
        investors = Investor.objects.filter(capital=project.capital)

        investor_list = []
        for investor in investors:
            for category in investor.categories.all():
                if category in project.categories.all():
                    investor_list.append(investor.id)
                    break
        investors = Investor.objects.filter(id__in=investor_list)

        # sort by avg_rating
        investors = sorted(investors.all(), key=lambda t: t.avg_rating())

        if investors:
            serializer = InvestorSerializer(investors, many=True)
            response = {'message': 'Investors found', 'result': serializer.data}
            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'Investors not found'}
            return Response(response, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'])
    def rate_project(self, request, pk=None):
        if 'stars' in request.data:

            project = Project.objects.get(id=pk)
            stars = request.data['stars']
            user = request.user

            try:
                rating = Rating.objects.get(user=user.id, project=project.id)
                rating.stars = stars
                rating.save()
                serializer = RatingSerializer(rating, many=False)
                response = {'message': 'Rating updated', 'result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)

            except:
                rating = Rating.objects.create(user=user, project=project, stars=stars)
                serializer = RatingSerializer(rating, many=False)
                response = {'message': 'Rating created', 'result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)

        else:
            response = {'message': 'You need to provide stars'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        response = {'message': 'You cant create rating like that'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        response = {'message': 'You cant update rating like that'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)