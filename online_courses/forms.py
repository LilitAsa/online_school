from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.CharField(max_length=100)
    
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'role', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется. Выберите другой.")
        return email
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm Password'


class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
            
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username'
        self.fields['password'].label = 'Password'

class UserLogoutForm(forms.Form):
    pass


class CourseForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=Course.students.field.related_model.objects.all(),
        required=False,  
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Course
        fields = ['title', 'description', 'students'] 
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }



class LessonForm(forms.ModelForm):
    module = forms.ModelChoiceField(
        queryset=Module.objects.none(),  # Default to no modules
        label="Выберите модуль",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Lesson
        fields = ['title', 'content', 'module']

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)  # Pass the course to filter modules
        super().__init__(*args, **kwargs)
        if course:
            self.fields['module'].queryset = Module.objects.filter(course=course)
            
class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['title', 'description', 'course', 'due_date', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }      

class ReviewHomeworkForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['status', 'grade']
        labels = {
            'status': 'Статус',
            'grade': 'Оценка (по желанию)',
        }
    
    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade < 0 or grade > 100:
            raise forms.ValidationError("Оценка должна быть в диапазоне от 0 до 100.")
        return grade
        
class QuizForm(forms.ModelForm):
    lesson = forms.ModelChoiceField(
        queryset=Lesson.objects.all(),
        required=False,
        empty_label="Без урока"
    )
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'lesson', 'course']
        widgets = {
            'lesson': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz', 'text', 'correct_answer', 'choices']
        widgets = {
            'quiz': forms.Select(attrs={'class': 'form-control'}),
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-control'}),
        }   
        

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "content"]

        
class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']