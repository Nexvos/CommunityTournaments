from django import forms
from decimal import Decimal
from .models import CommunityGroup

class CreateGroupForm(forms.Form):
    group_name = forms.CharField(max_length=120)
    invite_only = forms.BooleanField(required=False)
    members_can_invite = forms.BooleanField(required=False)
    header_background_colour = forms.CharField(max_length=7)
    header_text_colour = forms.CharField(max_length=7)
    tournaments = forms.CharField(required=False)
    daily_payout = forms.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal('0.01'), required=False)

    def clean(self):
        cd = self.cleaned_data
        name = cd.get('group_name').lower()
        if "public" in name:
            self.add_error('group_name', "You cannot have the word 'public' in your community's name !")
        for t in CommunityGroup.objects.all():
            if name == t.name.lower():
                self.add_error('group_name', "The community name must be unique !")
        return cd

class UpdateGroupOptionsForm(forms.Form):
    invite_only = forms.BooleanField(required=False)
    members_can_invite = forms.BooleanField(required=False)
    header_background_colour = forms.CharField(max_length=7)
    header_text_colour = forms.CharField(max_length=7)
    daily_payout = forms.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal('0.01'), required=False)

class InviteMembersForm(forms.Form):
    profile_id = forms.IntegerField(required=True)

class MembersAdminCommandForm(forms.Form):
    wallet_id = forms.IntegerField(required=True)
    admin_command = forms.CharField(required=True, max_length=16)


class AcceptInviteForm(forms.Form):
    accept_invite = forms.BooleanField(required=False)
    wallet_id = forms.IntegerField(required=True)

class JoinGroupForm(forms.Form):
    group_id = forms.IntegerField(required=True)

class CreateTournamentForm(forms.Form):
    tournament_name = forms.CharField(max_length=120)
    videogame_id = forms.IntegerField()
    tournament_start_date = forms.DateTimeField(input_formats=['%H:%M - %d/%m/%Y'])
    tournament_end_date = forms.DateTimeField(input_formats=['%H:%M - %d/%m/%Y'])
    twitch_url = forms.URLField()
    def clean(self):
        cd = self.cleaned_data
        start_date = cd.get('tournament_start_date')
        end_date = cd.get('tournament_end_date')

        if end_date < start_date:
            self.add_error('tournament_end_date', "Your tournament end date is earlier than your tournament start date")

        return cd


class UpdateTournamentDateForm(forms.Form):
    tournament_start_datetime = forms.DateTimeField(input_formats=['%H:%M - %d/%m/%Y'])
    tournament_end_datetime = forms.DateTimeField(input_formats=['%H:%M - %d/%m/%Y'])
    def clean(self):
        cd = self.cleaned_data
        start_date = cd.get('tournament_start_datetime')
        end_date = cd.get('tournament_end_datetime')

        if end_date < start_date:
            self.add_error('tournament_end_datetime', "Your tournament end date is earlier than your tournament start date")

        return cd

class UpdateStatusForm(forms.Form):
    status = forms.CharField(max_length=40)


class UpdateUrlForm(forms.Form):
    url = forms.URLField()

class UpdateVideogameForm(forms.Form):
    videogame_id = forms.IntegerField()

class UpdateWinnerForm(forms.Form):
    winner = forms.IntegerField()

class CreateGameForm(forms.Form):
    tournament_id = forms.IntegerField()
    user_a = forms.IntegerField()
    user_b = forms.IntegerField()
    game_start_datetime = forms.DateTimeField(input_formats=['%H:%M - %d/%m/%Y'])
    game_duration = forms.IntegerField()
    twitch_url = forms.URLField()

    def clean(self):
        cd = self.cleaned_data
        user_a = cd.get('user_a')
        user_b = cd.get('user_b')

        if user_a == user_b:
            self.add_error('user_b', "A user cannot play against themselves.")

        return cd


class UpdateMatchDateForm(forms.Form):
    match_start_datetime = forms.DateTimeField(input_formats=['%H:%M - %d/%m/%Y'])
    match_duration = forms.IntegerField()


class BetForm(forms.Form):
    chosen_team = forms.CharField(max_length=200)
    amount = forms.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal('0.01'))


class ChatForm(forms.Form):
    chat_message = forms.CharField(max_length=1024)
