from django.contrib import admin
from .models import Lesson, Exercise, Progress, Draft, Attempt, PracticeEvent, Conversation, Message

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'track', 'order', 'version']
    list_filter = ['track']
    search_fields = ['title']

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'difficulty', 'source']
    search_fields = ['title']

admin.site.register([Progress, Draft, Attempt, PracticeEvent, Conversation, Message])
