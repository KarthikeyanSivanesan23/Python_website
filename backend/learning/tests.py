import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .curriculum import LESSONS
from .models import Attempt, Conversation, Draft, Exercise, Lesson, Message, PracticeEvent, Progress


class LearningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_content', verbosity=0)
        cls.alice = User.objects.create_user('alice', password='Private-test-password-912!')
        cls.bob = User.objects.create_user('bob', password='Private-test-password-613!')

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.client.force_login(self.alice)

    def test_seed_is_idempotent_and_references_valid(self):
        call_command('seed_content', verbosity=0)
        self.assertEqual(Lesson.objects.count(), 24)
        self.assertEqual(Exercise.objects.count(), 24)
        ids = {l['id'] for l in LESSONS}
        for lesson in LESSONS:
            self.assertTrue(all(p in ids for p in lesson['content']['prerequisites']))
            for frame in lesson['content']['demo']['steps']:
                self.assertLessEqual(frame['line'], len(lesson['content']['demo']['code'].splitlines()))

    def test_initial_content_does_not_reveal_answers(self):
        response = self.client.get('/api/lessons/values/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('solution', response.data['exercise'])
        self.assertNotIn('hints', response.data['exercise'])
        self.assertEqual(response.data['exercise']['source'], 'Original curriculum exercise')

    def test_draft_ownership_reload_and_revision_conflict(self):
        url = '/api/exercises/values-practice/draft/'
        response = self.client.put(url, {'code': 'print("private draft")', 'revision': 0}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.put(url, {'code': 'stale', 'revision': 0}, format='json').status_code, 409)
        self.client.logout()
        self.assertIn(self.client.get(url).status_code, [401, 403])
        self.assertTrue(self.client.login(username='alice', password='Private-test-password-912!'))
        self.assertEqual(self.client.get(url).data['code'], 'print("private draft")')
        self.client.force_login(self.bob)
        self.assertNotEqual(self.client.get(url + '?user=1').data['code'], 'print("private draft")')
        self.client.put(url, {'code': 'bob code', 'revision': 0, 'user': self.alice.id}, format='json')
        self.assertEqual(Draft.objects.get(user=self.alice).code, 'print("private draft")')

    def test_attempts_progress_and_guidance_are_owned(self):
        exercise = Exercise.objects.get(pk='values-practice')
        self.client.post('/api/exercises/values-practice/reveal/hint/', {'level': 0}, format='json')
        self.client.post('/api/exercises/values-practice/reveal/solution/', {}, format='json')
        data = {'code': 'print("Ada is 20")', 'results': [{'name': 'Introduction', 'status': 'passed', 'actual': 'Ada is 20', 'expected': 'Ada is 20'}], 'user': self.bob.id}
        response = self.client.post('/api/exercises/values-practice/submit/', data, format='json')
        self.assertEqual(response.status_code, 201)
        attempt = Attempt.objects.get()
        self.assertEqual(attempt.user, self.alice)
        self.assertEqual(attempt.hints_used, 1)
        self.assertTrue(attempt.solution_viewed)
        self.client.post('/api/progress/values/', {'completed': True, 'active_seconds': 30}, format='json')
        # No open-tab time is fabricated by back-to-back requests.
        self.assertLess(Progress.objects.get().active_seconds, 3)
        self.assertTrue(self.client.get('/api/dashboard/').data['revisit'])
        self.client.force_login(self.bob)
        other = self.client.get('/api/dashboard/?user=' + str(self.alice.id)).data
        self.assertEqual(other['attempts'], [])
        self.assertEqual(other['progress'], [])
        self.assertEqual(PracticeEvent.objects.filter(user=self.bob).count(), 0)

    def test_validation_and_anonymous_protection(self):
        self.assertEqual(self.client.put('/api/exercises/values-practice/draft/', {'code': 'x' * 20001, 'revision': 0}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/progress/values/', {'active_seconds': 1000}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/exercises/values-practice/reveal/hint/', {'level': -1}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/exercises/values-practice/submit/', {'code': '', 'results': []}, format='json').status_code, 400)
        self.client.logout()
        for path in ['dashboard/', 'exercises/values-practice/draft/', 'exercises/values-practice/mentor/']:
            self.assertIn(self.client.get('/api/' + path).status_code, [401, 403])
        self.assertEqual(self.client.get('/api/curriculum/').status_code, 200)

    def test_authentication_csrf_and_new_session(self):
        client = APIClient(enforce_csrf_checks=True)
        token = client.get('/api/session/').data['csrfToken']
        data = {'username': 'learner_new', 'password': 'Uncommon-Test-Password-761!'}
        self.assertEqual(client.post('/api/auth/signup/', data, format='json').status_code, 403)
        response = client.post('/api/auth/signup/', data, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        token = response.data['csrfToken']
        response = client.post('/api/auth/signout/', {}, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        response = client.post('/api/auth/signin/', data, format='json', HTTP_X_CSRFTOKEN=response.data['csrfToken'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['username'], data['username'])

    @patch('learning.mentor.readiness', return_value={'reachable': False, 'model_available': False, 'model': 'missing', 'message': 'Start Ollama.'})
    def test_unavailable_mentor_is_honest(self, mocked):
        data = {'mode': 'coach', 'message': 'Help', 'code': 'print(1)', 'revision': 1}
        self.assertEqual(self.client.post('/api/exercises/values-practice/mentor/', data, format='json').status_code, 503)
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(self.client.get('/api/lessons/values/').status_code, 200)

    @patch('learning.mentor.generate', return_value='Consider which type input() returns.')
    @patch('learning.mentor.readiness', return_value={'model_available': True})
    def test_mentor_context_and_conversation_ownership(self, ready, generate):
        data = {'mode': 'coach', 'message': 'Help me understand', 'code': 'age = input()', 'feedback': 'TypeError', 'revision': 4}
        response = self.client.post('/api/exercises/input-output-practice/mentor/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['revision'], 4)
        self.assertEqual(generate.call_args.args[0].id, 'input-output-practice')
        self.assertEqual(generate.call_args.args[1]['feedback'], 'TypeError')
        self.assertEqual(len(self.client.get('/api/exercises/input-output-practice/mentor/').data), 2)
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get('/api/exercises/input-output-practice/mentor/').data, [])


class ReferenceContentTests(TestCase):
    """Execute only authored content offline, never learner code in a request process."""
    def test_all_reference_solutions_and_example_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            for lesson in LESSONS:
                checks = [{'name': 'lesson example', 'code': lesson['content']['example'], 'expected': lesson['content']['expected_output'], 'expression': '', 'stdin': ['Ada'] if lesson['id'] == 'input-output' else []}]
                checks += [{'name': extra['title'], 'code': extra['code'], 'expected': extra['expected_output'], 'expression': '', 'stdin': []} for extra in lesson['content'].get('extra_examples', [])]
                checks += [{**case, 'code': lesson['exercise']['solution']} for case in lesson['exercise']['tests']]
                for case in checks:
                    with self.subTest(lesson=lesson['id'], case=case['name']):
                        for name, text in {'data.txt': '3\n4\n5\n', 'empty.txt': '', 'signed.txt': '-5\n3\n'}.items():
                            Path(folder, name).write_text(text, encoding='utf-8')
                        script = case['code']
                        if case['expression']:
                            script += '\nimport json\nprint(json.dumps(' + case['expression'] + '))\n'
                        run = subprocess.run([sys.executable, '-I', '-c', script], cwd=folder, input=''.join(line + '\n' for line in case['stdin']), text=True, capture_output=True, timeout=3)
                        self.assertEqual(run.returncode, 0, run.stderr)
                        actual = json.loads(run.stdout.strip().splitlines()[-1]) if case['expression'] else run.stdout
                        self.assertEqual(actual, case['expected'])
