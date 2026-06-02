import logging
from django.utils import timezone
from django.db.models import Avg
from rest_framework import generics, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Category, Test, Question, AnswerOption, TestAttempt, UserAnswer
from .serializers import (
    RegisterSerializer, CategorySerializer, TestListSerializer,
    TestDetailSerializer, TakeQuestionSerializer, UserAnswerSerializer, MyResultsSerializer
)
from .permissions import IsAdminUserOrReadOnly

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]


class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.filter(is_active=True)
    permission_classes = [IsAdminUserOrReadOnly]
    filterset_fields = ['category']
    search_fields = ['title', 'description']

    def get_serializer_class(self):
        if self.action == 'list':
            return TestListSerializer
        return TestDetailSerializer

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def start(self, request, pk=None):
        test = self.get_object()
        attempt = TestAttempt.objects.create(user=request.user, test=test)
        logger.info(f"User {request.user.username} started test {test.title} (Attempt ID: {attempt.id})")
        return Response({
            "attempt_id": attempt.id,
            "started_at": attempt.started_at
        }, status=status.HTTP_201_CREATED)


class AttemptViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_attempt(self, pk):
        try:
            attempt = TestAttempt.objects.get(pk=pk)
            if attempt.user != self.request.user:
                raise PermissionDenied("Бул сиздин тест өтүү аракетиңиз эмес.")
            return attempt
        except TestAttempt.DoesNotExist:
            raise ValidationError({"detail": "Тест өтүү аракети табылган жок."})

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        attempt = self.get_attempt(pk)
        if attempt.is_expired():
            return Response({"error": "Убакыт өтүп кетти!"}, status=status.HTTP_400_BAD_REQUEST)

        questions = Question.objects.filter(test=attempt.test)
        serializer = TakeQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        attempt = self.get_attempt(pk)
        serializer = UserAnswerSerializer(data=request.data, context={'view': self})
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data['question']
        selected_options = request.data.get('selected_options', [])

        correct_options = list(
            AnswerOption.objects.filter(question=question, is_correct=True).values_list('id', flat=True)
        )
        is_correct = sorted(selected_options) == sorted(correct_options)

        user_answer, created = UserAnswer.objects.get_or_create(attempt=attempt, question=question)
        user_answer.selected_options.set(selected_options)
        user_answer.is_correct = is_correct
        user_answer.save()

        logger.info(f"User {request.user.username} answered question {question.id} in attempt {attempt.id}")
        return Response({"success": True})

    @action(detail=True, methods=['post'])
    def finish(self, request, pk=None):
        attempt = self.get_attempt(pk)
        if attempt.status == 'completed':
            return Response({"error": "Бул тест буга чейин эле аяктаган."}, status=status.HTTP_400_BAD_REQUEST)

        if attempt.is_expired():
            attempt.finished_at = attempt.started_at + timezone.timedelta(minutes=attempt.test.time_limit)
        else:
            attempt.finished_at = timezone.now()

        total_questions = attempt.test.questions.count()
        user_correct_answers = UserAnswer.objects.filter(attempt=attempt, is_correct=True).count()

        score_percent = int((user_correct_answers / total_questions) * 100) if total_questions > 0 else 0

        attempt.score = score_percent
        attempt.is_passed = score_percent >= attempt.test.passing_score
        attempt.status = 'completed'
        attempt.save()

        logger.info(f"User {request.user.username} finished test {attempt.test.title}. Score: {score_percent}%")

        return Response({
            "score": attempt.score,
            "is_passed": attempt.is_passed,
            "correct_answers": user_correct_answers,
            "total_questions": total_questions
        })

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        attempt = self.get_attempt(pk)
        if attempt.status != 'completed':
            return Response({"error": "Адегенде тестти аяктаңыз."}, status=status.HTTP_400_BAD_REQUEST)

        user_answers = UserAnswer.objects.filter(attempt=attempt)
        questions_data = [{
            "question": ans.question.text,
            "is_correct": ans.is_correct
        } for ans in user_answers]

        return Response({
            "score": attempt.score,
            "is_passed": attempt.is_passed,
            "questions": questions_data
        })


class MyResultsView(generics.ListAPIView):
    serializer_class = MyResultsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TestAttempt.objects.filter(user=self.request.user, status='completed')


# Admin API
class AdminTestStatisticsView(generics.RetrieveAPIView):
    queryset = Test.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def retrieve(self, request, *args, **kwargs):
        test = self.get_object()
        attempts = TestAttempt.objects.filter(test=test, status='completed')

        total_attempts = attempts.count()
        average_score = attempts.aggregate(Avg('score'))['score__avg'] or 0
        passed = attempts.filter(is_passed=True).count()
        failed = attempts.filter(is_passed=False).count()

        return Response({
            "attempts": total_attempts,
            "average_score": round(average_score, 2),
            "passed": passed,
            "failed": failed
        })