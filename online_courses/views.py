from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import *
from .forms import *
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model


# Главная страница
def home(request):
    courses = Course.objects.all()  
    return render(request, 'home.html', {'courses': courses})  


User = get_user_model()

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("online_courses:home")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def user_logout(request):
    logout(request) 
    return render(request, "logout.html")

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("online_courses:home")  
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form})

# Просмотр курсов
@login_required
def course_list(request):
    if request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
    else:
        courses = request.user.enrolled_courses.all()
    return render(request, 'course_list.html', {'courses': courses})

# Детали курса
@login_required
def course_detail(request, course_id):    
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'course_detail.html', {'course': course})

# Modules
@login_required
def module_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'module_list.html', {'course': course})

# Lesson details
@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'lesson_detail.html', {'lesson': lesson})

# Запись студента на курс
@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role != 'student':
        raise PermissionDenied("Только студенты могут записываться на курсы.")
    
    if request.method == "POST":
        Enrollment.objects.get_or_create(user=request.user, course=course)
        return redirect('online_courses:course_detail', course_id=course.id)
    
    course.students.add(request.user)

    return render(request, 'enroll_course.html', {'course': course})

# Прохождение теста
@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    if request.method == 'POST':
        correct_count = 0
        for question in questions:
            selected_answer = request.POST.get(f'question_{question.id}')
            is_correct = selected_answer == question.correct_answer

            StudentAnswer.objects.create(
                student=request.user,
                question=question,
                selected_answer=selected_answer,
                is_correct=is_correct
            )

            if is_correct:
                correct_count += 1

        score_percentage = (correct_count / len(questions)) * 100
        return render(request, 'quiz_result.html', {'quiz': quiz, 'score': score_percentage})

    return render(request, 'take_quiz.html', {'quiz': quiz, 'questions': questions})

# Отправка домашнего задания
@login_required
def submit_homework(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)

    if request.method == 'POST':
        submission_text = request.POST.get('submission_text')
        HomeworkSubmission.objects.create(
            homework=homework,
            student=request.user,
            submission_text=submission_text
        )
        return redirect('student_dashboard')

    return render(request, 'submit_homework.html', {'homework': homework})

# Проверка домашних заданий
@login_required
def review_homework(request, homework_id):
    if request.user.role != 'teacher':
        return redirect('index')

    submissions = HomeworkSubmission.objects.filter(homework_id=homework_id)

    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        grade = request.POST.get('grade')
        submission = HomeworkSubmission.objects.get(id=submission_id)
        submission.grade = grade
        submission.save()
        return redirect('online_courses:review_homework', homework_id=homework_id)

    return render(request, 'review_homework.html', {'submissions': submissions})

@login_required
def add_course(request):
    if request.user.role != 'teacher':
        raise PermissionDenied("Только преподаватели могут добавлять курсы.")

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)  # Create the Course object but don't save it yet
            course.teacher = request.user  # Set the teacher to the current user
            course.save()  # Save the Course object to the database
            form.save_m2m()  # Save the many-to-many data for the form
            course.students.add(request.user)  # Add the teacher to the students many-to-many field
            return redirect('online_courses:manage_courses')  # Redirect to the manage courses page
    else:
        form = CourseForm()

    return render(request, 'add_course.html', {'form': form})

@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        raise PermissionDenied("Вы можете удалять только свои курсы.")

    course.delete()
    return redirect('online_courses:manage_courses')

@login_required
def manage_courses(request):
    if request.user.role != 'teacher':
        raise PermissionDenied("Только преподаватели могут управлять курсами.")
    
    courses = Course.objects.filter(teacher=request.user)
    return render(request, 'manage_courses.html', {'courses': courses})

def account(request):
    return render(request, 'account.html')