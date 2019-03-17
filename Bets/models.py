from django.db import models
from Games.models import Match
from Groups.models import CommunityGroup
from Profiles.models import Wallet, Team, Profile
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save

# Create your models here.

class MatchBettingGroup(models.Model):
    match = models.ForeignKey(Match, related_name='game_mbgs', on_delete=models.PROTECT)
    group = models.ForeignKey(CommunityGroup, related_name='group_mbgs', on_delete=models.PROTECT)

    active = "active"
    deactivated = "deactivated"

    available_statuses = ((active, "Active"),
                           (deactivated, "Deactivated"))

    status = models.CharField(max_length=30,
                              choices=available_statuses,
                              default=active,
                              null=False,
                              blank=False)
    class Meta:
        unique_together = ('match', 'group')

    def __str__(self):
        return str(self.group.name) + "'s betting group for : " + str(self.match.__str__())


class Bet(models.Model):
    match_betting_group = models.ForeignKey(MatchBettingGroup, related_name='mbg_bets', on_delete=models.PROTECT)
    wallet = models.ForeignKey(Wallet, related_name='wallet_bets', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    chosen_team = models.ForeignKey(Team, on_delete=models.PROTECT, blank=True, null=True)
    chosen_user = models.ForeignKey(Wallet, on_delete=models.PROTECT, blank=True, null=True)


    open = "Open"
    lost = "Lost"
    paid = "Paid"

    available_statuses = ((open, "Open"),
                           (lost, "Lost"),
                           (paid, "Paid"))

    status = models.CharField(max_length=30,
                              choices=available_statuses,
                              default=open)

    winnings = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)

    def clean(self):
        super(Bet, self).clean()
        # raise error if none are filled out or both are filled out
        if self.chosen_team is not None and self.chosen_user is not None:
            raise ValidationError('Only chosen_team or chosen_user can be filled out')
        elif self.chosen_team is None and self.chosen_user is None:
            raise ValidationError('Either chosen_team or chosen_user must filled out')

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super().save(*args, **kwargs)


    def __str__(self):
        return str(self.match_betting_group.match) + " | " + str(self.wallet.profile.user) + " | £" + str(self.amount) +" bet for: " + str(self.chosen_team)

# Create mbg upon Match creation
@receiver(post_save, sender=Match)
def create_mbg_on_match_creation(sender, instance, created, **kwargs):
    if created:
        match = instance
        mbg = MatchBettingGroup()
        mbg.match = match
        mbg.group = match.tournament.owning_group
        mbg.save()