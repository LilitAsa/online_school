from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotFound
from django.core.exceptions import PermissionDenied
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Quiz, Question, Answer, StudentAnswer
from django.contrib import messages


# Главная страница
def home(request):
    courses = Course.objects.all()
    homeworks = Homework.objects.all()
    return render(request, 'home.html', {'courses': courses, 'homeworks': homeworks})

User = get_user_model()

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Вы вошли как {username}.")
                if user.role == 'student':
                    return redirect('online_courses:student_dashboard')
                else:
                    return redirect('online_courses:home')
            else:
                messages.error(request, "Неверное имя пользователя или пароль.")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
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
    is_enrolled = course.students.filter(id=request.user.id).exists()
    return render(request, 'course_detail.html', {'course': course, 'is_enrolled': is_enrolled})

# Modules
@login_required
def module_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'module_list.html', {'course': course})

# Lesson details
@login_required
def lesson_detail(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    return render(request, 'lesson_detail.html', {'course': course, 'lesson': lesson})

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


@login_required
def add_homework(request):
    if request.user.role != 'teacher':
        raise PermissionDenied("Только преподаватели могут добавлять домашние задания.")
    
    if request.method == 'POST':
        form = HomeworkForm(request.POST)
        if form.is_valid():
            homework = form.save(commit=False)
            homework.assigned_by = request.user
            homework.save()
            return redirect('online_courses:home')
    else:
        form = HomeworkForm()
    
    return render(request, 'add_homework.html', {'form': form})

# Прохождение теста
@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    if request.method == 'POST':
        correct_count = 0
        total_questions = len(questions)  # Считаем количество вопросов

        for question in questions:
            selected_answer = request.POST.get(f'question_{question.id}')
            
            # Проверяем, что ответ был выбран
            if selected_answer is None:
                messages.error(request, f"Вы не ответили на вопрос: {question.text}")
                return redirect('online_courses:take_quiz', quiz_id=quiz.id)

            # Приводим к строке, если ответы сравниваются неправильно
            correct_answer_text = str(question.correct_answer).strip().lower()
            selected_answer_text = str(selected_answer).strip().lower()

            is_correct = selected_answer_text == correct_answer_text

            # Создаём объект ответа студента
            StudentAnswer.objects.create(
                student=request.user,
                quiz=quiz,  # Должно быть обязательно
                question=question,
                selected_answer=selected_answer_text,
                is_correct=is_correct
            )

            if is_correct:
                correct_count += 1

        # Избегаем деления на 0
        score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0

        return render(request, 'quiz_result.html', {'quiz': quiz, 'score': round(score_percentage, 2)})

    return render(request, 'take_quiz.html', {'quiz': quiz, 'questions': questions})
# Отправка домашнего задания
@login_required
def submit_homework(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)

    if request.user.role != 'student':
        raise PermissionDenied("Только студенты могут отправлять домашние задания.")

    if request.method == 'POST':
        submission_text = request.POST.get('submission_text')
        HomeworkSubmission.objects.create(
            homework=homework,
            student=request.user,
            submission_text=submission_text
        )
        messages.success(request, "Домашнее задание успешно отправлено.")
        return redirect('online_courses:student_dashboard')

    return render(request, 'submit_homework.html', {'homework': homework})

# Проверка домашних заданий
@login_required
def review_homework(request, submission_id):
    submission = HomeworkSubmission.objects.filter(id=submission_id).first()

    if not submission:
        return HttpResponseNotFound("HomeworkSubmission not found.")

    # Check if the user is a teacher
    if not hasattr(request.user, 'role') or request.user.role != 'teacher':
        raise PermissionDenied("You do not have permission to review this homework.")

    if request.method == "POST":
        form = ReviewHomeworkForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            if submission.status == 'rejected':
                messages.warning(request, "Статус: Отклонена.")
            elif submission.status == 'pending':
                messages.warning(request, "Статус: На проверке.")
            else:
                messages.success(request, "Оценка успешно обновлена.")
            return redirect('online_courses:review_homework', submission_id=submission.id)  # Redirect to the same page to see the updated grade
    else:
        form = ReviewHomeworkForm(instance=submission)

    return render(request, 'review_homework.html', {'form': form, 'submission': submission})

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

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        raise PermissionDenied("Только студенты могут просматривать эту страницу.")

    # Get the list of assignments for the student
    assignments = Homework.objects.filter(course__students=request.user)
    quizzes = Quiz.objects.filter(lesson__module__course__students=request.user)

    return render(request, 'student_dashboard.html', {'assignments': assignments, 'quizzes': quizzes})