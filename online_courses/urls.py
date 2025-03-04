from django.urls import path
from .views import *

app_name = 'online_courses'

urlpatterns = [
    path('', home, name='home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', register, name='register'),
    
    # Курсы
    path('courses/', course_list, name='course_list'),
    path('course/<int:course_id>/', course_detail, name='course_detail'),
    path('course/<int:course_id>/modules/', module_list, name='module_list'),
    path('course/<int:lesson_id>/detail/', lesson_detail, name='lesson_detail'),
    path('course/<int:lesson_id>/enroll/', enroll_course, name='enroll_course'),

    # Управление курсами (только для преподавателей)
    path('courses/manage/', manage_courses, name='manage_courses'),
    path('courses/add/', add_course, name='add_course'),
    path('courses/delete/<int:course_id>/', delete_course, name='delete_course'),
    path('manage_courses/', manage_courses, name='manage_courses'),
    path('add_course/', add_course, name='add_course'),
    # Прохождение тестов                                                        
    path('quiz/<int:quiz_id>/', take_quiz, name='take_quiz'),

    # Домашние задания
    path('homework/<int:homework_id>/submit/', submit_homework, name='submit_homework'),
    path('homework/<int:homework_id>/review/', review_homework, name='review_homework'),
]
