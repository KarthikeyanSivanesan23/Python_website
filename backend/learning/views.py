import json
import time
from pathlib import Path
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import connection, transaction, IntegrityError
from django.db.models import F
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import serializers
from .models import Lesson, Exercise, Draft, Attempt, Progress, PracticeEvent, Conversation, Message
from .serializers import LessonSerializer, DraftSerializer, SubmissionSerializer, AttemptSerializer, ProgressSerializer, MentorSerializer
from . import mentor


class AuthThrottle(AnonRateThrottle):
    scope = 'auth'


class MentorThrottle(UserRateThrottle):
    scope = 'mentor'


def user_data(user):
    return {'id': user.id, 'username': user.username} if user.is_authenticated else None


@api_view(['GET'])
@permission_classes([AllowAny])
def session(request):
    return Response({'user': user_data(request.user), 'csrfToken': get_token(request)})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
@csrf_protect
def auth(request, action):
    if action == 'signout':
        logout(request)
        return Response({'user': None, 'csrfToken': get_token(request)})
    if action not in ['signup', 'signin']:
        return Response({'detail': 'Unknown authentication action.'}, status=404)
    username, password = request.data.get('username'), request.data.get('password')
    if not isinstance(username, str) or not isinstance(password, str) or not 3 <= len(username) <= 40 or len(password) > 128:
        return Response({'detail': 'Use a username of 3–40 characters and a password of at most 128 characters.'}, status=400)
    if not all(c.isalnum() or c in '_-.' for c in username):
        return Response({'detail': 'Username may contain letters, numbers, dots, underscores, and hyphens.'}, status=400)
    if action == 'signup':
        try:
            validate_password(password, User(username=username))
            user = User.objects.create_user(username=username, password=password)
        except ValidationError as exc:
            return Response({'detail': ' '.join(exc.messages)}, status=400)
        except IntegrityError:
            return Response({'detail': 'That username is already in use.'}, status=400)
    else:
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': 'Username or password is incorrect.'}, status=400)
    login(request, user)
    return Response({'user': user_data(user), 'csrfToken': get_token(request)})


def database_status():
    db = True
    local_cluster_match = False
    config = connection.settings_dict
    configured = {key.lower(): str(config.get(key, '')) for key in ['HOST', 'PORT', 'USER', 'NAME']}
    expected = {'name': 'python_studio', 'user': 'studio_test', 'host': '127.0.0.1', 'port': 55432}
    observed = None
    mismatches = []
    failure = None
    phase = 'connection_query'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            if connection.vendor == 'postgresql':
                # inet::text includes a /32 mask; host(inet) returns just the address.
                phase = 'identity_query'
                cursor.execute('SELECT current_database(), current_user, host(inet_server_addr()), inet_server_port()')
                observed = dict(zip(['name', 'user', 'host', 'port'], cursor.fetchone()))
                mismatches = [field for field in expected if observed[field] != expected[field]]
                local_cluster_match = not mismatches
        phase = 'schema_query'
        Lesson.objects.exists()
    except Exception as exc:
        db = False
        failure = {'phase': phase, 'type': type(exc).__name__}
    return {'backend': True, 'database': db, 'database_engine': connection.vendor, 'local_cluster_match': local_cluster_match,
            'database_message': 'Ready' if db else 'Configure DATABASE_URL, run migrations, and seed content.',
            'identity': {'expected': expected, 'observed': observed, 'configured': configured, 'mismatched_fields': mismatches},
            'failure': failure}


@api_view(['GET'])
@permission_classes([AllowAny])
def database_readiness(request):
    # Independent probe: never contacts or waits for Ollama.
    return Response(database_status())


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness(request):
    return Response({**database_status(), 'ollama': mentor.readiness()})


@api_view(['GET'])
@permission_classes([AllowAny])
def curriculum(request):
    rows = Lesson.objects.order_by('track', 'order').values('id', 'title', 'track', 'order', 'summary', 'content__minutes')
    return Response(list(rows))


@api_view(['GET'])
@permission_classes([AllowAny])
def lesson(request, slug):
    return Response(LessonSerializer(get_object_or_404(Lesson.objects.select_related('exercise'), pk=slug)).data)


@api_view(['GET', 'PUT'])
def draft(request, slug):
    exercise = get_object_or_404(Exercise, pk=slug)
    obj = Draft.objects.filter(user=request.user, exercise=exercise).first()
    if request.method == 'GET':
        return Response(DraftSerializer(obj).data if obj else {'code': exercise.starter, 'revision': 0, 'updated_at': None})
    data = DraftSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    with transaction.atomic():
        obj, _ = Draft.objects.get_or_create(user=request.user, exercise=exercise, defaults={'code': exercise.starter})
        obj = Draft.objects.select_for_update().get(pk=obj.pk)
        if data.validated_data.get('revision') != obj.revision:
            return Response({'detail': 'This draft changed in another tab. Reload the saved draft before overwriting it.', 'draft': DraftSerializer(obj).data}, status=409)
        obj.code = data.validated_data['code']
        obj.revision += 1
        obj.save()
    return Response(DraftSerializer(obj).data)


@api_view(['POST'])
def submit(request, slug):
    exercise = get_object_or_404(Exercise.objects.select_related('lesson'), pk=slug)
    serializer = SubmissionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    results = data['results']
    if len(results) != len(exercise.tests) or [r['name'] for r in results] != [t['name'] for t in exercise.tests]:
        return Response({'detail': 'Results do not match the current exercise test set. Reload the lesson.'}, status=400)
    events = PracticeEvent.objects.filter(user=request.user, exercise=exercise)
    obj = Attempt.objects.create(user=request.user, exercise=exercise, code=data['code'], results=results,
        passed=all(r['status'] == 'passed' for r in results), hints_used=events.filter(kind__in=['hint', 'mentor']).count(),
        solution_viewed=events.filter(kind='solution').exists(), lesson_version=exercise.lesson.version)
    Progress.objects.get_or_create(user=request.user, lesson=exercise.lesson)
    return Response(AttemptSerializer(obj).data, status=201)


@api_view(['POST'])
def reveal(request, slug, kind):
    exercise = get_object_or_404(Exercise, pk=slug)
    if kind == 'solution':
        PracticeEvent.objects.create(user=request.user, exercise=exercise, kind=kind)
        return Response({'solution': exercise.solution, 'explanation': exercise.explanation})
    if kind != 'hint':
        return Response(status=404)
    level = request.data.get('level', 0)
    if not isinstance(level, int) or isinstance(level, bool) or not 0 <= level < len(exercise.hints):
        return Response({'detail': 'Invalid hint level.'}, status=400)
    PracticeEvent.objects.create(user=request.user, exercise=exercise, kind='hint', level=level)
    return Response({'hint': exercise.hints[level]})


@api_view(['POST'])
def progress(request, slug):
    obj_lesson = get_object_or_404(Lesson, pk=slug)
    seconds = request.data.get('active_seconds', 0)
    complete = request.data.get('completed')
    if type(seconds) is not int or not 0 <= seconds <= 30 or (complete is not None and type(complete) is not bool):
        return Response({'detail': 'Invalid progress update.'}, status=400)
    obj, _ = Progress.objects.get_or_create(user=request.user, lesson=obj_lesson)
    # Cap active time by real elapsed wall time, even if clients send duplicate heartbeats.
    elapsed = max(0, int((timezone.now() - obj.updated_at).total_seconds()))
    updates = {'active_seconds': F('active_seconds') + min(seconds, elapsed), 'updated_at': timezone.now()}
    if complete is not None:
        updates['completed'] = complete
    Progress.objects.filter(pk=obj.pk).update(**updates)
    obj.refresh_from_db()
    return Response(ProgressSerializer(obj).data)


@api_view(['GET'])
def dashboard(request):
    progress_rows = Progress.objects.filter(user=request.user).order_by('-updated_at')
    attempts = Attempt.objects.filter(user=request.user).select_related('exercise__lesson').order_by('-created_at')
    revisits, seen = [], set()
    for attempt in attempts[:200]:
        if attempt.exercise_id in seen:
            continue
        seen.add(attempt.exercise_id)
        if not attempt.passed or attempt.hints_used or attempt.solution_viewed:
            revisits.append({'lesson': attempt.exercise.lesson_id, 'title': attempt.exercise.title,
                             'reason': 'Latest attempt did not pass all checks.' if not attempt.passed else 'Practised with guidance; try again from memory.'})
    return Response({'progress': ProgressSerializer(progress_rows, many=True).data, 'attempts': AttemptSerializer(attempts[:20], many=True).data,
                     'resume': progress_rows.first().lesson_id if progress_rows.exists() else 'values', 'revisit': revisits[:8],
                     'rules': 'Completion is self-marked after study. Test feedback is browser-reported. Revisit suggestions use the latest attempt and recorded guidance usage, not a trained model. Time is approximate active practice, excluding idle tabs.'})


@api_view(['GET', 'POST'])
@throttle_classes([MentorThrottle])
def conversation(request, slug):
    exercise = get_object_or_404(Exercise.objects.select_related('lesson'), pk=slug)
    conv, _ = Conversation.objects.get_or_create(user=request.user, exercise=exercise)
    if request.method == 'GET':
        rows = list(conv.messages.order_by('-id').values('role', 'text', 'created_at')[:20])
        return Response(list(reversed(rows)))
    serializer = MentorSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if not mentor.inference_gate.acquire(blocking=False):
        return Response({'detail': 'Mentor is helping another learner. Try again shortly.'}, status=429)
    try:
        status = mentor.readiness()
        if not status['model_available']:
            return Response({'detail': status['message']}, status=503)
        history = list(conv.messages.order_by('-id').values('role', 'text')[:6])
        history = [{'role': row['role'], 'content': row['text'][:2000]} for row in reversed(history)]
        answer = mentor.generate(exercise, data, history)
        with transaction.atomic():
            Message.objects.create(conversation=conv, role='user', text=data['message'])
            Message.objects.create(conversation=conv, role='assistant', text=answer)
            PracticeEvent.objects.create(user=request.user, exercise=exercise, kind='mentor')
        return Response({'text': answer, 'revision': data['revision'], 'model': settings.OLLAMA_MODEL})
    except Exception:
        return Response({'detail': 'Ollama did not finish a valid response within the request limits. Check that the configured model runs with ollama run, then retry. Your code and execution controls are still available.'}, status=503)
    finally:
        mentor.inference_gate.release()
