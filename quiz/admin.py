from django.contrib import admin
from .models import Category, Test, Question, AnswerOption, TestAttempt, UserAnswer

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # 'title' ордуна сенин моделиңдеги 'name' талаасын жаздык
    list_display = ('id', 'name')
    search_fields = ('name',)

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'time_limit', 'passing_score', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'test')
    list_filter = ('test',)
    search_fields = ('text',)
    inlines = [AnswerOptionInline]

@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__test')
    search_fields = ('text',)

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'test', 'status', 'score', 'is_passed', 'started_at')
    list_filter = ('status', 'is_passed', 'test')
    search_fields = ('user__username', 'test__title')

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'is_correct')
    list_filter = ('is_correct',)