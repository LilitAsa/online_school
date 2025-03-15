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
from functools import wraps

def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role != 'teacher':
            raise PermissionDenied("Доступ запрещен. Вход только учителям")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# Главная страница
def home(request):
    courses = Course.objects.all()
    homeworks = Homework.objects.all()
    lessons = Lesson.objects.none()  
    quizzes = Quiz.objects.none() 
    teachers = User.objects.filter(role='teacher')
    
    print()
    
    if request.user.is_authenticated:
        if request.user.role == 'teacher':
            lessons = Lesson.objects.filter(course__teacher=request.user)
            quizzes = Quiz.objects.filter(course__teacher=request.user)
            homeworks = Homework.objects.filter(course__teacher=request.user)
            homeworks = Homework.objects.none()
            
        else:
            lessons = Lesson.objects.filter(course__students=request.user)
            quizzes = Quiz.objects.filter(course__students=request.user)
            homeworks = Homework.objects.filter(course__students=request.user) 
            
    return render(request, 'home.html', {
        'courses': courses,
        'homeworks': homeworks,
        'lessons': lessons,
        'quizzes': quizzes,
        'homeworks': homeworks,
        'teachers': teachers,
    })
    
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
    is_teacher = request.user == course.teacher
    is_enrolled = course.students.filter(id=request.user.id).exists()

    if is_teacher or is_enrolled:
        quizzes = course.quizzes.all()  # Получаем все квизы для курса
    else:
        quizzes = []  # Не передаём квизы, если пользователь не подписан и не преподаватель

    return render(request, "course_detail.html", {
        "course": course,
        "is_teacher": is_teacher,
        "is_enrolled": is_enrolled,
        "quizzes": quizzes,
    })


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

@teacher_required
@login_required
def add_homework(request):
    if request.method == 'POST':
        form = HomeworkForm(request.POST)
        if form.is_valid():
            homework = form.save(commit=False)
            homework.assigned_by = request.user
            homework.course = form.cleaned_data.get('course')
            homework.save()
            print(f"Домашнее задание {homework.title} добавлено для курса {homework.course}")
            return redirect('online_courses:home')
        else:
            print("Форма невалидна:", form.errors)
    else:
        form = HomeworkForm()
    
    return render(request, 'add_homework.html', {'form': form})

# Прохождение теста
@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all() 
    is_teacher = request.user == quiz.course.teacher

    if is_teacher:
        return render(request, "quiz_detail.html", {"quiz": quiz, "questions": questions})

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

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user != quiz.course.teacher:
        return redirect("home")  # Разрешено только учителям

    questions = quiz.questions.all()
    return render(request, "quiz_detail.html", {"quiz": quiz, "questions": questions})

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
@teacher_required
@login_required
def review_homework(request, submission_id):
    submission = HomeworkSubmission.objects.filter(id=submission_id).first()

    if not submission:
        return HttpResponseNotFound("HomeworkSubmission not found.")

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

@teacher_required
@login_required
def add_course(request):
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

@login_required
def add_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        return redirect("home")  

    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect("course_detail", course_id=course.id)
    else:
        form = LessonForm()

    return render(request, "add_lesson.html", {"form": form, "course": course})

@login_required
def add_quiz(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lesson_id = request.POST.get("lesson")
    
    if lesson_id:
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        if lesson.course != course:
            return redirect("home")  # Защита от подмены данных
        quiz.lesson = lesson

    if request.user != course.teacher:
        return redirect("home")  

    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course

            lesson_id = request.POST.get("lesson")
            if lesson_id:
                quiz.lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
            
            quiz.lesson = lesson
            quiz.save()
            return redirect('online_courses:course_detail', course_id=course.id)
    else:
        form = QuizForm()

    lessons = course.lessons.all()  

    return render(request, "add_quiz.html", {"form": form, "course": course, "lessons": lessons})

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user != quiz.course.teacher:
        return redirect("home")

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz  # Привязываем вопрос к квизу
            question.save()
            return redirect("online_courses:course_detail", course_id=quiz.course.id)
    else:
        form = QuestionForm()

    return render(request, "add_question.html", {"form": form, "quiz": quiz})

@login_required
def quiz_list(request):
    if request.user.is_staff:  # Администратор видит все квизы
        quizzes = Quiz.objects.all()
    elif request.user.role == 'teacher':
        quizzes = Quiz.objects.filter(course__teacher=request.user)
    else:
        quizzes = Quiz.objects.filter(course__students=request.user)
    return render(request, 'quiz_list.html', {'quizzes': quizzes})

def account(request):
    return render(request, 'account.html')

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        raise PermissionDenied("Только студенты могут просматривать эту страницу.")

    # Get the list of assignments for the student
    assignments = Homework.objects.filter(course__students=request.user)
    quizzes = Quiz.objects.filter(course__students=request.user)

    return render(request, 'student_dashboard.html', {'assignments': assignments, 'quizzes': quizzes})

def teacher_list(request):
    teachers = User.objects.filter(role='teacher')
    return render(request, 'teachers.html', {'teachers': teachers})

def student_list(request):
    students = User.objects.filter(role='student')
    return render(request, 'students.html', {'students': students})

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def privacy(request):
    return render(request, 'privacy.html')