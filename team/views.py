import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import TeamMember
from .forms import TeamMemberForm

logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_superuser


def our_team(request):
    # Public view: only visible members
    team_members = TeamMember.objects.filter(is_visible=True)
    return render(request, 'ourteam.html', {'team_members': team_members})


@user_passes_test(is_admin)
def add_team_member(request):
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save()
            logger.info(f"Admin {request.user.username} added team member: {member.name}")
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
            logger.info(f"Admin {request.user.username} edited team member: {member.name}")
            messages.success(request, 'Team member updated successfully!')
            return redirect('our_team')
    else:
        form = TeamMemberForm(instance=member)
    return render(request, 'team_form.html', {'form': form})


@user_passes_test(is_admin)
def delete_team_member(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    member_name = member.name
    member.delete()
    logger.info(f"Admin {request.user.username} deleted team member: {member_name}")
    messages.success(request, 'Team member deleted successfully!')
    return redirect('our_team')