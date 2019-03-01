from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from Groups.models import CommunityGroup
import random

# Create your models here.
User = settings.AUTH_USER_MODEL


def upload_location(instance, filename):

    location = instance.user.username
    return "%s/%s"%(location, filename)


def hex_to_rgb(colour):
    rgb_str = str((tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4))))
    rgb_str = rgb_str.rstrip(")")
    rgb_str = rgb_str.lstrip("(")
    return rgb_str


def hex_to_rgb_whitened(colour):
    rgb_str = (tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4)))
    white = (255, 255, 255)
    whitened_value = str(((rgb_str[0] + white[0]) / 2, (rgb_str[1] + white[1]) / 2, (rgb_str[2] + white[2]) / 2))
    whitened_value = whitened_value.rstrip(")")
    whitened_value = whitened_value.lstrip("(")
    return whitened_value

# The number of custom images held. Will allow users to randomly be assigned an image on sign_up
number_of_custom_images = 32


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    location = models.CharField(max_length=120, null=True, blank=True)
    nickname = models.CharField(max_length=20, null=True, blank=True)
    picture_id = models.IntegerField(default=1, null=False, blank=False)
    colour = models.CharField(max_length=7, null=False, blank=False, default="D3D3D3")
    groups = models.ManyToManyField(
        CommunityGroup,
        through='Wallet',
        through_fields=('profile', 'group'),
        related_name="groups_profile"
    )

    @property
    def colour_rgb(self):
        return hex_to_rgb(self.colour)

    @property
    def colour_rgb_whitened(self):
        return hex_to_rgb_whitened(self.colour)

    def __str__(self):
        return self.user.username

class Wallet(models.Model):
    profile = models.ForeignKey(Profile, related_name='profiles_wallet', blank=False, null=False, on_delete=models.PROTECT)
    group = models.ForeignKey(CommunityGroup, related_name='groups_wallet', blank=False, null=False, on_delete=models.PROTECT)
    withdrawable_bank = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    non_withdrawable_bank = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    nickname = models.CharField(max_length=20, null=True, blank=True)
    picture_id = models.IntegerField(default=1, null=False, blank=False)
    colour = models.CharField(max_length=7, null=True, blank=True)
    ranking = models.IntegerField(default=0)
    founder = models.BooleanField(default=False, blank=False, null=False)
    admin = models.BooleanField(default=False, blank=False, null=False)
    inviter = models.ForeignKey(Profile, related_name='inviters_wallet', blank=True, null=True, on_delete=models.PROTECT)
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    active = "active"  # Active member of the group
    deactivated = "deactivated"  # A member who has left or been kicked out of the group
    sent = "sent"  # A user that has been invited to the group
    requesting_invite = "requesting_invite"  # A user that has requested an invited from a private group
    declined = "declined"  # A user that has had their request to join declined
    blocked_by_group = "blocked_by_group"  # A user that has been blocked by the group
    blocked_by_user = "blocked_by_user"  # Where a user has blocked a group from sending invites

    available_statuses = (
        (sent, "Sent"),
        (declined, "Declined"),
        (blocked_by_group, "Blocked by Group"),
        (blocked_by_user, "Blocked by User"),
        (active, "Active"),
        (deactivated, "Deactivated"),
        (requesting_invite, "Requesting Invite")
    )

    status = models.CharField(max_length=30,
                              choices=available_statuses,
                              default=active,
                              null=False,
                              blank=False)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Wallet, self).save(*args, **kwargs)


    @property
    def bank(self):
        return self.withdrawable_bank + self.non_withdrawable_bank

    @property
    def lifetime_winnings(self):
        bets = self.profile.user.user_bets.all()
        lifetime_winnings = 0
        for bet in bets:
            if bet.status == bet.paid:
                lifetime_winnings += bet.winnings
        return lifetime_winnings

    @property
    def colour_rgb(self):
        return hex_to_rgb(self.colour)

    @property
    def colour_rgb_whitened(self):
        return hex_to_rgb_whitened(self.colour)

    class Meta:
        unique_together = ('profile', 'group')

    def __str__(self):
        return str(self.profile.user.username) + "'s Wallet for: " + str(self.group.name)

class Team(models.Model):
    name = models.CharField(max_length=200, null=False)
    api_team_id = models.IntegerField(unique=True, null=True, blank=True)

    picture = models.ImageField(upload_to="teamLogos", null=True, blank=True)
    colour = models.CharField(max_length=7, null=False, blank=False, default="D3D3D3")

    @property
    def colour_rgb(self):
        return hex_to_rgb(self.colour)

    @property
    def colour_rgb_whitened(self):
        return hex_to_rgb_whitened(self.colour)

    def __str__(self):
        return self.name

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance, picture_id=random.randint(0, number_of_custom_images))

# Update the number of users in a community group after wallet creation
@receiver(post_save, sender=Wallet)
def update_number_of_community_users(sender, instance, created, **kwargs):
    if created:
        instance.picture_id = instance.profile.picture_id
        instance.save()

        community_group = instance.group
        number_of_users = len(community_group.groups_profile.all())
        community_group.total_number_users = number_of_users
        community_group.save()

