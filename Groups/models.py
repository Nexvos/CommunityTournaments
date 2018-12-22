from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class CommunityGroup(models.Model):
    name = models.CharField(max_length=200, null=False, unique=True)
    private = models.BooleanField(default=False)
    daily_payout = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    removable = models.BooleanField(default=True)
    max_users = models.IntegerField(default=32, blank=False, null=False)
    total_users = models.IntegerField(default=0, editable=False)
    members_can_inv = models.BooleanField(default=True)
    header_background_colour = models.CharField(max_length=7, null=False, blank=False, default="ffffff")
    header_text_colour = models.CharField(max_length=7, null=False, blank=False, default="000000")

    active = "active"
    deactivated = "deactivated"

    available_statuses = ((active, "Active"),
                           (deactivated, "Deactivated"))

    status = models.CharField(max_length=30,
                              choices=available_statuses,
                              default=active,
                              null=False,
                              blank=False)

    def __str__(self):
        return self.name

