from django.contrib import admin
from .models import *

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher')  
    search_fields = ('title', 'teacher__username')  
    list_filter = ('teacher',)  
    

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_editable = ('order',)  
    list_filter = ('course',)
    ordering = ('course', 'order')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module')  
    search_fields = ('title', 'module__title')  
    list_filter = ('module',)  

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson','course')  
    search_fields = ('title', 'lesson__title')  
    list_filter = ('lesson','course')

class HomeworkAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Админ видит все
        return qs.filter(course__teacher=request.user)  # Учитель видит только свои

# admin.site.register(Homework, HomeworkAdmin)
admin.site.register(User)
admin.site.register(Question)
admin.site.register(StudentAnswer)
admin.site.register(Homework)
admin.site.register(HomeworkSubmission)
