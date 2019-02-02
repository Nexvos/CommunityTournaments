from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from Profiles.models import Wallet, Profile
from .forms import *
from django.shortcuts import redirect
from django.contrib import messages
from Games.models import Tournament, Match, Videogame
from Bets.models import MatchBettingGroup, Bet
from django.http import Http404
from django.utils import timezone
from django.template import loader
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

User = get_user_model()
# Create your views here.
landing_page_url = reverse_lazy('profiles:landingPage')


@login_required(login_url=landing_page_url, redirect_field_name="")
def groupsHome(request):
    user = request.user

    wallets = user.profile.profiles_wallet.all()
    admin_wallets = wallets.filter(Q(admin=True))
    invites = wallets.filter(
        Q(status=Wallet.sent)
    )
    form = AcceptInviteForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            wallet_id = form.cleaned_data['wallet_id']
            accept_invite = form.cleaned_data['accept_invite']
            wallet = get_object_or_404(Wallet, id=wallet_id)

            # Ensure the wallet in question actually belongs to the requesting user
            if wallet.profile == user.profile:

                # Ensure that the wallet is an active invite
                if wallet.status == wallet.sent:

                    # Check that the post request is accepting or declining the invite,
                    # then change the status accordingly
                    if accept_invite:
                        wallet.status = wallet.active

                    else:
                        wallet.status = wallet.declined

                    wallet.save()
                else:
                    form.add_error(None, "This invite is not active.")

            else:
                form.add_error(None, "You are not the owner of this invite.")

    context = {
        "wallets": wallets,
        "admin_wallets": admin_wallets,
        "invites": invites,
        "form": form
    }
    return render(request, 'groups/home.html', context)


@login_required(redirect_field_name="")
def groupSearch(request):
    user = request.user

    user_groups = user.profile.groups.all()

    groups = CommunityGroup.objects.all().exclude(id__in=user_groups).order_by('private')
    wallets = user.profile.profiles_wallet.all().order_by('group__private')
    form = JoinGroupForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            group_id = form.cleaned_data['group_id']

            group = get_object_or_404(CommunityGroup, id=group_id)

            wallet, wallet_created = Wallet.objects.get_or_create(
                profile=user.profile,
                group=group,
                defaults={
                    "status": Wallet.deactivated
                }
            )

            if wallet_created:
                if group.private:
                    # ask for invite
                    wallet.status = wallet.requesting_invite
                    messages.success(request, 'Invite requested')
                else:
                    wallet.status = wallet.active
                    messages.success(request, 'Successfully joined group.')
            else:
                if wallet.status == wallet.active:
                    form.add_error(None, "You are already a member of this group.")
                elif wallet.status == wallet.declined_blocked:
                    form.add_error(None, "This group has blocked you. Please contact the group admin.")
                else:
                    if group.private:
                        # ask for invite
                        if wallet.status == wallet.requesting_invite:
                            form.add_error(None, "You have already requested an invite from this group.")
                        else:
                            wallet.status = wallet.requesting_invite
                            messages.success(request, 'Invite requested')
                    else:
                        wallet.status = wallet.active
                        messages.success(request, 'Successfully joined group.')
            wallet.save()

    context = {
        "model": groups,
        "form": form,
        "wallets": wallets
    }
    return render(request, 'groups/group_search.html', context)


@login_required(redirect_field_name="")
def createGroup(request):
    form = CreateGroupForm()

    if request.method == "POST":
        group_name = request.POST['group_name']
        if 'invite_only' in request.POST:
            invite_only = request.POST['invite_only']
        else:
            invite_only = False
        if 'members_can_invite' in request.POST:
            members_can_invite = request.POST['members_can_invite']
        else:
            members_can_invite = False
        header_background_colour = request.POST['header_background_colour']
        header_text_colour = request.POST['header_text_colour']
        daily_payout = request.POST["daily_payout"]

        form_dict = {
            "group_name": group_name,
            "invite_only": invite_only,
            "members_can_invite": members_can_invite,
            "header_background_colour": header_background_colour,
            "header_text_colour": header_text_colour,
            "daily_payout": daily_payout
        }
        form = CreateGroupForm(form_dict)

        # check whether it's valid:
        if form.is_valid():
            user = get_object_or_404(User, username=request.user)
            group_name = form.cleaned_data['group_name']
            invite_only = form.cleaned_data['invite_only']
            members_can_invite = form.cleaned_data['members_can_invite']
            header_background_colour = form.cleaned_data['header_background_colour']
            header_text_colour = form.cleaned_data['header_text_colour']
            daily_payout = form.cleaned_data['daily_payout']

            new_group = CommunityGroup()
            new_group.name = group_name
            new_group.private = invite_only
            new_group.members_can_inv = members_can_invite
            new_group.header_background_colour = header_background_colour
            new_group.header_text_colour = header_text_colour
            new_group.daily_payout = daily_payout
            new_group.save()

            user_wallet = Wallet()
            user_wallet.profile = user.profile
            user_wallet.group = new_group
            user_wallet.withdrawable_bank = daily_payout
            user_wallet.founder = True
            user_wallet.admin = True
            user_wallet.save()

            return redirect('groups:groupPage', group_id=new_group.id)

    context = {
        "form": form
    }
    return render(request, 'groups/create_group.html', context)


@login_required(redirect_field_name="")
def group_page(request, group_id):
    # Set user to request.user
    user = request.user

    # Fetch the group object
    group = get_object_or_404(CommunityGroup, id=group_id)

    # Attempt to get the ACTIVE wallet for this user for this group
    # If this fails then the user is not a member of the group and should be presented with a 404
    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    latest_game_list = MatchBettingGroup.objects.filter(
        Q(group__id=group_id),
        Q(status=MatchBettingGroup.active)
    )

    tournament_list = group.owning_group_tournaments.all()

    # Nd to create separate qurysets for different tournament statuses and only display active tournaments
    # & tournaments not yet begun
    query = request.GET.get('q')
    current_datetime = timezone.now()
    three_months = timezone.timedelta(days=90)

    if query:
        latest_game_list = latest_game_list.filter(
            ~Q(match__status=Match.finished),
            ~Q(match__status=Match.finished_not_confirmed),
            ~Q(match__status=Match.finished_confirmed),
            ~Q(match__status=Match.finished_paid),
            Q(match__tournament__videogame__name__iexact=query)
        ).order_by('match__start_datetime')[:12]

        tournament_list = tournament_list.filter(videogame__name__iexact=query)

    else:
        latest_game_list = latest_game_list.filter(
            ~Q(match__status=Match.finished),
            ~Q(match__status=Match.finished_not_confirmed),
            ~Q(match__status=Match.finished_confirmed),
            ~Q(match__status=Match.finished_paid)
        ).order_by('match__start_datetime')[:12]
        query = False

    upcoming_tournaments = tournament_list.filter(
            Q(start_datetime__gt=current_datetime),
            Q(start_datetime__lt=current_datetime + three_months)
        ).order_by('start_datetime')

    ongoing_tournaments = tournament_list.filter(
            Q(start_datetime__lt=current_datetime),
            Q(end_datetime__gt=current_datetime)
        ).order_by('start_datetime')[:12]

    ongoing_tournaments1 = ongoing_tournaments[:(-(-len(ongoing_tournaments)//2))]
    ongoing_tournaments2 = ongoing_tournaments[(-(-len(ongoing_tournaments)//2)):]

    completed_tournaments = tournament_list.filter(
            Q(start_datetime__lt=current_datetime),
            Q(end_datetime__lt=current_datetime),
            Q(end_datetime__gt=current_datetime - three_months)
        ).order_by('start_datetime')
    context = {
        'group': group,
        'latest_game_list': latest_game_list,
        'upcoming_tournaments': upcoming_tournaments,
        'ongoing_tournaments1': ongoing_tournaments1,
        'ongoing_tournaments2': ongoing_tournaments2,
        'completed_tournaments': completed_tournaments,
        'query': query,
        'wallet': wallet
    }
    return render(request, 'groups/group_page.html', context)


@login_required(redirect_field_name="")
def lazy_load_games(request, group_id):
    # Set user to request.user
    user = request.user

    # Fetch the group object
    group = get_object_or_404(CommunityGroup, id=group_id)

    # Attempt to get the ACTIVE wallet for this user for this group
    # If this fails then the user is not a member of the group and should be presented with a 404
    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    page = request.POST.get('page')

    group = get_object_or_404(CommunityGroup, id=group_id)

    latest_game_list = MatchBettingGroup.objects.filter(Q(group__id=group_id), Q(status=MatchBettingGroup.active))
    query = request.GET.get('q')
    if query:
        latest_game_list = latest_game_list.filter(
            ~Q(match__status=Match.finished),
            ~Q(match__status=Match.finished_not_confirmed),
            ~Q(match__status=Match.finished_confirmed),
            ~Q(match__status=Match.finished_paid),
            Q(match__tournament__videogame__name__iexact=query)
        ).order_by('match__start_datetime')
    else:
        latest_game_list = latest_game_list.filter(
            ~Q(match__status=Match.finished),
            ~Q(match__status=Match.finished_not_confirmed),
            ~Q(match__status=Match.finished_confirmed),
            ~Q(match__status=Match.finished_paid)
        ).order_by('match__start_datetime')

    # use Django’s pagination
    # https://docs.djangoproject.com/en/dev/topics/pagination/
    results_per_page = 12
    paginator = Paginator(latest_game_list, results_per_page)

    try:
        games = paginator.page(page)
    except PageNotAnInteger:
        games = paginator.page(2)
    except EmptyPage:
        games = paginator.page(paginator.num_pages)

    latest_game_list = games.object_list
    # build a html posts list with the paginated posts
    games_list_html = loader.render_to_string(
        'groups/games_list.html',
        {
            'latest_game_list': latest_game_list,
            'group': group,
        }
    )
    additional_html = "<script>var loop_number=" + str(int(page) * results_per_page - results_per_page) + "</script>"
    # package output data and return it as a JSON object
    output_data = {
        'games_list_html': additional_html + games_list_html,
        'has_next': games.has_next()
    }
    return JsonResponse(output_data)


# TODO: Show videogame name on list view page (probably in the HTML)
@login_required(redirect_field_name="")
def tournament_list_view(request, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')
    tournament_list = group.owning_group_tournaments.all()
    activesection = request.GET.get('activesection')
    query = request.GET.get('q')
    current_datetime = timezone.now()


    if query:
        if query !='None':
            tournament_list = tournament_list.filter(videogame__name__iexact=query)
    else:
        query = 'None'

    upcoming_tournaments = tournament_list.filter(
        Q(start_datetime__gt=current_datetime)
    ).order_by('start_datetime')

    ongoing_tournaments = tournament_list.filter(
        Q(start_datetime__lt=current_datetime),
        Q(end_datetime__gt=current_datetime)
    ).order_by('start_datetime')

    completed_tournaments = tournament_list.filter(
        Q(start_datetime__lt=current_datetime),
        Q(end_datetime__lt=current_datetime)
    ).order_by('start_datetime')

    context = {
        "group": group,
        "upcoming_tournaments": upcoming_tournaments,
        "ongoing_tournaments": ongoing_tournaments,
        "completed_tournaments": completed_tournaments,
        "activesection": activesection,
        'wallet': wallet
    }
    return render(request, "groups/tournament_list_view.html", context)


@login_required(redirect_field_name="")
def invitePage(request, group_id, page):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    # Check that the user is a member of the group AND an admin
    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active, admin=True)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    # TODO: This could be sped up, if the first page only got the first 30 users etc...
    # Get all Users in alphabetical order
    users = User.objects.all()

    # Get the q variable (if there is one)
    query = request.GET.get('q')

    # Filter by username (in the q variable)
    if query:
        if query !='None':
            users = users.filter(username__icontains=query)
    else:
        query = 'None'

    # Get all wallets associated with the group
    group_invites = group.groups_wallet.all()

    # Get all users for the wallets associated with the group
    group_invites_users = []
    for wallet in group_invites:
        group_invites_users.append(wallet.profile.user)

    # Paginate the users
    results_per_page = 30
    paginator = Paginator(users, results_per_page)

    num_pages = paginator.num_pages

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(num_pages)

    # Iterate through each user and if they already have some association to the group then mark the association,
    # if they don't then mark them as open to invite
    model_array = []
    for user in users:
        if user in group_invites_users:
            wallet = group_invites.filter(profile=user.profile)[0]
            if wallet.status == wallet.sent:
                model_array.append({"user": user, "invite_status": "sent"})
            elif wallet.status == wallet.active:
                model_array.append({"user": user, "invite_status": "member"})
            # TODO: is declined blocked from the group or user? Should a group see if a user blocks it?
            elif wallet.status == wallet.declined_blocked:
                model_array.append({"user": user, "invite_status": "blocked"})
            else:
                model_array.append({"user": user, "invite_status": "invite"})
        else:
            model_array.append({"user": user, "invite_status": "invite"})

    # Sort the list into alphabetical order
    model_array = sorted(model_array, key=lambda k: k['user'].username, reverse=True)

    form = InviteMembersForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            invitee_id = form.cleaned_data['profile_id']

            invitee_profile = get_object_or_404(Profile, id=invitee_id)
            invite, invite_created = Wallet.objects.get_or_create(
                profile=invitee_profile,
                group=group,
                defaults={
                    "status": Wallet.sent,
                    "inviter": user.profile
                }
            )
            if invite_created:
                messages.success(request, 'Form submission successful')
            else:
                if invite.status == invite.sent:
                    form.add_error(None, "This user already has a pending invite")
                elif invite.status == invite.active:
                    form.add_error(None, "This user is already a member")
                elif invite.status == invite.declined_blocked:
                    form.add_error(None, "This user is blocking invites from this group")
                else:
                    invite.status = invite.sent
                    invite.inviter = user.profile
                    invite.save()
                    messages.success(request, 'Form submission successful')

    context = {
        "group": group,
        "form": form,
        "model_array": model_array,
        "num_pages": num_pages,
        "num_pages_range": range(num_pages),
        "current_page": page,
        "query": query,
        'wallet': wallet
    }
    return render(request, 'groups/invite.html', context)


@login_required(redirect_field_name="")
def adminPageOptions(request, group_id):
    form = UpdateGroupOptionsForm(request.POST or None)

    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    if request.method == "POST":
        if form.is_valid():
            invite_only = form.cleaned_data['invite_only']
            members_can_invite = form.cleaned_data['members_can_invite']
            header_background_colour = form.cleaned_data['header_background_colour']
            header_text_colour = form.cleaned_data['header_text_colour']
            daily_payout = form.cleaned_data['daily_payout']

            group.private = invite_only
            group.members_can_inv = members_can_invite
            group.header_background_colour = header_background_colour
            group.header_text_colour = header_text_colour
            group.daily_payout = daily_payout
            group.save()

    context = {
        "group": group,
        "form": form,
        'wallet': wallet
    }
    return render(request, 'groups/admin.html', context)

# def adminPageTournaments(request, group_id):
#     # Set user to request.user
#     user = request.user
#
#     group = get_object_or_404(CommunityGroup, id=group_id)
#
#     try:
#         wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
#     except Wallet.DoesNotExist:
#         raise Http404('You are not a member of this group.')
#
#     context = {
#         "group": group,
#         'wallet': wallet
#     }
#     return render(request, 'groups/admin.html', context)


@login_required(redirect_field_name="")
def adminPageAddTournament(request, group_id):
    form = CreateTournamentForm(request.POST or None)

    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)
    videogames = Videogame.objects.all()

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    if request.method == "POST":
        if form.is_valid():
            tournament_name = form.cleaned_data['tournament_name']
            videogame_id = form.cleaned_data['videogame_id']
            start_datetime = form.cleaned_data['tournament_start_date']
            end_datetime = form.cleaned_data['tournament_end_date']

            videogame = get_object_or_404(Videogame, id=videogame_id)

            new_tournament = Tournament()
            new_tournament.name = tournament_name
            new_tournament.videogame = videogame
            new_tournament.start_datetime = start_datetime
            new_tournament.end_datetime = end_datetime
            new_tournament.owning_group = group

            new_tournament.save()
            new_tournament.groups.add(group)
            messages.success(request, 'Form submission successful')


    context = {
        "form": form,
        "group": group,
        "videogames": videogames,
        'wallet': wallet
    }
    return render(request, 'groups/admin.html', context)


@login_required(redirect_field_name="")
def adminPageEditTournament(request, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    context = {
        "group": group,
        'wallet': wallet
    }
    return render(request, 'groups/admin.html', context)


@login_required(redirect_field_name="")
def adminPageAddGames(request, group_id):
    form = CreateGameForm(request.POST or None)

    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')
    if request.method == "POST":
        if form.is_valid():
            tournament_id = form.cleaned_data['tournament_id']
            user_a_id = form.cleaned_data['user_a']
            user_b_id = form.cleaned_data['user_b']
            game_start_datetime = form.cleaned_data['game_start_datetime']
            game_duration = form.cleaned_data['game_duration']
            twitch_url = form.cleaned_data['twitch_url']

            user_a = get_object_or_404(User, id=user_a_id)
            user_b = get_object_or_404(User, id=user_b_id)
            tournament = get_object_or_404(Tournament, id=tournament_id)

            # Sort user_a and user_b alphabetically
            users = [user_a, user_b]
            users = sorted(users, key=lambda x: x.username, reverse=False)
            user_a = users[0]
            user_b = users[1]

            group_profiles = group.groups_profile.all()

            if user_a.profile not in group_profiles or user_a.profile not in group_profiles:
                form.add_error(None, "On of the users selected is not part of this group.")
            elif tournament.owning_group != group:
                form.add_error(None, "The tournament selected is not owned by this group.")
            else:
                new_game = Match()
                new_game.tournament = tournament
                new_game.user_a = user_a.profile
                new_game.user_b = user_b.profile
                new_game.start_datetime = game_start_datetime
                new_game.estimated_duration = timezone.timedelta(minutes=game_duration)
                new_game.twitch_url = twitch_url

                new_game.save()
                messages.success(request, 'Form submission successful')

    context = {
        "group": group,
        "form": form,
        'wallet': wallet
    }
    return render(request, 'groups/admin.html', context)


@login_required(redirect_field_name="")
def adminPageEditGames(request, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    context = {
        "group": group,
        'wallet': wallet
    }
    return render(request, 'groups/admin.html', context)


@login_required(redirect_field_name="")
def adminPageMembers(request, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    context = {
        "group": group,
        'wallet': wallet
    }
    return render(request, 'groups/admin.html', context)


@login_required(redirect_field_name="")
def tournament_view(request, tournament_id, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    tournament = get_object_or_404(Tournament, id=tournament_id)
    tournament_games = MatchBettingGroup.objects.filter(
        Q(group__id=group_id),
        Q(match__tournament__id=tournament_id)
    ).order_by('match__start_datetime')

    # TODO: Test that groups can't access tournaments they're not a part of

    context = {
        "group": group,
        "tournament": tournament,
        "latest_game_list": tournament_games,
        'wallet': wallet
    }
    return render(request, 'groups/tournament_view.html', context)


@login_required(redirect_field_name="")
def completed_game_list_view(request, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    game_list = MatchBettingGroup.objects.filter(
        Q(group__id=group_id)
    ).order_by('match__start_datetime')

    query = request.GET.get('q')
    if query:
        if query != 'None':
            game_list = game_list.filter(
                Q(match__tournament__videogame__name__iexact=query)
            )
    else:
        query = "None"

    completed_games = game_list.filter(
        Q(match__status=Match.finished) |
        Q(match__status=Match.finished_not_confirmed) |
        Q(match__status=Match.finished_confirmed) |
        Q(match__status=Match.finished_paid)
    ).order_by('match__start_datetime')
    context = {
        "group": group,
        "latest_game_list": completed_games,
        'wallet': wallet
    }
    return render(request, "groups/completed_game_list_view.html", context)


@login_required(redirect_field_name="")
def detail(request, betting_group_id, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    userbets = Bet.objects.all().filter(match_betting_group__id=betting_group_id, wallet=wallet)
    game_bgg = get_object_or_404(MatchBettingGroup, pk=betting_group_id)
    qs = game_bgg.mbg_bets.all()

    total_bet = 0
    for bet in qs:
        total_bet += bet.amount
    context = {
        'group': group,
        'game_bgg': game_bgg,
        'total_bet': total_bet,
        'userbets':userbets,
        'wallet': wallet
               }
    return render(request, 'groups/game.html', context)

