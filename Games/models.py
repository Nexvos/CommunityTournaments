from django.db import models
from django.core.exceptions import ValidationError
from Profiles.models import Profile, Team, Wallet
from Groups.models import CommunityGroup
from datetime import timedelta
from django.templatetags.static import static

# Create your models here.


class Videogame(models.Model):
    name = models.CharField(unique=True, max_length=30, default="LoL")
    api_videogame_id = models.IntegerField(unique=True, null=True, blank=True)
    picture_id = models.IntegerField(default=1, null=False, blank=False)
    colour = models.CharField(max_length=7, null=False, blank=False, default="D3D3D3")
    alt_colour = models.CharField(max_length=7, null=False, blank=False, default="D3D3D3")

    @property
    def picture_url(self):
        image = "img/game_logos/logo_" + str(self.picture_id) + ".png"
        return static(image)

    def __str__(self):
        return self.name


class Tournament(models.Model):
    name = models.CharField(max_length=120, null=False, blank=False)
    api_tournament_id = models.IntegerField(unique=True, null=True, blank=True)
    api_modified_at = models.DateTimeField('api_modified_at',null=True, blank=True)

    owning_group = models.ForeignKey(
        CommunityGroup,
        related_name='owning_group_tournaments',
        default=1,
        blank=False,
        null=False,
        on_delete=models.PROTECT
    )

    videogame = models.ForeignKey(
        Videogame,
        related_name='videogame_tournaments',
        blank=True,
        null=True,
        on_delete=models.PROTECT
    )
    start_datetime = models.DateTimeField('Tournament start date')
    end_datetime = models.DateTimeField('Tournament end date', blank=True, null=True)

    twitch_url = models.URLField(max_length=200, unique=False, blank=True, null=True)

    not_begun = "Not begun"
    ongoing = "Ongoing"
    finished = "Finished"


    available_statuses = ((not_begun, "Not begun"),
                           (ongoing, "Ongoing"),
                           (finished, "Finished"))

    status = models.CharField(max_length=30,
                              choices=available_statuses,
                              default=not_begun)

    def __str__(self):
        return self.name


class Match(models.Model):
    api_match_id = models.IntegerField(unique=True,blank=True,null=True)
    api_modified_at = models.DateTimeField('api_modified_at',null=True, blank=True)

    team_a = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='%(class)s_team_a', blank=True,null=True)
    team_b = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='%(class)s_team_b', blank=True,null=True)

    user_a = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='%(class)s_user_a', blank=True,null=True)
    user_b = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='%(class)s_user_b', blank=True,null=True)

    tournament = models.ForeignKey(Tournament, related_name='tournament_matches', blank=False, null=False, on_delete=models.PROTECT)
    start_datetime = models.DateTimeField('Game start datetime')
    estimated_duration = models.DurationField(default=timedelta(minutes=2))

    twitch_url = models.URLField(max_length=200, unique=False, blank=True, null=True)

    a_winner = "A is the winner"
    b_winner = "B is the winner"
    not_decided = "Not Decided"
    teams = ((not_decided, "Not Decided"),
             (a_winner, "A is the winner"),
             (b_winner, "B is the winner"))

    winner = models.CharField(
        max_length=60,
        choices=teams,
        default= not_decided,
        unique=False,
        blank=False,
        null=False
    )

    not_started = "not_started"
    starting = "Starting"
    running = "running"
    finished = "finished"
    finished_not_confirmed = "Finished - Not yet confirmed"
    finished_confirmed = "Finished - Confirmed"
    finished_paid = "Finished - All bets paid"

    available_statuses = ((not_started, "Not started"),
                           (starting, "Starting"),
                           (running, "Running"),
                           (finished, "Finished"),
                           (finished_not_confirmed, "Finished - Not yet confirmed"),
                           (finished_confirmed, "Finished - Confirmed"),
                           (finished_paid, "Finished - All bets paid"))

    status = models.CharField(max_length=30,
                              choices=available_statuses,
                              default=not_started)

    # Goal: Make it so that teamaa =/ team_b...
    # Useful thread = https://stackoverflow.com/questions/35096607/how-to-enforce-different-values-in-multiple-foreignkey-fields-for-django

    def clean(self):  # Used to raise validation errors if a mix of users and teams are assigned to a game
        super(Match, self).clean()
        # raise error if none are filled out or both are filled out + if a team is against a user
        if self.user_a is not None and self.team_a is not None:
            raise ValidationError('Only user_a or team_a can be filled out')
        elif self.user_b is not None and self.team_b is not None:
            raise ValidationError('Only user_b or team_b can filled out')
        elif self.user_a is None and self.team_a is None:
            raise ValidationError('Either user_a or team_a must filled out')
        elif self.user_b is None and self.team_b is None:
            raise ValidationError('Either user_b or team_b must filled out')
        elif self.user_a is not None and self.team_b is not None:
            raise ValidationError('A user cannot play versus a team')
        elif self.user_b is not None and self.team_a is not None:
            raise ValidationError('A user cannot play versus a team')

    def save(self, *args, **kwargs):  # Exceptions raised if values for teams or values for users ar the same
        try:
            if self.team_a == self.team_b:
                raise Exception('attempted to create a match object where team_a == team_b')
        except:
            pass
        try:
            if self.user_a == self.user_b:
                raise Exception('attempted to create a match object where user_a == user_b')
        except:
            pass
        super(Match, self).save(*args, **kwargs)

    def __str__(self):
        if self.team_a is not None:
            return str(self.team_a) + " vs " + str(self.team_b) + " - " + str(self.start_datetime)
        else:
            return str(self.user_a) + " vs " + str(self.user_b) + " - " + str(self.start_datetime)
