from django.urls import path
from .import views

urlpatterns = [
    path('article/', views.ArticleViewSet.as_view({'post': 'create'}), name='article'),
    path('article/<int:pk>',
         views.ArticleViewSet.as_view({'get': 'retrieve', 'delete': 'destroy', 'patch': 'update'}),
         name='exact_article'),
    path('article/<int:pk>/files/', views.CreateArticleFileView.as_view(), name='article_files'),

    path('specialities', views.SpecialitiesView.as_view(), name='specialities'),
    path('specialities/<int:speciality_id>/years/<int:year>/subjects',
         views.SubjectsView.as_view(), name='subjects'),
    path('specialities/<int:speciality_id>/years/<int:year>/subjects/<int:subject_id>/articles',
         views.ArticlesView.as_view(), name='articles'),
    path('specialities/<int:speciality_id>/years/<int:year>/subjects/<int:subject_id>/teachers',
         views.TeachersView.as_view(), name='teachers'),
]
