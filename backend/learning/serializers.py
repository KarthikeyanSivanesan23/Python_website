from rest_framework import serializers
from .models import Lesson, Exercise, Draft, Attempt, Progress


class ExerciseSerializer(serializers.ModelSerializer):
    hint_count = serializers.SerializerMethodField()

    def get_hint_count(self, obj):
        return len(obj.hints)

    class Meta:
        model = Exercise
        fields = ['id', 'title', 'statement', 'difficulty', 'starter', 'tests', 'examples', 'constraints', 'prerequisites', 'source', 'hint_count']


class LessonSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'track', 'order', 'title', 'summary', 'content', 'version', 'exercise']


class DraftSerializer(serializers.ModelSerializer):
    code = serializers.CharField(max_length=20000, allow_blank=True, trim_whitespace=False)

    class Meta:
        model = Draft
        fields = ['code', 'revision', 'updated_at']
        read_only_fields = ['updated_at']


class ResultSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    status = serializers.ChoiceField(choices=['passed', 'wrong', 'syntax_error', 'runtime_error', 'timeout', 'stopped'])
    actual = serializers.CharField(max_length=3000, allow_blank=True)
    expected = serializers.CharField(max_length=3000, allow_blank=True)
    error = serializers.CharField(max_length=3000, allow_blank=True, required=False)


class SubmissionSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20000, allow_blank=True, trim_whitespace=False)
    results = ResultSerializer(many=True, allow_empty=False)

    def validate_results(self, value):
        if len(value) > 30:
            raise serializers.ValidationError('Too many test results.')
        return value


class AttemptSerializer(serializers.ModelSerializer):
    lesson = serializers.CharField(source='exercise.lesson_id')
    title = serializers.CharField(source='exercise.title')

    class Meta:
        model = Attempt
        fields = ['id', 'exercise', 'lesson', 'title', 'results', 'passed', 'hints_used', 'solution_viewed', 'created_at']


class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ['lesson', 'completed', 'active_seconds', 'updated_at']


class MentorSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=['explain', 'coach'])
    message = serializers.CharField(max_length=1500)
    code = serializers.CharField(max_length=12000, allow_blank=True, trim_whitespace=False)
    feedback = serializers.CharField(max_length=4000, allow_blank=True, required=False, default='No execution feedback available.')
    revision = serializers.IntegerField(min_value=0)
