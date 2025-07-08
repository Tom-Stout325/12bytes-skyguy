from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import *
from .forms import *



@login_required
def home(request):
    context = {'current_page': 'home'} 
    return render(request, 'app/home.html', context)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    context = {'form': form, 'current_page': 'register'} 
    return render(request, 'registration/register.html', context)


@login_required
def profile(request):
    profile = get_object_or_404(PilotProfile, user=request.user)
    year_filter = request.GET.get('year')

    trainings = profile.trainings.all()
    if year_filter:
        trainings = trainings.filter(date_completed__year=year_filter)

    training_years = profile.trainings.dates('date_completed', 'year', order='DESC')

    context = {
        'profile': profile,
        'trainings': trainings,
        'years': [y.year for y in training_years],
        'current_page': 'profile' 
    }
    return render(request, 'app/profile.html', context)


@login_required
def edit_profile(request):
    profile = get_object_or_404(PilotProfile, user=request.user)
    if request.method == 'POST':
        form = PilotProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = PilotProfileForm(instance=profile)
    context = {'form': form, 'current_page': 'profile'}  
    return render(request, 'app/edit_profile.html', context)


@login_required
def delete_pilot_profile(request):
    profile = get_object_or_404(PilotProfile, user=request.user)
    if request.method == 'POST':
        user = profile.user
        profile.delete()
        user.delete()
        messages.success(request, "Your profile and account have been deleted.")
        return redirect('login')
    context = {'profile': profile, 'current_page': 'profile'}  
    return render(request, 'app/pilot_profile_delete.html', context)


@login_required
def training_create(request):
    profile = get_object_or_404(PilotProfile, user=request.user)
    if request.method == 'POST':
        form = TrainingForm(request.POST, request.FILES)
        if form.is_valid():
            training = form.save(commit=False)
            training.pilot = profile
            training.save()
            return redirect('profile')
    else:
        form = TrainingForm()
    context = {'form': form, 'current_page': 'profile'}  
    return render(request, 'app/training_form.html', context)


@login_required
def training_edit(request, pk):
    training = get_object_or_404(Training, pk=pk, pilot__user=request.user)
    form = TrainingForm(request.POST or None, request.FILES or None, instance=training)
    if form.is_valid():
        form.save()
        return redirect('profile')
    context = {'form': form, 'current_page': 'profile'}  
    return render(request, 'app/training_form.html', context)


@login_required
def training_delete(request, pk):
    training = get_object_or_404(Training, pk=pk, pilot__user=request.user)
    if request.method == 'POST':
        training.delete()
        return redirect('profile')
    context = {'training': training, 'current_page': 'profile'}  
    return render(request, 'app/training_confirm_delete.html', context)