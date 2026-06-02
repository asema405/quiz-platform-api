from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Test, Question, AnswerOption, TestAttempt, UserAnswer


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class TestListSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Test
        fields = ('id', 'title', 'questions_count', 'time_limit', 'category')


class TestDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = '__all__'


# Сериализатор для прохождения (скрывает Is_correct)
class AnonymousOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ('id', 'text')


class TakeQuestionSerializer(serializers.ModelSerializer):
    options = AnonymousOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'text', 'question_type', 'options')


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ('question', 'selected_options')

    def validate(self, attrs):
        attempt_id = self.context['view'].kwargs.get('pk')
        attempt = TestAttempt.objects.get(pk=attempt_id)

        if attempt.is_expired():
            attempt.status = 'completed'
            attempt.finished_at = attempt.started_at + timezone.timedelta(minutes=attempt.test.time_limit)
            attempt.save()
            raise serializers.ValidationError("Время прохождения теста истекло.")

        if attempt.status == 'completed':
            raise serializers.ValidationError("Этот тест уже завершен.")

        if attrs['question'].test != attempt.test:
            raise serializers.ValidationError("Вопрос не принадлежит данному тесту.")

        return attrs


class MyResultsSerializer(serializers.ModelSerializer):
    test = serializers.CharField(source='test.title')

    class Meta:
        model = TestAttempt
        fields = ('test', 'score', 'is_passed', 'finished_at')