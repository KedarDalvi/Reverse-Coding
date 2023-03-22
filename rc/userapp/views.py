from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from userapp.models import UserProfile, Question, Response
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
import random
from datetime import datetime, timedelta
import re
from django.http import JsonResponse


def username_validation(request):
    if request.method == 'GET':
        try:
            user = User.objects.get(username=request.GET.get('name'))
            user_regex = '^(?=.{6,32}$)(?![_.-])(?!.*[_.-]{2})[a-zA-Z0-9._-]+(?<![_.-])$'
            if re.search(user_regex, request.GET.get('name')) == None:
                found = False
            else:
                found = True
            data = {'found': found}
        except User.DoesNotExist:
            data = {'found': False}
        return JsonResponse(data)


def signup(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('quiz'))
        return render(request, 'userapp/SignUp.html')
    else:
        username = request.POST.get('username')
        user_regex = '^(?=.{6,32}$)(?![_.-])(?!.*[_.-]{2})[a-zA-Z0-9._-]+(?<![_.-])$'
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        phone = request.POST.get('phone')
        f_pass = request.POST.get('f_pass')
        c_pass = request.POST.get('c_pass')
        category = request.POST.get('category')
        if re.search(user_regex, username) == None:
            return render(request, 'userapp/SignUp.html', {'message': 'Enter a valid Username.'})
        if re.search(email_regex, email) == None:
            return render(request, 'userapp/SignUp.html', {'message': 'Enter a valid email id.'})
        if c_pass == f_pass:
            try:
                user = User.objects.get(username=username)
                return render(request, 'userapp/SignUp.html', {'message': 'Username already exists.'})
            except User.DoesNotExist:
                user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                                email=email, password=f_pass)
                user.save()
                profile = UserProfile(user=user, phone=int(phone), category=category)
                profile.save()
                auth.login(request, user)
                profile.login_time = request.user.last_login
                profile.predicted_logout_time = profile.login_time + timedelta(seconds=1680)
                profile.save()
                return HttpResponseRedirect(reverse('quiz'))
        return render(request, 'userapp/SignUp.html', {'message': "Passwords don't match"})


def signin_validation(request):
    if request.method == 'GET':
        try:
            user = User.objects.get(username=request.GET.get('name'))
            data = {'is_same': True}
        except User.DoesNotExist:
            data = {'is_same': False}
        return JsonResponse(data)


def signin(request):
    if request.method == 'GET':
        return render(request, 'userapp/SignIn.html')
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.user_logout == 1:
                    return render(request, 'userapp/SignIn.html',
                              {'message': 'You have already attempted the quiz', 'score': profile.current_score})
                if profile.emergency_time != 0 & (profile.no_question_solved < 15 | profile.decision == 1):
                    auth.login(request, user)
                    profile.login_time = datetime.now()
                    profile.predicted_logout_time = profile.login_time + timedelta(seconds=profile.emergency_time)
                    profile.save()
                    return HttpResponseRedirect(reverse('quiz'))
                if profile.logout_time is not None:
                    if profile.logout_time > profile.predicted_logout_time:
                        return render(request, 'userapp/SignIn.html',
                                  {'message': 'You have already attempted the quiz', 'score': profile.current_score})
                if user.last_login is None:
                    auth.login(request, user)
                    profile.login_time = datetime.now()
                    profile.predicted_logout_time = profile.login_time + timedelta(seconds=1680)
                    profile.save()
                    return HttpResponseRedirect(reverse('quiz'))
            except UserProfile.DoesNotExist:
                return render(request, 'userapp/SignIn.html', {'message': 'Invalid Credentials.'})
        else:
            auth.login(request, user)
            return HttpResponseRedirect(reverse('quiz'))
        return render(request, 'userapp/SignIn.html', {'message': 'Invalid Credentials.'})


def logout(request):
    user1 = UserProfile.objects.get(user=request.user)
    if (user1.predicted_logout_time > datetime.now()) | (user1.extra_time == 1) | (user1.current_score < 12):
        user1.logout_time = datetime.now()
        user1.decision = 0
        user1.no_question_solved += 1
        user1.user_logout = 1
        user1.save(update_fields=["user_logout", 'logout_time', 'decision', "no_question_solved"])
        auth.logout(request)
        return render(request, 'userapp/SignIn.html',
                        {'message': 'You logged out successfully.', 'score': user1.current_score})
    else:
        user1.decision = 0
        user1.no_question_solved += 1
        user1.save(update_fields=['decision', "no_question_solved"])
        return render(request, 'userapp/quiz.html', {'extra_time_window': 1})


def quiz(request):
    try:
        if request.user.is_authenticated:
            username = request.user.username
            user = User.objects.get(username=username)
        if request.method == "GET":
            try:
                user_to_get = UserProfile.objects.get(user=user)
                timer = time(user_to_get.predicted_logout_time)
                rem_time = timedelta(seconds=timer)
                if timer <= 0:
                    return redirect('logout')
                if user_to_get.no_question_solved >= 15:
                    user_to_get.user_logout = 1
                    user_to_get.logout_time = datetime.now()
                    user_to_get.save(update_fields=["user_logout", 'logout_time'])
                    auth.logout(request)
                    return render(request, 'userapp/SignIn.html',
                              {'message': 'You logged out Successfully.', 'score': user_to_get.current_score})
                if len(user_to_get.question_attempted.split(" ")) >= 2:
                    response_to_get = Response.objects.filter(user=user.id).last()
                    if (response_to_get.attempt_1 == -1 & response_to_get.attempt_2 == -1) | (user_to_get.decision == 1):
                        ques = Question.objects.get(id=user_to_get.current_ques_id)
                        current_score_to_show = user_to_get.current_score
                        sr_no = user_to_get.no_question_solved + 1
                        if user_to_get.extra_time == 0:
                            extra_time = 0
                        else:
                            extra_time = 1
                        return render(request, 'userapp/quiz.html',
                                  {'question': ques, 'sr': sr_no, 'score': current_score_to_show,
                                   'remain_time': rem_time, 'abc': user_to_get.decision, 'attempt1': response_to_get.attempt_1,
                                   'progress': ((user_to_get.correct_answers*100)/3), 'extra_time_window': 0, 'extra_time': extra_time})
                different = 0
                while (different == 0):
                    id1 = random.randint(1, 15)
                    if str(id1) not in user_to_get.question_attempted.split(" "):
                        different = 1
                ques = Question.objects.get(id=id1)
                ques_list = user_to_get.question_attempted.split(" ")
                ques_list.append(id1)
                user_to_get.question_attempted = " ".join(map(str, ques_list))
                user_to_get.current_ques_id = id1
                user_to_get.save(update_fields=["question_attempted", "current_ques_id"])
                response = Response(question=ques, user=user)
                response.save()
                current_score_to_show = user_to_get.current_score
                sr_no = user_to_get.no_question_solved + 1
                if user_to_get.extra_time == 0:
                    extra_time = 0
                else:
                    extra_time = 1
                return render(request, 'userapp/quiz.html', {'question': ques, 'sr': sr_no, 'score': current_score_to_show,
                                                         'remain_time': rem_time, 'abc': user_to_get.decision,
                                                             'progress': ((user_to_get.correct_answers*100)/3), 'extra_time_window': 0, 'extra_time': extra_time})
            except Question.DoesNotExist:
                return redirect('quiz')
    except:
        return render(request, 'userapp/SignIn.html', {'message': 'You need to login.'})


def quiz_post(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    user = User.objects.get(username=username)
    if request.method == 'POST':
        user_to_update = UserProfile.objects.get(user=request.user)
        response_to_update = Response.objects.filter(user=user.id).last()
        timer = time(user_to_update.predicted_logout_time)
        rem_time = timedelta(seconds=timer)
        if timer <= 0:
            return redirect('logout')
        if user_to_update.decision == 0:
            attempt_1 = request.POST.get("attempt1")
            response_to_update.attempt_1 = attempt_1
            response_to_update.save(update_fields=["attempt_1"])
            if int(attempt_1) == Question.objects.get(id=user_to_update.current_ques_id).correct_ans:
                user_to_update.no_question_solved = user_to_update.no_question_solved + 1
                user_to_update.current_score = user_to_update.current_score + 4
                user_to_update.correct_answers += 1
                user_to_update.save(update_fields=["no_question_solved", "current_score", "correct_answers"])
                return HttpResponseRedirect(reverse('quiz'))
            else:
                user_to_update.decision = 1
                user_to_update.save(update_fields=['current_score', "decision"])
                if user_to_update.extra_time == 0:
                    extra_time = 0
                else:
                    extra_time = 1
                return render(request, 'userapp/quiz.html',
                              {'question': Question.objects.get(id=user_to_update.current_ques_id),
                               'sr': user_to_update.no_question_solved + 1, 'score': user_to_update.current_score,
                               "remain_time": rem_time, 'abc': user_to_update.decision, 'attempt1': attempt_1,
                               'progress': (user_to_update.correct_answers*100)/3, 'extra_time_window': 0, 'extra_time': extra_time})
        elif user_to_update.decision == 1:
            attempt_2 = request.POST.get("attempt2")
            response_to_update.save(update_fields=["attempt_2"])
            response_to_update.attempt_2 = attempt_2
            user_to_update.decision = 0
            user_to_update.no_question_solved = user_to_update.no_question_solved + 1
            try:
                if int(attempt_2) == Question.objects.get(id=user_to_update.current_ques_id).correct_ans:
                    if user_to_update.hot_or_cold == 1:
                        user_to_update.current_score = user_to_update.current_score + 8
                        user_to_update.hot_or_cold = 0
                        user_to_update.correct_answers = 0
                    else:
                        user_to_update.current_score = user_to_update.current_score + 2
                        user_to_update.correct_answers += 1
                else:
                    if user_to_update.hot_or_cold == 1:
                        user_to_update.current_score = user_to_update.current_score - 8
                        user_to_update.hot_or_cold = 0
                        user_to_update.correct_answers = 0
                    else:
                        user_to_update.current_score = user_to_update.current_score - 1
                user_to_update.save(update_fields=['current_score', 'no_question_solved', "decision", "correct_answers", "hot_or_cold"])
                return HttpResponseRedirect(reverse('quiz'))
            except TypeError:
                return redirect('quiz')


def hot_or_cold(request):
    if request.method == 'POST':
        username = request.user.username
        user = User.objects.get(username=username)
        user_to_get = UserProfile.objects.get(user=user)
        response = Response.objects.filter(user=user.id).last()
        ques = Question.objects.get(id=user_to_get.current_ques_id)
        user_to_get.hot_or_cold = 1
        user_to_get.save(update_fields=["hot_or_cold"])
        if abs(response.attempt_1 - ques.correct_ans) <= ques.correct_ans*0.05:
            verdict = "HOT"
        else:
            verdict = 'COLD'
        current_score_to_show = user_to_get.current_score
        sr_no = user_to_get.no_question_solved + 1
        timer = time(user_to_get.predicted_logout_time)
        rem_time = timedelta(seconds=timer)
        if user_to_get.extra_time == 0:
            extra_time = 0
        else:
            extra_time = 1
        return render(request, 'userapp/quiz.html',
                        {'question': ques, 'sr': sr_no, 'score': current_score_to_show, 'remain_time': rem_time, 'abc': user_to_get.decision,
                        'attempt1': response.attempt_1, 'progress': ((user_to_get.correct_answers * 100) / 3), 'lifeline_message': verdict,
                         'extra_time_window': 0, 'extra_time': extra_time})


def extra_time(request):
    if request.method == "POST":
        username = request.user.username
        user = User.objects.get(username=username)
        user_to_get = UserProfile.objects.get(user=user)
        time = request.POST.get('user_response')
        user_to_get.extra_time = 1
        if time == 'logout':
            user_to_get.save(update_fields=['extra_time'])
            return redirect('logout')
        else:
            user_to_get.predicted_logout_time = (datetime.now() + timedelta(seconds=int(time)))
            if time == "300":
                user_to_get.current_score -= 1
            elif time == "600":
                user_to_get.current_score -= 2
            elif time == "900":
                user_to_get.current_score -= 3
            user_to_get.save(update_fields=['predicted_logout_time', 'current_score', 'extra_time'])
            return redirect('quiz')



def emergencylogin(request):
    if request.method == 'POST':
        super_username = request.POST.get('super_username')
        super_password = request.POST.get('super_password')
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        superuser = auth.authenticate(username=super_username, password=super_password)
        if (user is None) & (superuser is not None):
            return render(request, 'userapp/emergencylogin.html', {'message': 'Participant Credentials are invalid.'})
        if (user is not None) & (superuser is None):
            return render(request, 'userapp/emergencylogin.html',
                          {'message': 'Superuser Credentials are invalid.'})
        if (superuser is None) & (user is None):
            return render(request, 'userapp/emergencylogin.html', {'message': 'Superuser and Participant credentials are invalid.'})
        else:
            time = request.POST.get('time')
            profile = UserProfile.objects.get(user=user)
            profile.user_logout = 0
            profile.emergency_time = int(time)
            profile.save()
            return render(request, 'userapp/emergencylogin.html', {'message': 'Time added successfully.'})
    return render(request, 'userapp/emergencylogin.html')


def time(predicted_logout_time):
    present_time = datetime.now()
    present_time = (present_time.hour * 3600) + (present_time.minute * 60) + (present_time.second)
    end_time = (predicted_logout_time.hour * 3600) + (predicted_logout_time.minute * 60) + (predicted_logout_time.second)
    timer = end_time - present_time
    return timer
