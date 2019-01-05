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
from datetime import datetime
from datetime import timedelta
from django.template import loader
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse


User = get_user_model()
# Create your views here.


def groupsHome(request):
    if not request.user.is_authenticated:
        return redirect('profiles:landingPage')
    user = get_object_or_404(User, username=request.user)

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

def groupSearch(request):
    user = get_object_or_404(User, username=request.user)

    user_groups = user.profile.groups.all()

    groups = CommunityGroup.objects.all().exclude(id__in=user_groups).order_by('private')
    wallets = user.profile.profiles_wallet.all().order_by('group__private')
    print("ys")
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
    print(user_groups)
    context = {
        "model": groups,
        "form": form,
        "wallets": wallets
    }
    return render(request, 'groups/group_search.html', context)

def createGroup(request):
    form = CreateGroupForm()

    if request.method == "POST":

        print(request.POST)
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
        # tournaments = ""
        # if 'tournaments' in request.POST:
        #     for t in request.POST.getlist("tournaments"):
        #         tournaments += (t + ",")
        daily_payout = request.POST["daily_payout"]

        form_dict = {
            "group_name": group_name,
            "invite_only": invite_only,
            "members_can_invite": members_can_invite,
            "header_background_colour": header_background_colour,
            "header_text_colour": header_text_colour,
            # "tournaments": tournaments,
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
            # tournaments = form.cleaned_data['tournaments']
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

            # tournament_list = tournaments.split(",")
            # tournament_list_int = []
            # tournament_objs = []
            # print(tournament_list)
            # for t in tournament_list:
            #     try:
            #         t = int(t)
            #         tournament_list_int.append(t)
            #     except:
            #         pass
            # print(tournament_list_int)
            # for t in tournament_list_int:
            #     if isinstance(t, int):
            #         tournament_to_add = get_object_or_404(Tournament, tournament_id=t)
            #         tournament_to_add.groups.add(new_group)

            return redirect('groups:groupPage', group_id=new_group.id)

    context = {
        "form": form
    }
    return render(request, 'groups/create_group.html', context)

def group_page(request, group_id):

    user = get_object_or_404(User, username=request.user)
    group = get_object_or_404(CommunityGroup, id=group_id)
    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    latest_game_list = MatchBettingGroup.objects.filter(Q(group__id=group_id),
                                                       Q(status=MatchBettingGroup.active)
                                                       )
    tournament_list = group.group_tournaments.all()

    # Nd to create separate qurysets for different tournament statuses and only display active tournaments
    # & tournaments not yet begun
    query = request.GET.get('q')
    current_datetime = datetime.now()
    three_months = timedelta(days=90)

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
        query = "None"

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
    print(latest_game_list)
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

def lazy_load_games(request, group_id):
  page = request.POST.get('page')[:12]
  print(page)
  group = get_object_or_404(CommunityGroup, id=group_id)
  latest_game_list = MatchBettingGroup.objects.filter(Q(group__id=group_id), Q(status=MatchBettingGroup.active)) # get just 5 posts
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
  print(paginator.page(1).object_list)
  try:
      games = paginator.page(page)
      latest_game_list = games.object_list
  except PageNotAnInteger:
      games = paginator.page(2)
  except EmptyPage:
      games = paginator.page(paginator.num_pages)
  print("test")
  # build a html posts list with the paginated posts
  games_list_html = loader.render_to_string(
    'groups/games_list.html',
    {
        'latest_game_list': latest_game_list,
        'group': group,
     }
  )
  print("test2")
  additional_html = "<script>var loop_number=" + str(int(page) * 12 - 12) + "</script>"
  # package output data and return it as a JSON object
  output_data = {
    'games_list_html': additional_html + games_list_html,
    'has_next': games.has_next()
  }
  print("test")
  print(output_data)
  return JsonResponse(output_data)

def tournament_list_view(request, group_id):
    user = get_object_or_404(User, username=request.user)
    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')
    tournament_list = group.group_tournaments.all()
    activesection = request.GET.get('activesection')
    query = request.GET.get('q')
    current_datetime = datetime.now()


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

def invitePage(request, group_id):
    user = get_object_or_404(User, username=request.user)
    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    form = InviteMembersForm(request.POST or None)
    model_array = []
    model = User.objects.all()

    group_invites = group.groups_wallet.all()

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
    for user_obj in model:
        invite_count = 0
        for user_invite in user_obj.profile.profiles_wallet.all():
            if user_invite in group_invites:
                invite_count += 1
                if user_invite.status == user_invite.sent:
                    model_array.append({"user": user_obj, "invite_status": "sent"})
                elif user_invite.status == user_invite.active:
                    model_array.append({"user": user_obj, "invite_status": "member"})
                elif user_invite.status == user_invite.declined_blocked:
                    model_array.append({"user": user_obj, "invite_status": "blocked"})
                else:
                    model_array.append({"user": user_obj, "invite_status": "invite"})
        if invite_count == 0:
            model_array.append({"user": user_obj, "invite_status": "invite"})
    SORT_ORDER = {"member": 0, "sent": 1, "invite": 2, "blocked": 3}

    model_array = sorted(model_array, key=lambda k: SORT_ORDER[k['invite_status']])

    context = {
        "group": group,
        "model": model,
        "form": form,
        "model_array": model_array,
        'wallet': wallet
    }
    return render(request, 'groups/invite.html', context)

def adminPageOptions(request, group_id):
    form = UpdateGroupOptionsForm(request.POST or None)
    user = get_object_or_404(User, username=request.user)
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
#     user = get_object_or_404(User, username=request.user)
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

def adminPageAddTournament(request, group_id):
    form = CreateTournamentForm(request.POST or None)
    user = get_object_or_404(User, username=request.user)
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

def adminPageEditTournament(request, group_id):
    user = get_object_or_404(User, username=request.user)
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

def adminPageAddGames(request, group_id):
    form = CreateGameForm(request.POST or None)
    user = get_object_or_404(User, username=request.user)
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
                new_game.estimated_duration = timedelta(minutes=game_duration)
                new_game.twitch_url = twitch_url

                new_game.save()
                messages.success(request, 'Form submission successful')

    context = {
        "group": group,
        "form": form,
        'wallet': wallet
    }
    return render(request, 'groups/admin.html', context)
def adminPageEditGames(request, group_id):
    user = get_object_or_404(User, username=request.user)
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

def adminPageMembers(request, group_id):
    user = get_object_or_404(User, username=request.user)
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

def tournament_view(request, tournament_id, group_id):
    user = get_object_or_404(User, username=request.user)
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

def completed_game_list_view(request, group_id):
    user = get_object_or_404(User, username=request.user)
    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    game_list = MatchBettingGroup.objects.filter(
        Q(group__id=group_id)
    ).order_by('match__start_datetime')

    query = request.GET.get('q')
    print(game_list)
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
    print(completed_games)
    context = {
        "group": group,
        "latest_game_list": completed_games,
        'wallet': wallet
    }
    return render(request, "groups/completed_game_list_view.html", context)

def detail(request, betting_group_id, group_id):
    user = get_object_or_404(User, username=request.user)
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