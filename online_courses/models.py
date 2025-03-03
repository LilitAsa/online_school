from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from ordered_model.models import OrderedModel

# Пользователь с ролями
class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор')
    ]
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    def __str__(self):
        return self.username

# Курс
class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'teacher'}, related_name='courses_taught')
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True, limit_choices_to={'role': 'student'})
     
    def clean(self):
        if self.teacher and self.teacher.role != 'teacher':
            raise ValidationError("Only teachers can be assigned to a course.")

        # Only perform this check if the object has been saved and has an id
        if self.pk and self.teacher and self.teacher in self.students.all():
            raise ValidationError("A teacher cannot be enrolled in their own course.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} (Teacher: {self.teacher.username if self.teacher else 'None'})"

# Прогресс студента по курсу
class Progress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, blank=True, null=True)
    progress_percentage = models.FloatField(default=0.0)

    def clean(self):
        if self.student.role != 'student':
            raise ValidationError("Only students can have progress records.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# Модуль курса
class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()
    order_with_respect_to = 'course'  # Сортировка только внутри курса
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} (Course: {self.course.title})"
    
# Урок
class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to='lessons/files/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} (Module: {self.module.title})"

# Запись на курс
class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_enrollments')
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('user', 'course')  # Запрещаем дублирующиеся записи
    
    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"

# Отзывы о курсе
class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review by {self.user.username} on {self.course.title}"

# Квиз
class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    def __str__(self):
        return self.title

# Вопрос к квизу
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    correct_answer = models.CharField(max_length=255)
    choices = models.TextField(help_text="Варианты ответов через запятую")  # Добавляем поле для вариантов ответов
    
    def get_choices(self):
        return self.choices.split(",")
    
    def __str__(self):
        return f"{self.text} (Quiz: {self.quiz.title})"

# Ответ студента на вопрос к квизу
class StudentAnswer(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.username} - {self.question.text} ({'Correct' if self.is_correct else 'Incorrect'})"

# Домашняя работа
class Homework(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    def __str__(self):
        return self.title

# Подача домашней работы
class HomeworkSubmission(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_text = models.TextField()
    file_submission = models.FileField(upload_to='homework_submissions/', blank=True, null=True)
    grade = models.IntegerField(null=True, blank=True)  # Оценка (если уже проверено)
    
    def __str__(self):
        return f"{self.student.username} - {self.homework.title}"
    
    def save(self, *args, **kwargs):
        if not self.grade:
            # Если оценка не указана, то автоматически считаем, что она 0
            self.grade = 0
        super().save(*args, **kwargs)