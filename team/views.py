from django.shortcuts import render, redirect, get_object_or_404
from .models import TeamMember
from .forms import TeamMemberForm
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_superuser

def our_team(request):
    team_members = TeamMember.objects.filter(is_visible=True)
    return render(request, 'ourteam.html', {'team_members': team_members})

@user_passes_test(is_admin)
def add_team_member(request):
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team member added successfully!')
            return redirect('our_team')
    else:
        form = TeamMemberForm()
    return render(request, 'team_form.html', {'form': form})

@user_passes_test(is_admin)
def edit_team_member(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team member updated successfully!')
            return redirect('our_team')
    else:
        form = TeamMemberForm(instance=member)
    return render(request, 'team_form.html', {'form': form})

@user_passes_test(is_admin)
def delete_team_member(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    member.delete()
    messages.success(request, 'Team member deleted successfully!')
    return redirect('our_team')
