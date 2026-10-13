from django.conf import settings
from django.db import models


class Lesson(models.Model):
    id = models.SlugField(primary_key=True)
    track = models.CharField(max_length=12, choices=[('python', 'Python'), ('dsa', 'DSA')])
    order = models.PositiveIntegerField()
    title = models.CharField(max_length=160)
    summary = models.CharField(max_length=300)
    content = models.JSONField(default=dict)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['track', 'order']

    def __str__(self):
        return self.title


class Exercise(models.Model):
    id = models.SlugField(primary_key=True)
    lesson = models.OneToOneField(Lesson, related_name='exercise', on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    statement = models.TextField()
    difficulty = models.CharField(max_length=20, default='Beginner')
    starter = models.TextField()
    tests = models.JSONField(default=list)
    hints = models.JSONField(default=list)
    solution = models.TextField()
    explanation = models.TextField()
    examples = models.JSONField(default=list)
    constraints = models.JSONField(default=list)
    prerequisites = models.JSONField(default=list)
    source = models.CharField(max_length=100, default='Original curriculum exercise')

    def __str__(self):
        return self.title


class Progress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    active_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'lesson'], name='unique_progress')]


class Draft(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    code = models.TextField()
    revision = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'exercise'], name='unique_draft')]


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    code = models.TextField()
    results = models.JSONField()
    passed = models.BooleanField(default=False)
    hints_used = models.PositiveIntegerField(default=0)
    solution_viewed = models.BooleanField(default=False)
    lesson_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class PracticeEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20, choices=[('hint', 'Hint'), ('solution', 'Solution'), ('mentor', 'Mentor')])
    level = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'exercise'], name='unique_conversation')]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=12)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
