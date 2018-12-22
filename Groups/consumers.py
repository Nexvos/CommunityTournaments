from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from Games.models import Match, Team
from Bets.models import Bet, MatchBettingGroup as BettingGameGroup
from Profiles.models import Wallet, Profile
from django.shortcuts import get_object_or_404
import json
from .forms import BetForm, ChatForm
from django import forms
from django.contrib.auth import get_user_model
User = get_user_model()

def remove_funds(user_wallet, amountBid, ):
    if user_wallet.non_withdrawable_bank >= amountBid:
        user_wallet.non_withdrawable_bank = user_wallet.non_withdrawable_bank - amountBid
        user_wallet.save()
    else:
        amountBid = amountBid - user_wallet.non_withdrawable_bank
        user_wallet.non_withdrawable_bank = 0
        user_wallet.withdrawable_bank = user_wallet.withdrawable_bank - amountBid
        user_wallet.save()

class DataConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.betting_group_id = self.scope['url_route']['kwargs']['betting_group_id']
        self.room_group_name = 'chat_%s' % self.betting_group_id
        self.user = self.scope["user"]
        print(self.betting_group_id)
        self.match_betting_group = get_object_or_404(BettingGameGroup, pk=self.betting_group_id)
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if "amountBid" in text_data_json:
            chosenTeamJson = text_data_json['chosenTeam']
            amountBidJson = text_data_json['amountBid']

            form_data = {
                "chosen_team": chosenTeamJson,
                "amount": amountBidJson
                         }
            form = BetForm(form_data)
            if form.is_valid():
                print("form valid")
                chosenTeam = form.cleaned_data['chosen_team']
                amountBid = form.cleaned_data['amount']
                message = "nothing"
                print(chosenTeam)
                try:
                    chosen_user = User.objects.get(username=chosenTeam)
                    team = chosen_user.profile
                except:
                    team = get_object_or_404(Team, name=chosenTeam)
                user_wallet = Wallet.objects.get(profile=self.user.profile, group=self.match_betting_group.group)
                if amountBid <= user_wallet.bank:
                    if self.match_betting_group.match.user_a == team or self.match_betting_group.match.user_b == team:

                        remove_funds(user_wallet, amountBid)
                        newBet = Bet(wallet=user_wallet, match_betting_group=self.match_betting_group, chosen_user=team, amount=amountBid)
                        newBet.save()

                        # Send message to room group
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'send_update',
                                # 'username': self.user,
                                'message': message
                            }
                        )
                    elif self.match_betting_group.match.team_a == team or self.match_betting_group.match.team_b == team:
                        remove_funds(user_wallet, amountBid)
                        newBet = Bet(wallet=user_wallet, match_betting_group=self.match_betting_group, chosen_team=team, amount=amountBid)
                        newBet.save()

                        # Send message to room group
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'send_update',
                                # 'username': self.user,
                                'message': message
                            }
                        )
                    else:
                        raise forms.ValidationError("Team Value is not valid")
                else:
                    raise forms.ValidationError("User does not have the money to make this bet")
            else:
                raise forms.ValidationError("Form is not valid")
        elif "chat_message" in text_data_json:
            chat_message = text_data_json['chat_message']

            form_data = {
                "chat_message": chat_message
            }
            form = ChatForm(form_data)
            if form.is_valid():
                chat_message = form.cleaned_data['chat_message']
                print(chat_message)
                chat_message = chat_message
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_chat_message',
                        'username': self.user.username,
                        'message': chat_message
                    }
                )
            else:
                raise forms.ValidationError("Form is not valid")
        else:
            print("Not correct form")

    async def send_update(self, event):
        message = event['message']
        self.match_betting_group = get_object_or_404(BettingGameGroup, pk=self.betting_group_id)
        data = '['
        qs = self.match_betting_group.mbg_bets.all()
        total_bet = 0
        count = 0
        for bet in qs:
            total_bet += bet.amount
        for bet in qs:
            if bet.chosen_team:
                chosen = bet.chosen_team
            else:
                chosen = bet.chosen_user
            data += '{"name": "'+ str(bet.wallet.profile.user) + '", "amount": ' + str(bet.amount) + ', "percent": ' + str((bet.amount / total_bet)*100) + ', "team": "' + str(chosen) + '", "colour": "' + "#"+ str(bet.wallet.profile.colour) + '"}'
            count += 1
            if count != qs.count():
                data += ","
        data += ']'
        total_bet = str(total_bet)
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': data,
            'total_bet': total_bet
        }))

    async def send_chat_message(self, event):
        message = event['message']
        chat_user = event['username']
        # user_colour = event.user.profile.colour
        await self.send(text_data=json.dumps({
            'message': str(message),
            'chat_user': chat_user,
            # 'user_colour': user_colour
        }))