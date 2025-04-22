from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, get_object_or_404, redirect
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
        if getattr(request.user, 'role', None) != 'teacher':
            raise PermissionDenied("Доступ запрещен. Вход только учителям")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_user_courses(user):
    if user.role == 'teacher':
        return Course.objects.filter(teacher=user)
    return Course.objects.filter(students=user)

# Главная страница
def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html', {
            'courses': Course.objects.all(),
            'homeworks': Homework.objects.none(),
            'lessons': Lesson.objects.none(),
            'quizzes': Quiz.objects.none(),
            'teachers': User.objects.filter(role='teacher'),
        })

    user_courses = get_user_courses(request.user)
    lessons = Lesson.objects.filter(course__in=user_courses)
    quizzes = Quiz.objects.filter(course__in=user_courses)
    homeworks = Homework.objects.filter(course__in=user_courses)

    return render(request, 'home.html', {
        'courses': user_courses,
        'homeworks': homeworks,
        'lessons': lessons,
        'quizzes': quizzes,
        'teachers': User.objects.filter(role='teacher'),
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
                if getattr(user, 'role', None) == 'student':
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
    return redirect("online_courses:home")

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

# Детали курса@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_teacher = request.user == course.teacher
    is_enrolled = course.students.filter(id=request.user.id).exists()

    if is_teacher or is_enrolled:
        quizzes = course.quizzes.all()  # Получаем все квизы для курса
        modules = course.modules.prefetch_related('lessons')  # Получаем модули и связанные уроки
    else:
        quizzes = []  # Не передаём квизы, если пользователь не подписан и не преподаватель
        modules = []  # Не передаём модули, если пользователь не подписан и не преподаватель

    return render(request, "course_detail.html", {
        "course": course,
        "is_teacher": is_teacher,
        "is_enrolled": is_enrolled,
        "quizzes": quizzes,
        "modules": modules,  # Передаём модули в шаблон
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
        course.students.add(request.user)  # Add the student to the course
        messages.success(request, f"Вы успешно записались на курс: {course.title}.")
        return redirect('online_courses:course_detail', course_id=course.id)

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

@login_required
@teacher_required
def add_module_and_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        if 'add_module' in request.POST:  # Добавление модуля
            module_title = request.POST.get('module_title')
            if module_title:
                Module.objects.create(course=course, title=module_title)
                messages.success(request, "Модуль успешно добавлен.")
            else:
                messages.error(request, "Название модуля не может быть пустым.")
        
        elif 'add_lesson' in request.POST:  # Добавление урока
            lesson_title = request.POST.get('lesson_title')
            module_id = request.POST.get('lesson_module')
            lesson_content = request.POST.get('lesson_content')

            if not lesson_title or not module_id:
                messages.error(request, "Название урока и модуль обязательны.")
            else:
                module = get_object_or_404(Module, id=module_id, course=course)
                Lesson.objects.create(course=course, module=module, title=lesson_title, content=lesson_content)
                messages.success(request, "Урок успешно добавлен.")

        return redirect('online_courses:add_module_and_lesson', course_id=course.id)

    modules = Module.objects.filter(course=course)
    return render(request, 'add_module_and_lesson.html', {'course': course, 'modules': modules})

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

    # Проверка, что только студенты могут отправлять домашние задания
    if request.user.role != 'student':
        raise PermissionDenied("Только студенты могут отправлять домашние задания.")

    if request.method == 'POST':
        submission_text = request.POST.get('submission_text')
        file = request.FILES.get('file_submission')  # Получаем файл из формы

        # Создаем запись о домашнем задании
        submission = HomeworkSubmission.objects.create(
            homework=homework,
            student=request.user,
            submission_text=submission_text,
            file_submission=file  # Сохраняем файл, если он был прикреплен
        )

        messages.success(request, "Домашнее задание успешно отправлено.")
        return redirect('online_courses:student_dashboard')  # Перенаправление на дашборд студента

    return render(request, 'submit_homework.html', {'homework': homework})

@login_required
def student_submissions(request):
    submissions = HomeworkSubmission.objects.filter(student=request.user)

    return render(request, 'student_submissions.html', {'submissions': submissions})

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

            # Перезагружаем объект из базы, чтобы получить актуальный статус
            submission.refresh_from_db()

            # Проверка актуального статуса
            if submission.status == 'rejected':
                messages.warning(request, "Статус: Отклонена.")
            elif submission.status == 'pending':

                messages.success(request, "Оценка: На проверке.")
            else:
                messages.success(request, "Оценка успешно обновлена.")

            return redirect('online_courses:review_homework', submission_id=submission.id)  # Перенаправление на ту же страницу для отображения обновлённой оценки
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
            messages.success(request, "Курс успешно добавлен.")
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
def add_quiz(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        return redirect("online_courses:home")  # Only teachers can add quizzes

    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course

            lesson_id = request.POST.get("lesson")
            if lesson_id:
                lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
                quiz.lesson = lesson

            quiz.save()
            messages.success(request, "Квиз успешно добавлен.")
            return redirect('online_courses:course_detail', course_id=course.id)
        else:
            messages.error(request, "Ошибка при добавлении квиза. Проверьте форму.")
    else:
        form = QuizForm()

    lessons = course.lessons.all()  # Get all lessons for the course
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
        raise PermissionDenied("Вы не имеете доступа к этой странице.")
    
    assignments = Homework.objects.filter(assigned_to=request.user)
    quizzes = Quiz.objects.filter(course__students=request.user)

    return render(request, 'student_dashboard.html', {
        'assignments': assignments,
        'quizzes': quizzes,
    })

@login_required
def available_courses(request):
    # Fetch courses the user is not enrolled in
    enrolled_courses = request.user.enrolled_courses.all() if request.user.role == 'student' else []
    available_courses = Course.objects.exclude(id__in=enrolled_courses)

    return render(request, 'available_courses.html', {'available_courses': available_courses})

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