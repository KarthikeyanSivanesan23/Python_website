from django.core.management.base import BaseCommand
from django.db import transaction
from learning.curriculum import LESSONS
from learning.models import Lesson, Exercise


class Command(BaseCommand):
    help = 'Idempotently seed the original Python and DSA curriculum (updates matching stable IDs).'

    @transaction.atomic
    def handle(self, *args, **options):
        for source in LESSONS:
            data = source.copy()
            exercise = data.pop('exercise').copy()
            lesson, _ = Lesson.objects.update_or_create(id=data.pop('id'), defaults=data)
            Exercise.objects.update_or_create(id=exercise.pop('id'), defaults={**exercise, 'lesson': lesson})
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(LESSONS)} original lessons and exercises. PDF import blocked: source file not supplied.'))
