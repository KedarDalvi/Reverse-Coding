from django.db import models
from django.contrib.auth.models import User, auth


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, max_length=100)
    phone = models.IntegerField()
    no_question_solved = models.IntegerField(default=0, editable=True)
    current_score = models.IntegerField(default=0, editable=True)
    question_attempted = models.TextField()
    current_ques_id = models.IntegerField(default=0)
    user_logout = models.IntegerField(default=0)
    decision = models.IntegerField(default=0)
    login_time = models.DateTimeField(max_length=100, null=True)
    logout_time = models.DateTimeField(max_length=100, null=True)
    predicted_logout_time = models.DateTimeField(max_length=100, null=True)
    category = models.CharField(max_length=10, default=0)
    emergency_time = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    hot_or_cold = models.IntegerField(default=0)
    extra_time = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


class Question(models.Model):
    question = models.TextField()
    level = models.CharField(max_length=100)
    correct_ans = models.IntegerField()

    def __str__(self):
        return self.question


class Response(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempt_1 = models.IntegerField(default=-1)
    attempt_2 = models.IntegerField(default=-1)

    def __str__(self):
        return self.user.username