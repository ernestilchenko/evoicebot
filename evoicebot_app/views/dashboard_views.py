from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.forms import modelform_factory
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Project, Team, UserProfile, TeamMembership


@login_required
def dashboard(request):
    """Widok głównej strony panelu administracyjnego"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    teams = user_profile.get_teams()
    projects = Project.objects.filter(teams__in=teams).distinct()

    context = {
        'teams': teams,
        'projects': projects,
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def team_list(request):
    """Widok listy zespołów"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    teams = user_profile.get_teams()

    context = {
        'teams': teams,
    }

    return render(request, 'dashboard/team_list.html', context)


@login_required
def team_detail(request, uuid):
    """Widok szczegółów zespołu"""
    team = get_object_or_404(Team, uuid=uuid)
    members = team.get_members()

    # Sprawdzamy czy użytkownik jest członkiem tego zespołu
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    try:
        membership = TeamMembership.objects.get(user_profile=user_profile, team=team)
        is_member = True
        user_role = membership.role
    except TeamMembership.DoesNotExist:
        is_member = False
        user_role = None

    if not is_member and user_profile.role != 'admin':
        messages.error(request, 'Nie masz dostępu do tej grupy.')
        return redirect('dashboard')

    context = {
        'team': team,
        'members': members,
        'user_role': user_role,
        'is_admin': user_role == 'admin' or user_profile.role == 'admin',
    }

    return render(request, 'dashboard/team_detail.html', context)


@login_required
def project_list(request):
    """Widok listy projektów"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    teams = user_profile.get_teams()
    projects = Project.objects.filter(teams__in=teams).distinct()

    context = {
        'projects': projects,
    }

    return render(request, 'dashboard/project_list.html', context)


@login_required
def project_detail(request, uuid):
    """Widok szczegółów projektu"""
    project = get_object_or_404(Project, uuid=uuid)
    teams = project.teams.all()

    # Sprawdzamy czy użytkownik ma dostęp do tego projektu
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_teams = user_profile.get_teams()
    has_access = any(team in user_teams for team in teams) or user_profile.role == 'admin'

    if not has_access:
        messages.error(request, 'Nie masz dostępu do tego projektu.')
        return redirect('dashboard')

    # Sprawdzamy role użytkownika w każdym zespole projektu
    user_roles = {}
    is_project_admin = False

    for team in teams:
        try:
            membership = TeamMembership.objects.get(user_profile=user_profile, team=team)
            user_roles[team.id] = membership.role
            if membership.role == 'admin':
                is_project_admin = True
        except TeamMembership.DoesNotExist:
            user_roles[team.id] = None

    # Użytkownik jest administratorem projektu, jeśli jest adminem co najmniej jednego zespołu
    # lub ma globalną rolę admina
    is_project_admin = is_project_admin or user_profile.role == 'admin'

    context = {
        'project': project,
        'teams': teams,
        'user_roles': user_roles,
        'is_project_admin': is_project_admin,
    }

    return render(request, 'dashboard/project_detail.html', context)


@login_required
def create_team(request):
    """Widok tworzenia nowego zespołu"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Formularz dla zespołu
    TeamForm = modelform_factory(Team, fields=['name', 'description', 'logo', 'project'])

    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            # Tworzymy nowy zespół
            team = form.save()

            # Dodajemy użytkownika jako administratora zespołu
            TeamMembership.objects.create(
                user_profile=user_profile,
                team=team,
                role='admin'
            )

            messages.success(request, 'Zespół został pomyślnie utworzony. Jesteś jego administratorem.')
            return redirect('team_detail', uuid=team.uuid)
    else:
        # Jeśli jest przekazany parametr project, predefiniujemy projekt
        project_id = request.GET.get('project')
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                form = TeamForm(initial={'project': project})
            except Project.DoesNotExist:
                form = TeamForm()
        else:
            form = TeamForm()

    context = {
        'form': form,
    }

    return render(request, 'dashboard/team_form.html', context)


@login_required
def create_project(request):
    """Widok tworzenia nowego projektu"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Formularz dla projektu
    ProjectForm = modelform_factory(Project, fields=['name', 'description'])

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            # Tworzymy nowy projekt
            project = form.save()

            # Tworzymy główny zespół dla projektu
            initial_team = Team.objects.create(
                name=f"Główny zespół - {project.name}",
                description=f"Domyślny zespół zarządzający projektem {project.name}",
                project=project
            )

            # Dodajemy użytkownika jako administratora zespołu
            TeamMembership.objects.create(
                user_profile=user_profile,
                team=initial_team,
                role='admin'
            )

            messages.success(request,
                             f'Projekt "{project.name}" został pomyślnie utworzony. Jesteś administratorem głównego zespołu.')

            # Przekierowanie do szczegółów projektu - upewnij się, że ten URL działa poprawnie
            return redirect('project_detail', id=project.id)
        else:
            # Wyświetl komunikat o błędach formularza
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Błąd w polu {field}: {error}')
    else:
        form = ProjectForm()

    context = {
        'form': form,
    }

    return render(request, 'dashboard/project_form.html', context)


@login_required
def manage_team_members(request, uuid):
    """Widok zarządzania członkami zespołu"""
    team = get_object_or_404(Team, uuid=uuid)
    user_profile = get_object_or_404(UserProfile, user=request.user)

    # Sprawdź, czy użytkownik jest administratorem zespołu
    try:
        membership = TeamMembership.objects.get(user_profile=user_profile, team=team)
        is_admin = membership.role == 'admin' or user_profile.role == 'admin'
    except TeamMembership.DoesNotExist:
        is_admin = user_profile.role == 'admin'

    if not is_admin:
        messages.error(request, 'Nie masz uprawnień do zarządzania członkami tego zespołu.')
        return redirect('team_detail', uuid=team.uuid)

    # Obsługa formularza dodawania/usuwania członków i zmiany ról
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_member':
            username = request.POST.get('username')
            role = request.POST.get('role', 'member')

            try:
                user = User.objects.get(username=username)
                member_profile, created = UserProfile.objects.get_or_create(user=user)

                # Sprawdź, czy użytkownik już jest członkiem zespołu
                membership, created = TeamMembership.objects.get_or_create(
                    user_profile=member_profile,
                    team=team,
                    defaults={'role': role}
                )

                if not created:
                    messages.info(request, f'Użytkownik {username} jest już członkiem zespołu.')
                else:
                    messages.success(request,
                                     f'Użytkownik {username} został dodany do zespołu z rolą {dict(TeamMembership.ROLE_CHOICES)[role]}.')

            except User.DoesNotExist:
                messages.error(request, f'Użytkownik o nazwie {username} nie istnieje.')

        elif action == 'change_role':
            member_id = request.POST.get('member_id')
            new_role = request.POST.get('new_role')

            try:
                membership = TeamMembership.objects.get(id=member_id, team=team)
                old_role = membership.get_role_display()
                membership.role = new_role
                membership.save()
                messages.success(request,
                                 f'Rola użytkownika {membership.user_profile.user.username} została zmieniona z {old_role} na {dict(TeamMembership.ROLE_CHOICES)[new_role]}.')
            except TeamMembership.DoesNotExist:
                messages.error(request, 'Członek zespołu nie został znaleziony.')

        elif action == 'remove_member':
            member_id = request.POST.get('member_id')

            try:
                membership = TeamMembership.objects.get(id=member_id, team=team)
                username = membership.user_profile.user.username

                # Nie pozwól na usunięcie ostatniego administratora
                if membership.role == 'admin' and TeamMembership.objects.filter(team=team, role='admin').count() <= 1:
                    messages.error(request, 'Nie można usunąć ostatniego administratora zespołu.')
                else:
                    membership.delete()
                    messages.success(request, f'Użytkownik {username} został usunięty z zespołu.')
            except TeamMembership.DoesNotExist:
                messages.error(request, 'Członek zespołu nie został znaleziony.')

    # Pobierz wszystkich członków zespołu z ich rolami
    memberships = TeamMembership.objects.filter(team=team).select_related('user_profile__user')

    context = {
        'team': team,
        'memberships': memberships,
        'role_choices': TeamMembership.ROLE_CHOICES,
    }

    return render(request, 'dashboard/manage_team_members.html', context)


@login_required
def edit_project(request, uuid):
    """Widok edycji projektu"""
    project = get_object_or_404(Project, uuid=uuid)

    # Sprawdzamy czy użytkownik ma dostęp do tego projektu
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    teams = project.teams.all()
    user_teams = user_profile.get_teams()
    has_access = any(team in user_teams for team in teams) or user_profile.role == 'admin'

    if not has_access:
        messages.error(request, 'Nie masz dostępu do tego projektu.')
        return redirect('dashboard')

    # Sprawdzamy czy użytkownik jest adminem projektu
    is_project_admin = False
    for team in teams:
        try:
            membership = TeamMembership.objects.get(user_profile=user_profile, team=team)
            if membership.role == 'admin':
                is_project_admin = True
                break
        except TeamMembership.DoesNotExist:
            pass

    is_project_admin = is_project_admin or user_profile.role == 'admin'

    if not is_project_admin:
        messages.error(request, 'Nie masz uprawnień do edycji tego projektu.')
        return redirect('project_detail', id=project.id)

    # Formularz dla projektu
    ProjectForm = modelform_factory(Project, fields=['name', 'description'])

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Projekt "{project.name}" został zaktualizowany.')
            return redirect('project_detail', id=project.id)
    else:
        form = ProjectForm(instance=project)

    context = {
        'form': form,
        'project': project
    }

    return render(request, 'dashboard/project_form.html', context)


@login_required
def delete_project(request, uuid):
    """Widok usuwania projektu"""
    project = get_object_or_404(Project, uuid)

    # Sprawdzamy czy użytkownik ma dostęp do tego projektu
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    teams = project.teams.all()
    user_teams = user_profile.get_teams()
    has_access = any(team in user_teams for team in teams) or user_profile.role == 'admin'

    if not has_access:
        messages.error(request, 'Nie masz dostępu do tego projektu.')
        return redirect('dashboard')

    # Sprawdzamy czy użytkownik jest adminem projektu
    is_project_admin = False
    for team in teams:
        try:
            membership = TeamMembership.objects.get(user_profile=user_profile, team=team)
            if membership.role == 'admin':
                is_project_admin = True
                break
        except TeamMembership.DoesNotExist:
            pass

    is_project_admin = is_project_admin or user_profile.role == 'admin'

    if not is_project_admin:
        messages.error(request, 'Nie masz uprawnień do usunięcia tego projektu.')
        return redirect('project_detail', id=project.id)

    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Projekt "{project_name}" został usunięty.')
        return redirect('dashboard')

    context = {
        'project': project
    }

    return render(request, 'dashboard/project_delete_confirm.html', context)


@login_required
def edit_team(request, uuid):
    """Widok edycji zespołu"""
    team = get_object_or_404(Team, uuid=uuid)

    # Sprawdzamy czy użytkownik jest administratorem tego zespołu
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    try:
        membership = TeamMembership.objects.get(user_profile=user_profile, team=team)
        is_admin = membership.role == 'admin' or user_profile.role == 'admin'
    except TeamMembership.DoesNotExist:
        is_admin = user_profile.role == 'admin'

    if not is_admin:
        messages.error(request, 'Nie masz uprawnień do edycji tego zespołu.')
        return redirect('team_detail', uuid=team.uuid)

    # Formularz dla zespołu
    TeamForm = modelform_factory(Team, fields=['name', 'description', 'logo', 'project'])

    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f'Zespół "{team.name}" został zaktualizowany.')
            return redirect('team_detail', uuid=team.uuid)
    else:
        form = TeamForm(instance=team)

    context = {
        'form': form,
        'team': team
    }

    return render(request, 'dashboard/team_form.html', context)
