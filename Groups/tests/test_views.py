from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib import auth
from django.urls import reverse
from Groups.models import CommunityGroup
from Games.models import Tournament, Match, Videogame
from Profiles.models import Wallet
from Bets.models import MatchBettingGroup
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.template import loader
User = get_user_model()


# TODO: test the context of group based views always pass the correct group etc

# Create your tests here.
class UrlTests(TestCase):
    # Tests to confirm that urls are wired up to the correct address

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
        url = reverse('groups:invitePage', kwargs={"group_id": 1, "page": 1})
        self.assertEqual(url, '/1/invite/1/')

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


class RedirectTests(TestCase):
    # If a user isn't signed-in then they should be redirected from the base url "/" to the landing/ join page
    # Test 1: a registered user tries to access the home url "/" and is NOT redirected
    # Test 2: an unregistered user tries to access the home url and IS redirected to the landing/ join page

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

    def test_1_homepage_with_login(self):
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

    def test_2_homepage_redirect_without_login(self):
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
    # Tests for the create group view
    # Test 1: Check that a valid post request creates the correct group
    # Test 2: Check that a valid post request with different bool values works
    # Test 3: Check that a valid post request with no bool values works (should add them as false)
    # Test 4: Test that the view handles an invalid form correctly

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

        # Log user in
        self.client.login(username='testuser', password='12345')

    def test_1_create_group_form_pass_true(self):
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

    def test_2_create_group_form_pass_false(self):
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

    def test_3_create_group_form_pass_missing(self):
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

    def test_4_create_group_form_fail(self):
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
        with self.assertRaises(CommunityGroup.DoesNotExist):
            CommunityGroup.objects.get(name=group_name)

        # Check that the response is 302 OK.
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)


class GroupSearchTests(TestCase):
    # Test 1: Check that the user submitting a valid form CAN join a non-private group (wallet marked as
    # "active")
    # Test 2: Check that the user submitting a valid form to a private (invite only) group sends a request
    # (wallet marked as "requesting_invite")
    # Test 3: Check that the user submitting a valid form CANNOT join a non-private group they are already a member of
    # (status unchanged)
    # Test 4: Check that the user submitting a valid form CANNOT join a private (invite only) group they are already a
    # member of (status unchanged)
    # Test 5: Check that a user is redirected to the login page when not logged in
    # Test 6: If a user has been blocked by a private group (with the status "declined_blocked") then a valid form will
    # provide an error message and leave the wallet unchanged
    # Test 7: If a user has been blocked by a non-private group (with the status "declined_blocked") then a valid form
    # will provide an error message and leave the wallet unchanged

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()

        # Log user in
        self.client.login(username='testuser', password='12345')

        # create private group
        group_name = "test_group_1"
        invite_only = True
        members_can_invite = True
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        self.group_object_private = CommunityGroup.objects.create(
            name=group_name,
            private=invite_only,
            members_can_inv=members_can_invite,
            header_background_colour=header_background_colour,
            header_text_colour=header_text_colour,
            daily_payout=daily_payout
        )

        # create non-private group
        group_name = "test_group_2"
        invite_only = False
        members_can_invite = False
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        self.group_object_not_private = CommunityGroup.objects.create(
            name=group_name,
            private=invite_only,
            members_can_inv=members_can_invite,
            header_background_colour=header_background_colour,
            header_text_colour=header_text_colour,
            daily_payout=daily_payout
        )

    def test_1_join_not_private_group(self):
        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupSearch')

        group_id = self.group_object_not_private.id

        # Send the post request
        response = self.client.post(address, {
            "group_id": group_id
        })

        # Get the newly created wallet
        wallet = Wallet.objects.get(
            profile=self.user.profile,
            group=self.group_object_not_private
        )

        # check the wallet was created correct status
        self.assertEqual(wallet.status, Wallet.active)

        # Check that the response is 302 OK.
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_2_request_inv_from_private_group(self):
        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupSearch')

        group_id = self.group_object_private.id

        # Send the post request
        response = self.client.post(address, {
            "group_id": group_id
        })

        # Get the newly created wallet
        wallet = Wallet.objects.get(
            profile=self.user.profile,
            group=self.group_object_private
        )

        # check the wallet was created correct status
        self.assertEqual(wallet.status, Wallet.requesting_invite)

        # Check that the response is 302 OK.
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_3_join_group_existing_member(self):
        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupSearch')

        # Set wallet attributes
        group_id = self.group_object_not_private.id
        status = Wallet.active

        # Create existing relationship with group
        wallet = Wallet.objects.create(
            profile=self.user.profile,
            group=self.group_object_not_private,
            status=status
        )

        # Send the post request
        response = self.client.post(address, {
            "group_id": group_id
        })

        # Get the newly created wallet
        wallet = Wallet.objects.get(
            profile=self.user.profile,
            group=self.group_object_not_private
        )

        # check the wallet maintains correct status
        self.assertEqual(wallet.status, Wallet.active)

        # Assert that the error is correct
        self.assertFormError(response, 'form', None, "You are already a member of this group.")

        # Check that the response is 302 OK.
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_4_request_inv_existing_member(self):
        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupSearch')

        # Set wallet attributes
        group_id = self.group_object_private.id
        status = Wallet.active

        # Create existing relationship with group
        wallet = Wallet.objects.create(
            profile=self.user.profile,
            group=self.group_object_private,
            status=status
        )

        # Send the post request
        response = self.client.post(address, {
            "group_id": group_id
        })

        # Get the newly created wallet
        wallet = Wallet.objects.get(
            profile=self.user.profile,
            group=self.group_object_private
        )

        # check the wallet maintains correct status
        self.assertEqual(wallet.status, Wallet.active)

        # Assert that the error is correct
        self.assertFormError(response, 'form', None, "You are already a member of this group.")

        # Check that the response is 302 OK.
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_5_redirect_if_not_logged(self):
        # Logout
        self.client.logout()

        # Assert that the user is not logged in
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

        address = reverse('groups:groupSearch')

        # Set group_id for post request
        group_id = self.group_object_private.id

        # Send the post request
        response = self.client.post(address, {
            "group_id": group_id
        })

        # Check that the response is 302 OK.
        self.assertRedirects(response, '/accounts/login/', status_code=302, target_status_code=200)

    def test_6_deny_blocked_user_private(self):
        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupSearch')

        # Set wallet attributes
        group_id = self.group_object_private.id
        status = Wallet.declined_blocked

        # Create existing relationship with group
        wallet = Wallet.objects.create(
            profile=self.user.profile,
            group=self.group_object_private,
            status=status
        )

        # Send the post request
        response = self.client.post(address, {
            "group_id": group_id
        })

        # (Re-)get the wallet
        wallet = Wallet.objects.get(
            profile=self.user.profile,
            group=self.group_object_private
        )

        # check the wallet maintains correct status
        self.assertEqual(wallet.status, Wallet.declined_blocked)

        # Assert that the error is correct
        self.assertFormError(response, 'form', None, "This group has blocked you. Please contact the group admin.")

        # Check that the response is 302 OK.
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_7_deny_blocked_user_not_private(self):
        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupSearch')

        # Set wallet attributes
        group_id = self.group_object_not_private.id
        status = Wallet.declined_blocked

        # Create existing relationship with group
        wallet = Wallet.objects.create(
            profile=self.user.profile,
            group=self.group_object_not_private,
            status=status
        )

        # Send the post request
        response = self.client.post(address, {
            "group_id": group_id
        })

        # (Re-)get the wallet
        wallet = Wallet.objects.get(
            profile=self.user.profile,
            group=self.group_object_not_private
        )

        # check the wallet maintains correct status
        self.assertEqual(wallet.status, Wallet.declined_blocked)

        # Assert that the error is correct
        self.assertFormError(response, 'form', None, "This group has blocked you. Please contact the group admin.")

        # Check that the response is 302 OK.
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)


class GroupPageTests(TestCase):
    # There are 3 groups of tournaments passed through context variables:
    #   1: "upcoming_tournaments" - start date is in the future, but not more than 3 months into the future
    #   2: "ongoing_tournaments1" and "ongoing_tournaments2" - Start date is in the past and the end date is in the
    #   future - Also split into two other variables splitting the list in half
    #   3: "completed_tournaments" - End date is in the past, but not more than 3 months ago
    # ---
    # The latest 12 matches are passed into the context variable "latest_game_list" - These are ordered by the start
    # date of the match and must not be any status given to "completed" games
    # ---
    # When a url variable "q" is given, then the tournaments and matches must be filtered to only contain tournaments
    # and matches for that videogame
    # ---
    # Only members of the group should be able to access this group - non-members should be presented with a 404

    # Test 1: Check that a user is redirected to the login page when not logged in
    # Test 2: Check that a user that isn't a member of the group is delivered a 404
    # Test 3: Check that a user that has a wallet with the associated group that is not active is delivered a 404
    # Test 4: Check that a user with a wallet associated with the group, which is active is delivered the correct page
    # Test 5: Check that "upcoming_tournaments" contains tournaments in the correct range and not outside
    # Test 6: Check that the url variable q correctly filters "upcoming_tournaments"
    # Test 7: Check that "ongoing_tournaments1" and "ongoing_tournaments2" contains tournaments in the correct range
    # and not outside - Also that "ongoing_tournaments1" + "ongoing_tournaments2" contain all ongoing tournaments
    # Test 8: Check that the url variable q correctly filters "ongoing_tournaments1" and "ongoing_tournaments2"
    # Test 9: Check that "completed_tournaments" contains tournaments in the correct range and not outside
    # Test 10: Check that the url variable q correctly filters "completed_tournaments"
    # Test 11: Check that "latest_game_list" Will provide only the most recent 12 games in the correct order
    # Test 12: Check that the url variable q correctly filters "latest_game_list"

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()

        # Log user in
        self.client.login(username='testuser', password='12345')

        # create a group
        group_name = "test_group_1"
        invite_only = True
        members_can_invite = True
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        self.group_object = CommunityGroup.objects.create(
            name=group_name,
            private=invite_only,
            members_can_inv=members_can_invite,
            header_background_colour=header_background_colour,
            header_text_colour=header_text_colour,
            daily_payout=daily_payout
        )

        # Create wallet between the user and group
        self.wallet = Wallet.objects.create(
            profile=self.user.profile,
            group=self.group_object,
            status=Wallet.active
        )

    def test_1_redirect_when_not_logged(self):
        # Log the user out
        self.client.logout()

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 302 OK.
        self.assertRedirects(response, '/accounts/login/', status_code=302, target_status_code=200)

    def test_2_404_when_not_associated(self):
        # Delete existing wallet
        self.wallet.delete()

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 404.
        self.assertEqual(response.status_code, 404)

    def test_3_404_when_not_active(self):
        # Change wallet status to deactivated
        self.wallet.status = Wallet.deactivated
        self.wallet.save()

        # Ensure the wallet's status was changed
        self.assertEqual(self.wallet.status, Wallet.deactivated)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 404
        self.assertEqual(response.status_code, 404)

    def test_4_200_when_active(self):
        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 200
        self.assertEqual(response.status_code, 200)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_5_upcoming_tournaments(self):
        # "upcoming_tournaments" - start date must be in the future, but not more than 3 months into the future
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create tournaments
        # Tournament 1: 1 hour in the future - Should be in the variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1)
        )
        # Tournament 2: 1 hour in the past - Shouldn't be in the variable
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1)
        )
        # Tournament 3: 89 days in the future - Should be in the variable
        tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(days=89)
        )
        # Tournament 4: 91 days in the future - Shouldn't be in the variable
        tournament_4 = Tournament.objects.create(
            name="tournament_4",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(days=91)
        )

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Get the context
        upcoming_tournaments = response.context['upcoming_tournaments']

        # Check that tournament_1 and tournament_3 are in upcoming_tournaments
        self.assertIn(tournament_1, upcoming_tournaments)
        self.assertIn(tournament_3, upcoming_tournaments)

        # Check that tournament_2 and tournament_4 are not in upcoming_tournaments
        self.assertNotIn(tournament_2, upcoming_tournaments)
        self.assertNotIn(tournament_4, upcoming_tournaments)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_6_filter_upcoming_tournaments(self):
        # "upcoming_tournaments" - start date must be in the future, but not more than 3 months into the future
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create a videogame to test
        videogame_name = "SC2"
        videogame_1 = Videogame.objects.create(
            name=videogame_name
        )
        videogame_2 = Videogame.objects.create(
            name="not_SC2"
        )

        # Create tournaments
        # Tournament 1: 1 hour in the future - Should be in the variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1),
            videogame=videogame_1
        )
        tournament_1_filter = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1)
        )

        # Tournament 3: 89 days in the future - Should be in the variable
        tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(days=89),
            videogame=videogame_1
        )
        tournament_3_filter = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(days=89),
            videogame= videogame_2
        )

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        address = address + "?q=" + videogame_name

        # Send the get request
        response = self.client.get(address)

        # Get the context
        upcoming_tournaments = response.context['upcoming_tournaments']

        # Check that tournament_1 and tournament_3 are in upcoming_tournaments
        self.assertIn(tournament_1, upcoming_tournaments)
        self.assertIn(tournament_3, upcoming_tournaments)

        # Check that tournament_1_filter and tournament_3_filter are not in upcoming_tournaments
        self.assertNotIn(tournament_1_filter, upcoming_tournaments)
        self.assertNotIn(tournament_3_filter, upcoming_tournaments)

    def test_7_ongoing_tournaments(self):
        # "ongoing_tournaments1" + "ongoing_tournaments2" - start date must be in the past and end dates must be in
        # the future
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create tournaments
        # Tournament 1: start date one hour in the past and end date one hour in the future - Should be in the variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1)
        )
        # Tournament 2: start date two hours in the past and end date one hour in the past - Shouldn't be in the
        # variable
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=2),
            end_datetime=timezone.now() - timezone.timedelta(hours=1)
        )
        # Tournament 3: start date one hour in the future and end date two hours in the future - Shouldn't be in the
        # variable
        tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=2)
        )

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Get the context
        ongoing_tournaments1 = response.context['ongoing_tournaments1']
        ongoing_tournaments2 = response.context['ongoing_tournaments2']

        ongoing_tournaments = ongoing_tournaments1 + ongoing_tournaments2

        # Check that tournament_1 and tournament_3 are in upcoming_tournaments
        self.assertIn(tournament_1, ongoing_tournaments)

        # Check that tournament_2 and tournament_4 are not in upcoming_tournaments
        self.assertNotIn(tournament_2, ongoing_tournaments)
        self.assertNotIn(tournament_3, ongoing_tournaments)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_8_filter_ongoing_tournaments(self):
        # "ongoing_tournaments1" + "ongoing_tournaments2" - start date must be in the past and end dates must be in
        # the future
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create a videogame to test
        videogame_name = "SC2"
        videogame_1 = Videogame.objects.create(
            name=videogame_name
        )
        videogame_2 = Videogame.objects.create(
            name="not_SC2"
        )

        # Create tournaments
        # Tournament 1: start date one hour in the past and end date one hour in the future - Should be in the variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1),
            videogame= videogame_1
        )
        tournament_1_filter_1 = Tournament.objects.create(
            name="tournament_1_filter_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1),
            videogame=videogame_2
        )
        tournament_1_filter_2 = Tournament.objects.create(
            name="tournament_1_filter_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1)
        )

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})
        address = address + "?q=" + videogame_name

        # Send the get request
        response = self.client.get(address)

        # Get the context
        ongoing_tournaments1 = response.context['ongoing_tournaments1']
        ongoing_tournaments2 = response.context['ongoing_tournaments2']

        ongoing_tournaments = ongoing_tournaments1 + ongoing_tournaments2

        # Check that tournament_1 and tournament_3 are in upcoming_tournaments
        self.assertIn(tournament_1, ongoing_tournaments)

        # Check that tournament_2 and tournament_4 are not in upcoming_tournaments
        self.assertNotIn(tournament_1_filter_1, ongoing_tournaments)
        self.assertNotIn(tournament_1_filter_2, ongoing_tournaments)

    def test_9_completed_tournaments(self):
        # "completed_tournaments" - start date must be in the past and end dates must be in the past but not ended more
        # than 90 days ago
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create tournaments
        # Tournament 1: start date one hour in the past and end date one hour in the future - Shouldn't be in the
        # variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1)
        )
        # Tournament 2: start date two hours in the past and end date one hour in the past - Should be in the variable
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=2),
            end_datetime=timezone.now() - timezone.timedelta(hours=1)
        )
        # Tournament 3: start date one hour in the future and end date two hours in the future - Shouldn't be in the
        # variable
        tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=2)
        )
        # Tournament 4: start date 100 days in the past and end date 89 days in the past - Should be in the
        # variable
        tournament_4 = Tournament.objects.create(
            name="tournament_4",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=100),
            end_datetime=timezone.now() - timezone.timedelta(days=89)
        )
        # Tournament 5: start date 100 days in the past and end date 91 days in the past - Shouldn't be in the
        # variable
        tournament_5 = Tournament.objects.create(
            name="tournament_5",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=100),
            end_datetime=timezone.now() - timezone.timedelta(days=91)
        )
        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Get the context
        completed_tournaments = response.context['completed_tournaments']

        # Check that tournament_2 and tournament_4 are in completed_tournaments
        self.assertIn(tournament_2, completed_tournaments)
        self.assertIn(tournament_4, completed_tournaments)

        # Check that tournament_1, tournament_3 and tournament_5 are not in upcoming_tournaments
        self.assertNotIn(tournament_1, completed_tournaments)
        self.assertNotIn(tournament_3, completed_tournaments)
        self.assertNotIn(tournament_5, completed_tournaments)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_10_filter_completed_tournaments(self):
        # "completed_tournaments" - start date must be in the past and end dates must be in the past but not ended more
        # than 90 days ago
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create a videogame to test
        videogame_name = "SC2"
        videogame_1 = Videogame.objects.create(
            name=videogame_name
        )
        videogame_2 = Videogame.objects.create(
            name="not_SC2"
        )

        # Create tournaments

        # Tournament 2: start date two hours in the past and end date one hour in the past - Should be in the variable
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=2),
            end_datetime=timezone.now() - timezone.timedelta(hours=1),
            videogame=videogame_1
        )
        tournament_2_filter = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=2),
            end_datetime=timezone.now() - timezone.timedelta(hours=1),
            videogame=videogame_2
        )
        # Tournament 4: start date 100 days in the past and end date 89 days in the past - Should be in the
        # variable
        tournament_4 = Tournament.objects.create(
            name="tournament_4",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=100),
            end_datetime=timezone.now() - timezone.timedelta(days=89),
            videogame=videogame_1
        )
        tournament_4_filter = Tournament.objects.create(
            name="tournament_4",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=100),
            end_datetime=timezone.now() - timezone.timedelta(days=89)
        )
        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})
        address = address + "?q=" + videogame_name

        # Send the get request
        response = self.client.get(address)

        # Get the context
        completed_tournaments = response.context['completed_tournaments']

        # Check that tournament_2 and tournament_4 are in completed_tournaments
        self.assertIn(tournament_2, completed_tournaments)
        self.assertIn(tournament_4, completed_tournaments)

        # Check that tournament_1, tournament_3 and tournament_5 are not in upcoming_tournaments
        self.assertNotIn(tournament_2_filter, completed_tournaments)
        self.assertNotIn(tournament_4_filter, completed_tournaments)

    def test_11_latest_game_list(self):
        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create a second user so a match can be created
        user_2 = User.objects.create(username='testuser2')

        # Create a tournament for the matches
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=20),
            end_datetime=timezone.now() + timezone.timedelta(hours=20)
        )

        # Create matches with varying "start_datetime"s
        match_1 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now(),
            tournament=tournament_1
        )
        match_2 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=1),
            tournament=tournament_1
        )
        match_3 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=2),
            tournament=tournament_1
        )
        match_4 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=3),
            tournament=tournament_1
        )
        match_5 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=4),
            tournament=tournament_1
        )
        match_6 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=5),
            tournament=tournament_1
        )
        match_7 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=6),
            tournament=tournament_1
        )
        match_8 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=7),
            tournament=tournament_1
        )
        match_12 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=11),
            tournament=tournament_1
        )
        match_13 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=12),
            tournament=tournament_1
        )
        match_9 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=8),
            tournament=tournament_1
        )
        match_10 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=9),
            tournament=tournament_1
        )
        match_11 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=10),
            tournament=tournament_1
        )

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Get the context
        latest_game_list = response.context['latest_game_list']

        # Check that each match is in the latest_game_list variable in the correct order
        self.assertEqual(match_1, latest_game_list[0].match)
        self.assertEqual(match_2, latest_game_list[1].match)
        self.assertEqual(match_3, latest_game_list[2].match)
        self.assertEqual(match_4, latest_game_list[3].match)
        self.assertEqual(match_5, latest_game_list[4].match)
        self.assertEqual(match_6, latest_game_list[5].match)
        self.assertEqual(match_7, latest_game_list[6].match)
        self.assertEqual(match_8, latest_game_list[7].match)
        self.assertEqual(match_9, latest_game_list[8].match)
        self.assertEqual(match_10, latest_game_list[9].match)
        self.assertEqual(match_11, latest_game_list[10].match)
        self.assertEqual(match_12, latest_game_list[11].match)

        # Check that the variable only holds the 12 latest matches
        self.assertNotIn(match_13.game_mbgs.all()[0], latest_game_list)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_12_filter_latest_game_list(self):
        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create a second user so a match can be created
        user_2 = User.objects.create(username='testuser2')

        # Create a videogame to test
        videogame_name = "SC2"
        videogame_1 = Videogame.objects.create(
            name=videogame_name
        )
        videogame_2 = Videogame.objects.create(
            name="not_SC2"
        )

        # Create a tournament for the matches
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=20),
            end_datetime=timezone.now() + timezone.timedelta(hours=20),
            videogame=videogame_1
        )
        # Tournaments 2 & 3 should be filtered out
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=20),
            end_datetime=timezone.now() + timezone.timedelta(hours=20),
            videogame=videogame_2
        )
        tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=20),
            end_datetime=timezone.now() + timezone.timedelta(hours=20)
        )

        # Create matches with varying "start_datetime"s
        match_1 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now(),
            tournament=tournament_1
        )
        match_2 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=1),
            tournament=tournament_2
        )
        match_3 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=2),
            tournament=tournament_2
        )
        match_4 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=3),
            tournament=tournament_1
        )
        match_5 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=4),
            tournament=tournament_3
        )
        match_6 = Match.objects.create(
            user_a=self.user.profile,
            user_b=user_2.profile,
            start_datetime=timezone.now() + timezone.timedelta(hours=5),
            tournament=tournament_3
        )

        address = reverse('groups:groupPage', kwargs={'group_id': self.group_object.id})
        address = address + "?q=" + videogame_name
        # Send the get request
        response = self.client.get(address)

        # Get the context
        latest_game_list = response.context['latest_game_list']

        # Check that each match is in the latest_game_list variable in the correct order
        self.assertEqual(match_1, latest_game_list[0].match)
        self.assertEqual(match_4, latest_game_list[1].match)

        # Check that the variable only holds the 12 latest matches
        self.assertNotIn(match_2.game_mbgs.all()[0], latest_game_list)
        self.assertNotIn(match_3.game_mbgs.all()[0], latest_game_list)
        self.assertNotIn(match_5.game_mbgs.all()[0], latest_game_list)
        self.assertNotIn(match_6.game_mbgs.all()[0], latest_game_list)


class LazyLoadTests(TestCase):
    # Lazy_load takes a group_id and a "page" variable via post request
    # - The next 12 games are then sent back to the user
    # --- The games should be filtered by the q variable and only be accessible by users that are a member of that group

    # Matches 1-15 are in tournament 1 ::: 16-29 are in tournament 2 ::: 30 is in tournament 3

    # Test 1: Test that the next 12 games are correctly returned
    # Test 2: Test that only members of the group can request the next 12 games
    # Test 3: Test that the games are correctly filtered with the q variable

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()

        # TODO: currently a user not in a group can be created for a user not active in said group - Can this be fixed
        #  at the model level, or does it have to be at the view level?
        # Create second user for matches
        self.user_2 = User.objects.create(username='testuser2')
        self.user_2.set_password("12345")
        self.user_2.save()

        # create a group
        group_name = "test_group_1"
        invite_only = True
        members_can_invite = True
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        self.group_object = CommunityGroup.objects.create(
            name=group_name,
            private=invite_only,
            members_can_inv=members_can_invite,
            header_background_colour=header_background_colour,
            header_text_colour=header_text_colour,
            daily_payout=daily_payout
        )

        # Create wallet between the user and group
        self.wallet = Wallet.objects.create(
            profile=self.user.profile,
            group=self.group_object,
            status=Wallet.active
        )
        # Create a videogame to test
        self.videogame_1 = Videogame.objects.create(
            name="SC2"
        )
        self.videogame_2 = Videogame.objects.create(
            name="not_SC2"
        )

        # Create a tournament for the matches
        self.tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=20),
            end_datetime=timezone.now() + timezone.timedelta(hours=20),
            videogame=self.videogame_1
        )
        # Tournaments 2 & 3 should be filtered out
        self.tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=20),
            end_datetime=timezone.now() + timezone.timedelta(hours=20),
            videogame=self.videogame_2
        )
        self.tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=20),
            end_datetime=timezone.now() + timezone.timedelta(hours=20)
        )

        # Create matches with varying "start_datetime"s
        self.match_dict = {}
        self.tournament_1_matches = []
        self.tournament_2_matches = []
        self.tournament_3_matches = []
        for x in range(1, 16):
            y = Match.objects.create(
                user_a=self.user.profile,
                user_b=self.user_2.profile,
                start_datetime=timezone.now() + timezone.timedelta(hours=x),
                tournament=self.tournament_1
            )
            g = MatchBettingGroup.objects.get(match=y, group=self.group_object)
            self.match_dict["match_{0}".format(x)] = g
            self.tournament_1_matches.append(g)

        for x in range(16, 30):
            y = Match.objects.create(
                user_a=self.user.profile,
                user_b=self.user_2.profile,
                start_datetime=timezone.now() + timezone.timedelta(hours=x),
                tournament=self.tournament_2
            )
            g = MatchBettingGroup.objects.get(match=y, group=self.group_object)
            self.match_dict["match_{0}".format(x)] = g
            self.tournament_2_matches.append(g)

        for x in range(30, 31):
            y = Match.objects.create(
                user_a=self.user.profile,
                user_b=self.user_2.profile,
                start_datetime=timezone.now() + timezone.timedelta(hours=x),
                tournament=self.tournament_3
            )
            g = MatchBettingGroup.objects.get(match=y, group=self.group_object)
            self.match_dict["match_{0}".format(x)] = g
            self.tournament_3_matches.append(g)

    def test_1_(self):
        # Log user in
        self.client.login(username='testuser', password='12345')

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        page = 2
        results_per_page = 12
        matches = self.tournament_1_matches + self.tournament_2_matches + self.tournament_3_matches
        paginator = Paginator(matches, results_per_page)

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
                'group': self.group_object,
            }
        )
        additional_html = "<script>var loop_number=" + str(int(page) * results_per_page - results_per_page) + "</script>"
        # package output data and return it as a JSON object
        output_data = {
            'games_list_html': additional_html + games_list_html,
            'has_next': games.has_next()
        }
        test_data = JsonResponse(output_data).content

        address = reverse('groups:lazy_load_posts', kwargs={"group_id": self.group_object.id})

        response = self.client.post(address, {
            "page": page
        })

        self.assertEqual(test_data, response.content)
        # Check that the response is 200.
        self.assertEqual(response.status_code, 200)

    def test_2_(self):
        # Log user in to user2
        self.client.login(username='testuser2', password='12345')

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        page = 2

        address = reverse('groups:lazy_load_posts', kwargs={"group_id": self.group_object.id})

        response = self.client.post(address, {
            "page": page
        })

        # Check that the response is 404.
        self.assertEqual(response.status_code, 404)

    def test_3_(self):
        # Log user in
        self.client.login(username='testuser', password='12345')

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        page = 2
        results_per_page = 12
        matches = self.tournament_1_matches
        paginator = Paginator(matches, results_per_page)

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
                'group': self.group_object,
            }
        )
        additional_html = "<script>var loop_number=" + str(int(page) * results_per_page - results_per_page) + "</script>"
        # package output data and return it as a JSON object
        output_data = {
            'games_list_html': additional_html + games_list_html,
            'has_next': games.has_next()
        }
        test_data = JsonResponse(output_data).content

        address = reverse('groups:lazy_load_posts', kwargs={"group_id": self.group_object.id})
        address = address + "?q=" + self.videogame_1.name
        response = self.client.post(address, {
            "page": page
        })

        self.assertEqual(test_data, response.content)
        # Check that the response is 200.
        self.assertEqual(response.status_code, 200)


class TournamentListViewTests(TestCase):
    # There are 3 groups of tournaments passed through context variables:
    #   1: "upcoming_tournaments" - start date is in the future with no cut off
    #   2: "ongoing_tournaments" - Start date is in the past and the end date is in the future
    #   3: "completed_tournaments" - End date is in the past with no cut off
    # ---
    #
    # When a url variable "q" is given, then the tournaments must be filtered to only contain tournaments
    # and matches for that videogame name
    # ---
    # Only members of the group should be able to access this group - non-members should be presented with a 404

    # Test 1: Check that a user is redirected to the login page when not logged in
    # Test 2: Check that a user that isn't a member of the group is delivered a 404
    # Test 3: Check that a user that has a wallet with the associated group that is not active is delivered a 404
    # Test 4: Check that a user with a wallet associated with the group, which is active is delivered the correct page
    # Test 5: Check that the "upcoming_tournaments" variable is the correct list
    # Test 6: Check that the "upcoming_tournaments" variable is correctly filtered with a q variable
    # Test 7: Check that the "ongoing_tournaments" variable is the correct list
    # Test 8: Check that the "ongoing_tournaments" variable is correctly filtered with a q variable
    # Test 9: Check that the "completed_tournaments" variable is the correct list
    # Test 10: Check that the "completed_tournaments" variable is correctly filtered with a q variable

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create user
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()

        # Log user in
        self.client.login(username='testuser', password='12345')

        # create a group
        group_name = "test_group_1"
        invite_only = True
        members_can_invite = True
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        self.group_object = CommunityGroup.objects.create(
            name=group_name,
            private=invite_only,
            members_can_inv=members_can_invite,
            header_background_colour=header_background_colour,
            header_text_colour=header_text_colour,
            daily_payout=daily_payout
        )

        # Create wallet between the user and group
        self.wallet = Wallet.objects.create(
            profile=self.user.profile,
            group=self.group_object,
            status=Wallet.active
        )
        self.url = "groups:tournament_list_view"

    def test_1_redirect_when_not_logged(self):
        # Log the user out
        self.client.logout()

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 302 OK.
        self.assertRedirects(response, '/accounts/login/', status_code=302, target_status_code=200)

    def test_2_404_when_not_associated(self):
        # Delete existing wallet
        self.wallet.delete()

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 404.
        self.assertEqual(response.status_code, 404)

    def test_3_404_when_not_active(self):
        # Change wallet status to deactivated
        self.wallet.status = Wallet.deactivated
        self.wallet.save()

        # Ensure the wallet's status was changed
        self.assertEqual(self.wallet.status, Wallet.deactivated)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 404
        self.assertEqual(response.status_code, 404)

    def test_4_200_when_active(self):
        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 200
        self.assertEqual(response.status_code, 200)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_5_upcoming_tournaments(self):
        # "upcoming_tournaments" - start date must be in the future
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create tournaments
        # Tournament 1: 1 hour in the future - Should be in the variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1)
        )
        # Tournament 2: 1 hour in the past - Shouldn't be in the variable
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1)
        )
        # Tournament 3: 89 days in the past with an end date in the future - Shouldn't be in the variable
        tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=89),
            end_datetime=timezone.now() +timezone.timedelta(days=1)
        )
        # Tournament 4: 150 days in the future - should be in the variable
        tournament_4 = Tournament.objects.create(
            name="tournament_4",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(days=150)
        )

        address = reverse(self.url, kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Get the context
        upcoming_tournaments = response.context['upcoming_tournaments']

        # Check that tournament_1 and tournament_3 are in upcoming_tournaments
        self.assertIn(tournament_1, upcoming_tournaments)
        self.assertIn(tournament_4, upcoming_tournaments)

        # Check that tournament_2 and tournament_4 are not in upcoming_tournaments
        self.assertNotIn(tournament_2, upcoming_tournaments)
        self.assertNotIn(tournament_3, upcoming_tournaments)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_6_filter_upcoming_tournaments(self):
        # "upcoming_tournaments" - start date must be in the future
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create a videogame to test
        videogame_name = "SC2"
        videogame_1 = Videogame.objects.create(
            name=videogame_name
        )
        videogame_2 = Videogame.objects.create(
            name="not_SC2"
        )

        # Create tournaments
        # Tournament 1: 1 hour in the future - Should be in the variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1),
            videogame=videogame_1
        )
        tournament_1_filter = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1)
        )

        # Tournament 3: 150 days in the future - Should be in the variable
        tournament_4 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(days=150),
            videogame=videogame_1
        )
        tournament_4_filter = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(days=150),
            videogame= videogame_2
        )

        address = reverse(self.url, kwargs={'group_id': self.group_object.id})

        address = address + "?q=" + videogame_name

        # Send the get request
        response = self.client.get(address)

        # Get the context
        upcoming_tournaments = response.context['upcoming_tournaments']

        # Check that tournament_1 and tournament_3 are in upcoming_tournaments
        self.assertIn(tournament_1, upcoming_tournaments)
        self.assertIn(tournament_4, upcoming_tournaments)

        # Check that tournament_1_filter and tournament_3_filter are not in upcoming_tournaments
        self.assertNotIn(tournament_1_filter, upcoming_tournaments)
        self.assertNotIn(tournament_4_filter, upcoming_tournaments)

    def test_7_ongoing_tournaments(self):
        # "ongoing_tournaments1" + "ongoing_tournaments2" - start date must be in the past and end dates must be in
        # the future
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create tournaments
        # Tournament 1: start date one hour in the past and end date one hour in the future - Should be in the variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1)
        )
        # Tournament 2: start date two hours in the past and end date one hour in the past - Shouldn't be in the
        # variable
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=2),
            end_datetime=timezone.now() - timezone.timedelta(hours=1)
        )
        # Tournament 3: start date one hour in the future and end date two hours in the future - Shouldn't be in the
        # variable
        tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=2)
        )

        address = reverse(self.url, kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Get the context
        ongoing_tournaments = response.context['ongoing_tournaments']

        # Check that tournament_1 and tournament_3 are in upcoming_tournaments
        self.assertIn(tournament_1, ongoing_tournaments)

        # Check that tournament_2 and tournament_4 are not in upcoming_tournaments
        self.assertNotIn(tournament_2, ongoing_tournaments)
        self.assertNotIn(tournament_3, ongoing_tournaments)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_8_filter_ongoing_tournaments(self):
        # "ongoing_tournaments1" + "ongoing_tournaments2" - start date must be in the past and end dates must be in
        # the future
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create a videogame to test
        videogame_name = "SC2"
        videogame_1 = Videogame.objects.create(
            name=videogame_name
        )
        videogame_2 = Videogame.objects.create(
            name="not_SC2"
        )

        # Create tournaments
        # Tournament 1: start date one hour in the past and end date one hour in the future - Should be in the variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1),
            videogame= videogame_1
        )
        tournament_1_filter_1 = Tournament.objects.create(
            name="tournament_1_filter_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1),
            videogame=videogame_2
        )
        tournament_1_filter_2 = Tournament.objects.create(
            name="tournament_1_filter_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1)
        )

        address = reverse(self.url, kwargs={'group_id': self.group_object.id})
        address = address + "?q=" + videogame_name

        # Send the get request
        response = self.client.get(address)

        # Get the context
        ongoing_tournaments = response.context['ongoing_tournaments']

        # Check that tournament_1 and tournament_3 are in upcoming_tournaments
        self.assertIn(tournament_1, ongoing_tournaments)

        # Check that tournament_2 and tournament_4 are not in upcoming_tournaments
        self.assertNotIn(tournament_1_filter_1, ongoing_tournaments)
        self.assertNotIn(tournament_1_filter_2, ongoing_tournaments)

    def test_9_completed_tournaments(self):
        # "completed_tournaments" - start date must be in the past and end dates must be in the past
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create tournaments
        # Tournament 1: start date one hour in the past and end date one hour in the future - Shouldn't be in the
        # variable
        tournament_1 = Tournament.objects.create(
            name="tournament_1",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=1)
        )
        # Tournament 2: start date two hours in the past and end date one hour in the past - Should be in the variable
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=2),
            end_datetime=timezone.now() - timezone.timedelta(hours=1)
        )
        # Tournament 3: start date one hour in the future and end date two hours in the future - Shouldn't be in the
        # variable
        tournament_3 = Tournament.objects.create(
            name="tournament_3",
            owning_group=self.group_object,
            start_datetime=timezone.now() + timezone.timedelta(hours=1),
            end_datetime=timezone.now() + timezone.timedelta(hours=2)
        )
        # Tournament 4: start date 100 days in the past and end date 89 days in the past - Should be in the
        # variable
        tournament_4 = Tournament.objects.create(
            name="tournament_4",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=100),
            end_datetime=timezone.now() - timezone.timedelta(days=89)
        )
        # Tournament 5: start date 100 days in the past and end date 91 days in the past - should be in the
        # variable
        tournament_5 = Tournament.objects.create(
            name="tournament_5",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=100),
            end_datetime=timezone.now() - timezone.timedelta(days=91)
        )
        address = reverse(self.url, kwargs={'group_id': self.group_object.id})

        # Send the get request
        response = self.client.get(address)

        # Get the context
        completed_tournaments = response.context['completed_tournaments']

        # Check that tournament_2 and tournament_4 are in completed_tournaments
        self.assertIn(tournament_2, completed_tournaments)
        self.assertIn(tournament_4, completed_tournaments)
        self.assertIn(tournament_5, completed_tournaments)

        # Check that tournament_1, tournament_3 and tournament_5 are not in upcoming_tournaments
        self.assertNotIn(tournament_1, completed_tournaments)
        self.assertNotIn(tournament_3, completed_tournaments)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    def test_10_filter_completed_tournaments(self):
        # "completed_tournaments" - start date must be in the past and end dates must be in the past but not ended more
        # than 90 days ago
        # --- ---

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # Create a videogame to test
        videogame_name = "SC2"
        videogame_1 = Videogame.objects.create(
            name=videogame_name
        )
        videogame_2 = Videogame.objects.create(
            name="not_SC2"
        )

        # Create tournaments

        # Tournament 2: start date two hours in the past and end date one hour in the past - Should be in the variable
        tournament_2 = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=2),
            end_datetime=timezone.now() - timezone.timedelta(hours=1),
            videogame=videogame_1
        )
        tournament_2_filter = Tournament.objects.create(
            name="tournament_2",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(hours=2),
            end_datetime=timezone.now() - timezone.timedelta(hours=1),
            videogame=videogame_2
        )
        # Tournament 4: start date 100 days in the past and end date 89 days in the past - Should be in the
        # variable
        tournament_4 = Tournament.objects.create(
            name="tournament_4",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=100),
            end_datetime=timezone.now() - timezone.timedelta(days=89),
            videogame=videogame_1
        )
        tournament_4_filter = Tournament.objects.create(
            name="tournament_4",
            owning_group=self.group_object,
            start_datetime=timezone.now() - timezone.timedelta(days=100),
            end_datetime=timezone.now() - timezone.timedelta(days=89)
        )
        address = reverse(self.url, kwargs={'group_id': self.group_object.id})
        address = address + "?q=" + videogame_name

        # Send the get request
        response = self.client.get(address)

        # Get the context
        completed_tournaments = response.context['completed_tournaments']

        # Check that tournament_2 and tournament_4 are in completed_tournaments
        self.assertIn(tournament_2, completed_tournaments)
        self.assertIn(tournament_4, completed_tournaments)

        # Check that tournament_1, tournament_3 and tournament_5 are not in upcoming_tournaments
        self.assertNotIn(tournament_2_filter, completed_tournaments)
        self.assertNotIn(tournament_4_filter, completed_tournaments)


class InvitePageTests(TestCase):
    # A list of users is returned in an array "model_array" - with their invite status, in alphabetical order.
    # The possible invite statuses are:
    #   1: Existing members: "member"
    #   2: Users with a pending invite (from the group): "sent"
    #   TODO: invite from groups and requests from users are possible,
    #    is this shown in the model and how do groups approve requesting users?
    #   3: Users that have no association with the group and can be invited: "invite"
    #   4: Users that have been blocked: "blocked"
    # ---
    # Admins can invite users and are given errors or success messages where appropriate
    # ---
    # Only ADMINS of the group should be able to access this page - non-members should be presented with a 404

    # Test 1: Check that a user is redirected to the login page when not logged in
    # Test 2: Check that a user that isn't associated with the group is delivered a 404
    # Test 3: Check that a user that isn't an ADMIN of the group is delivered a 404
    # Test 4: Check that a user that has a wallet with the associated group that is not active is delivered a 404
    # Test 5: Check that an admin that has a wallet with the associated group that is not active is delivered a 404
    # Test 6: Check that an ADMIN with a wallet associated with the group, which is active is delivered the correct page
    # Test 7: Ensure "model_array" returns users in the correct order
    # Test 8: Test that a user can be successfully invited, with success message being sent
    # Test 9: Test that trying to invite a user that is 1. already a member 2. already invited or 3. declined_blocked
    # (i.e. the user is blocking invites from this group), cannot be re-invited and the admin is presented an error
    # TODO: Check that declined_blocked means this

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

        # Create admin and non-admin users
        self.admin_user = User.objects.create(username='testuser_admin')
        self.admin_user.set_password('12345')
        self.admin_user.save()

        self.non_admin_user = User.objects.create(username='testuser_nonadmin')
        self.non_admin_user.set_password('12345')
        self.non_admin_user.save()

        # create a group
        group_name = "test_group_1"
        invite_only = True
        members_can_invite = True
        header_background_colour = "496693"
        header_text_colour = "496693"
        daily_payout = 10

        self.group_object = CommunityGroup.objects.create(
            name=group_name,
            private=invite_only,
            members_can_inv=members_can_invite,
            header_background_colour=header_background_colour,
            header_text_colour=header_text_colour,
            daily_payout=daily_payout
        )

        # Create wallet between the user and group
        self.wallet_admin = Wallet.objects.create(
            profile=self.admin_user.profile,
            group=self.group_object,
            status=Wallet.active,
            admin=True
        )
        # TODO: Create a signal so that when a user creates a group they're set as the founder and an
        #  admin (Logic may already be in the view - Will groups be created from anywhere else?)

        # TODO: Add method for members to be promoted to admin by another admin - Members page?

        # TODO: Add a separate members page - Invite page should be to invite new members and see who has a pending
        #  invite (which could be revoked?) - Members page could be used to view current members, promote others,
        #  kick members etc

        self.wallet_non_admin = Wallet.objects.create(
            profile=self.non_admin_user.profile,
            group=self.group_object,
            status=Wallet.active,
            admin=False
        )

        self.url = 'groups:invitePage'

    def test_1_redirect_when_not_logged(self):

        # Assert that the user is not logged in
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id, 'page': 1})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 302 OK.
        self.assertRedirects(response, '/accounts/login/', status_code=302, target_status_code=200)

    def test_2_404_when_not_associated(self):

        # Log user in to admin account
        self.client.login(username='testuser_admin', password='12345')

        # Delete existing wallet
        self.wallet_admin.delete()

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id, 'page': 1})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 404.
        self.assertEqual(response.status_code, 404)

    def test_3_404_when_not_admin(self):

        # Log user in to admin account
        self.client.login(username='testuser_nonadmin', password='12345')

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id, 'page': 1})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 404.
        self.assertEqual(response.status_code, 404)

    def test_4_404_not_active_non_admin(self):
        # Log user in to admin account
        self.client.login(username='testuser_nonadmin', password='12345')

        # Change wallet status to deactivated
        self.wallet_non_admin.status = Wallet.deactivated
        self.wallet_non_admin.save()

        # Ensure the wallet's status was changed
        self.assertEqual(self.wallet_non_admin.status, Wallet.deactivated)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id, 'page': 1})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 404
        self.assertEqual(response.status_code, 404)

    def test_5_404_not_active_admin(self):
        # Log user in to admin account
        self.client.login(username='testuser_admin', password='12345')

        # Change wallet status to deactivated
        self.wallet_admin.status = Wallet.deactivated
        self.wallet_admin.save()

        # Ensure the wallet's status was changed
        self.assertEqual(self.wallet_admin.status, Wallet.deactivated)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id, 'page': 1})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 404
        self.assertEqual(response.status_code, 404)

    def test_6_200_when_active_admin(self):
        # Log user in to admin account
        self.client.login(username='testuser_admin', password='12345')

        # Ensure the wallet's status is active
        self.assertEqual(self.wallet_admin.status, Wallet.active)

        # Assert that the user is logged in
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        address = reverse(self.url, kwargs={'group_id': self.group_object.id, 'page': 1})

        # Send the get request
        response = self.client.get(address)

        # Check that the response is 200
        self.assertEqual(response.status_code, 200)

        # Assert that the user has NOT been redirected
        last_path = response.request['PATH_INFO']
        self.assertEqual(last_path, address)

    # def test_7(self):
    #     # Assert that the user is logged in
    #     user = auth.get_user(self.client)
    #     self.assertTrue(user.is_authenticated)
    #
    #     address = reverse(self.url, kwargs={'group_id': self.group_object.id})
    #
    #     # Send the get request
    #     response = self.client.get(address)
    #
    #     # Get the context
    #     completed_tournaments = response.context['model_array']

