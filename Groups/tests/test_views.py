from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib import auth
from django.urls import reverse
from Groups.models import CommunityGroup
from Games.models import Tournament, Match
from Profiles.models import Wallet
from django.utils import timezone
User = get_user_model()


# TODO: test registered users get directed to home page
# TODO: Test unregistered users can't access any page apart from the landing page or accounts pages
# TODO: test the context of group based views always pass the correct group etc

# Create your tests here.
class UrlTests(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create a group to be used in URLs
        test_group = CommunityGroup.objects.create(name="testgroup")

        # create a tournament for tournament url tests
        test_tournament = Tournament.objects.create(name="test_tournament", owning_group=test_group, start_datetime=timezone.now())

        # Create users and match for match_page test
        user_1 = User.objects.create(username='testuser1')
        user_2 = User.objects.create(username='testuser2')
        test_match = Match.objects.create(user_a=user_1.profile, user_b=user_2.profile, tournament=test_tournament, start_datetime=timezone.now())

    def test_homepage(self):
        url = reverse('groups:home')
        self.assertEqual(url, '/')

    def test_search_groups(self):
        url = reverse('groups:groupSearch')
        self.assertEqual(url, '/search/')

    def test_create_group(self):
        url = reverse('groups:createGroup')
        self.assertEqual(url, '/create/')

    def test_group_page(self):
        url = reverse('groups:groupPage', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/')

    def test_group_invite(self):
        url = reverse('groups:invitePage', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/invite/')

    def test_group_admin(self):
        url = reverse('groups:adminPage', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/admin/')

    def test_group_admin_edit_game(self):
        url = reverse('groups:adminPageEditGames', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/admin/games/edit/')

    def test_group_admin_add_game(self):
        url = reverse('groups:adminPageAddGames', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/admin/games/add/')

    def test_group_admin_edit_tournament(self):
        url = reverse('groups:adminPageEditTournament', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/admin/tournaments/edit/')

    def test_group_admin_add_tournament(self):
        url = reverse('groups:adminPageAddTournament', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/admin/tournaments/add/')

    def test_group_admin_members(self):
        url = reverse('groups:adminPageMembers', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/admin/members/')

    def test_group_tournament_list(self):
        url = reverse('groups:tournament_list_view', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/tournaments/')

    def test_group_tournament(self):

        url = reverse('groups:tournament_view', kwargs={"group_id": 1, "tournament_id": 1})
        self.assertEqual(url, '/1/tournaments/1/')

    def test_match_page(self):
        url = reverse('groups:detail', kwargs={"group_id": 1, "betting_group_id": 1})
        self.assertEqual(url, '/1/1/')

    def test_completed_games_list(self):
        url = reverse('groups:completed_games_list_view', kwargs={"group_id": 1})
        self.assertEqual(url, '/1/completed-games/')


class HomepageRedirectTests(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

    def test_homepage_with_login(self):
        # Log user in
        self.client.login(username='testuser', password='12345')

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Issue a GET request.
        address = reverse('groups:home')
        response = self.client.get(address)

        # Assert that the user has NOT been redirected (user should be redirected when not logged in)
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_homepage_redirect_without_login(self):
        # Issue a GET request.
        address = reverse('groups:home')
        response = self.client.get(address, follow=True)

        # Check that the response is 302 OK.
        self.assertRedirects(response, '/join/', status_code=302, target_status_code=200)

class HomepagePostTests(TestCase):

    # User must have a valid invite with the correct status (sent)
    # Test 1: Accept a valid invite (Change invite status to Active)
    # Test 2: Decline a valid invite (Change invite status to declined)
    # Test 3: Accept an invite belonging to another user (should add a form error and not change the status)
    # Test 4: Accept an invite where the status is not "sent" (should add a form error and not change the status)
    # Test 5: Invalid form (shouldn't change the invite and should reload the page only)

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

        # create group
        group_name = "test_group_1"
        invite_only = True
        members_can_invite = True
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        group_object = CommunityGroup.objects.create(
            name=group_name,
            private=invite_only,
            members_can_inv=members_can_invite,
            header_background_colour=header_background_colour,
            header_text_colour=header_text_colour,
            daily_payout=daily_payout
        )

        # Create wallet/ invite
        invite = Wallet.objects.create(
            profile=user.profile,
            group=group_object,
            status=Wallet.sent
        )
        self.invite = invite

    def test_1_homepage_accept_invite(self):
        # Log user in
        self.client.login(username='testuser', password='12345')

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:home')

        accept_invite = True

        response = self.client.post(address, {
            'wallet_id': self.invite.id,
            'accept_invite': accept_invite
        })

        # re-fetch the Wallet object
        self.invite = Wallet.objects.get(id=self.invite.id)

        # check the wallet status was changed correctly
        self.assertEqual(self.invite.status, Wallet.active)

        # Check that the page was reloaded
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_2_homepage_decline_invite(self):
        # Log user in
        self.client.login(username='testuser', password='12345')

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:home')

        accept_invite = False

        response = self.client.post(address, {
            'wallet_id': self.invite.id,
            'accept_invite': accept_invite
        })

        # re-fetch the Wallet object
        self.invite = Wallet.objects.get(id=self.invite.id)

        # check the wallet status was changed correctly
        self.assertEqual(self.invite.status, Wallet.declined)

        # Check that the page was reloaded
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_3_homepage_accept_other_users_invite(self):
        # Create not-invited user
        not_invited_user = User.objects.create(username='not_invited_user')
        not_invited_user.set_password('12345')
        not_invited_user.save()

        # Log user in
        self.client.login(username='not_invited_user', password='12345')

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:home')

        accept_invite = True

        response = self.client.post(address, {
            'wallet_id': self.invite.id,
            'accept_invite': accept_invite
        })

        # Assert that the error
        self.assertFormError(response, 'form', None, "You are not the owner of this invite.")

        # re-fetch the Wallet object
        self.invite = Wallet.objects.get(id=self.invite.id)

        # check the wallet status was changed correctly
        self.assertEqual(self.invite.status, Wallet.sent)

        # Check that the page was reloaded
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_4_homepage_accept_not_sent_invite(self):
        # Log user in
        self.client.login(username='testuser', password='12345')

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Change invite/ wallet status to not sent (active in this case)
        self.invite.status = self.invite.active
        self.invite.save()

        address = reverse('groups:home')

        accept_invite = True

        response = self.client.post(address, {
            'wallet_id': self.invite.id,
            'accept_invite': accept_invite
        })

        # Assert that the error
        self.assertFormError(response, 'form', None, "This invite is not active.")

        # re-fetch the Wallet object
        self.invite = Wallet.objects.get(id=self.invite.id)

        # check the wallet status was changed correctly
        self.assertEqual(self.invite.status, Wallet.active)

        # Check that the page was reloaded
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_5_invalid_form(self):
        # Log user in
        self.client.login(username='testuser', password='12345')

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:home')

        accept_invite = True

        response = self.client.post(address, {
            'wallet_id': "abc",
            'accept_invite': accept_invite
        })

        form = response.context[-1]['form']

        # Confirm the form isn't valid
        self.assertFalse(form.is_valid())

        # re-fetch the Wallet object
        self.invite = Wallet.objects.get(id=self.invite.id)

        # check the wallet status was changed correctly
        self.assertEqual(self.invite.status, Wallet.sent)

        # Check that the page was reloaded
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)


class CreateGroupTests(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

        # Log user in
        self.client.login(username='testuser', password='12345')

    def test_create_group_form_pass_true(self):
        address = reverse('groups:createGroup')

        group_name = "test_group_1"
        invite_only = True
        members_can_invite = True
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        response = self.client.post(address, {
            "group_name": group_name,
            "invite_only": str(invite_only),
            "members_can_invite": str(members_can_invite),
            "header_background_colour": header_background_colour,
            "header_text_colour": header_text_colour,
            "daily_payout": str(daily_payout)
        })

        group_object = CommunityGroup.objects.get(name=group_name)

        # Check that the response is 302 OK.
        url = reverse('groups:groupPage', kwargs={"group_id": group_object.id})
        self.assertRedirects(response, url, status_code=302, target_status_code=200)

        # check the group was created correctly
        self.assertEqual(group_object.name, group_name)
        self.assertEqual(group_object.private, invite_only)
        self.assertEqual(group_object.members_can_inv, members_can_invite)
        self.assertEqual(group_object.header_background_colour, header_background_colour)
        self.assertEqual(group_object.header_text_colour, header_text_colour)
        self.assertEqual(group_object.daily_payout, daily_payout)

    def test_create_group_form_pass_false(self):
        address = reverse('groups:createGroup')

        group_name = "test_group_1"
        invite_only = False
        members_can_invite = False
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        response = self.client.post(address, {
            "group_name": group_name,
            "invite_only": str(invite_only),
            "members_can_invite": str(members_can_invite),
            "header_background_colour": header_background_colour,
            "header_text_colour": header_text_colour,
            "daily_payout": str(daily_payout)
        })

        group_object = CommunityGroup.objects.get(name=group_name)

        # Check that the response is 302 OK.
        url = reverse('groups:groupPage', kwargs={"group_id": group_object.id})
        self.assertRedirects(response, url, status_code=302, target_status_code=200)

        # check the group was created correctly
        self.assertEqual(group_object.name, group_name)
        self.assertEqual(group_object.private, invite_only)
        self.assertEqual(group_object.members_can_inv, members_can_invite)
        self.assertEqual(group_object.header_background_colour, header_background_colour)
        self.assertEqual(group_object.header_text_colour, header_text_colour)
        self.assertEqual(group_object.daily_payout, daily_payout)


    def test_create_group_form_pass_missing(self):
        address = reverse('groups:createGroup')

        group_name = "test_group_1"
        invite_only = False
        members_can_invite = False
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        response = self.client.post(address, {
            "group_name": group_name,
            "header_background_colour": header_background_colour,
            "header_text_colour": header_text_colour,
            "daily_payout": str(daily_payout)
        })

        group_object = CommunityGroup.objects.get(name=group_name)

        # Check that the response is 302 OK.
        url = reverse('groups:groupPage', kwargs={"group_id": group_object.id})
        self.assertRedirects(response, url, status_code=302, target_status_code=200)

        # check the group was created correctly
        self.assertEqual(group_object.name, group_name)
        self.assertEqual(group_object.private, invite_only)
        self.assertEqual(group_object.members_can_inv, members_can_invite)
        self.assertEqual(group_object.header_background_colour, header_background_colour)
        self.assertEqual(group_object.header_text_colour, header_text_colour)
        self.assertEqual(group_object.daily_payout, daily_payout)


    def test_create_group_form_fail(self):
        address = reverse('groups:createGroup')

        group_name = "test_group_2"
        invite_only = True
        members_can_invite = True
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = True

        response = self.client.post(address, {
            "group_name": group_name,
            "invite_only": str(invite_only),
            "members_can_invite": str(members_can_invite),
            "header_background_colour": header_background_colour,
            "header_text_colour": header_text_colour,
            "daily_payout": str(daily_payout)
        })
        print(CommunityGroup.objects.all())
        with self.assertRaises(CommunityGroup.DoesNotExist):
            CommunityGroup.objects.get(name=group_name)

        # Check that the response is 302 OK.
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)


