from django.urls import path, include
from .views import *

app_name = 'online_courses'

urlpatterns = [
    path('', home, name='home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', register, name='register'),
    
    #Пользователи
    path('teachers', teacher_list, name='teacher_list'),
    path('students', student_list, name='student_list'),
    
    # Курсы
    path('courses/', course_list, name='course_list'),
    path('course/<int:course_id>/', course_detail, name='course_detail'),
    path('course/<int:course_id>/enroll/', enroll_course, name='enroll_course'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/', lesson_detail, name='lesson_detail'),

    # Управление курсами (только для преподавателей)
    path('courses/manage/', manage_courses, name='manage_courses'),
    path('courses/add/', add_course, name='add_course'),
    path('courses/delete/<int:course_id>/', delete_course, name='delete_course'),
    path('manage_courses/', manage_courses, name='manage_courses'),
    path('add_course/', add_course, name='add_course'),
    path('course/<int:course_id>/add_module_and_lesson/', add_module_and_lesson, name='add_module_and_lesson'),
    path('courses/available/', available_courses, name='available_courses'),
    
    path('account/', account, name='account'),
    
    # Домашние задания
    path('homework/add/', add_homework, name='add_homework'),
    path('homework/<int:homework_id>/submit/', submit_homework, name='submit_homework'),
    path('homework/<int:submission_id>/review/', review_homework, name='review_homework'),
      
    # Студенческая панель
    path('student_dashboard/', student_dashboard, name='student_dashboard'),
        
    # Прохождение тестов
    path("quiz/<int:quiz_id>/", take_quiz, name="take_quiz"),    
    path("course/<int:course_id>/add_quiz/", add_quiz, name="add_quiz"),
    path('quiz/<int:quiz_id>/add-question/', add_question, name='add_question'), 
    path('quiz/<int:quiz_id>/', quiz_detail, name='quiz_detail'),
    path('quizzes/', quiz_list, name='quiz_list'),
    
    #
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('privacy/', privacy, name='privacy'),
    ]