# Generated by Django 2.1.3 on 2018-11-11 13:07

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Groups', '0001_initial'),
        ('Profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_match_id', models.IntegerField(blank=True, null=True, unique=True)),
                ('api_modified_at', models.DateTimeField(blank=True, null=True, verbose_name='api_modified_at')),
                ('start_datetime', models.DateTimeField(verbose_name='Game start datetime')),
                ('estimated_duration', models.DurationField(default=datetime.timedelta(0, 120))),
                ('twitch_url', models.URLField(blank=True, null=True, unique=True)),
                ('winner', models.CharField(choices=[('Not Decided', 'Not Decided'), ('A is the winner', 'A is the winner'), ('B is the winner', 'B is the winner')], default='Not Decided', max_length=60)),
                ('status', models.CharField(choices=[('not_started', 'Not started'), ('Starting', 'Starting'), ('running', 'Running'), ('finished', 'Finished'), ('Finished - Not yet confirmed', 'Finished - Not yet confirmed'), ('Finished - Confirmed', 'Finished - Confirmed'), ('Finished - All bets paid', 'Finished - All bets paid')], default='not_started', max_length=30)),
                ('team_a', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_team_a', to='Profiles.Team')),
                ('team_b', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_team_b', to='Profiles.Team')),
            ],
        ),
        migrations.CreateModel(
            name='Series',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('api_series_id', models.IntegerField(blank=True, null=True)),
                ('api_modified_at', models.DateTimeField(blank=True, null=True, verbose_name='api_modified_at')),
                ('start_datetime', models.DateTimeField(verbose_name='Series start date')),
                ('end_datetime', models.DateTimeField(blank=True, null=True, verbose_name='Series end date')),
                ('twitch_url', models.URLField(blank=True, null=True, unique=True)),
                ('status', models.CharField(choices=[('Not begun', 'Not begun'), ('Ongoing', 'Ongoing'), ('Finished', 'Finished')], default='Not begun', max_length=30)),
                ('groups', models.ManyToManyField(related_name='group_series', to='Groups.CommunityGroup')),
                ('owning_group', models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='owning_group_series', to='Groups.CommunityGroup')),
            ],
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('api_tournament_id', models.IntegerField(blank=True, null=True, unique=True)),
                ('api_modified_at', models.DateTimeField(blank=True, null=True, verbose_name='api_modified_at')),
                ('start_datetime', models.DateTimeField(verbose_name='Tournament start date')),
                ('end_datetime', models.DateTimeField(blank=True, null=True, verbose_name='Tournament end date')),
                ('status', models.CharField(choices=[('Not begun', 'Not begun'), ('Ongoing', 'Ongoing'), ('Finished', 'Finished')], default='Not begun', max_length=30)),
                ('series', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='series_tournaments', to='Games.Series')),
            ],
        ),
        migrations.CreateModel(
            name='Videogame',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='LoL', max_length=30, unique=True)),
                ('api_videogame_id', models.IntegerField(blank=True, null=True, unique=True)),
                ('picture', models.ImageField(blank=True, null=True, upload_to='teamLogos')),
                ('colour', models.CharField(default='D3D3D3', max_length=7)),
                ('alt_colour', models.CharField(default='D3D3D3', max_length=7)),
            ],
        ),
        migrations.AddField(
            model_name='tournament',
            name='videogame',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='videogame_tournaments', to='Games.Videogame'),
        ),
        migrations.AddField(
            model_name='match',
            name='tournament',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tournament_matches', to='Games.Tournament'),
        ),
        migrations.AddField(
            model_name='match',
            name='user_a',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_user_a', to='Profiles.Profile'),
        ),
        migrations.AddField(
            model_name='match',
            name='user_b',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_user_b', to='Profiles.Profile'),
        ),
    ]
