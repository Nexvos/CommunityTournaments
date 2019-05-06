from django.shortcuts import render, get_object_or_404
from Profiles.models import Wallet, Profile, number_of_custom_images
from django.http import Http404
from Groups.models import CommunityGroup
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.templatetags.staticfiles import static
from .forms import *
import colorsys

# Create your views here.
def landingPage(request):
    context = {

    }
    return render(request, 'profiles/landingPage.html', context)


# TODO: Set created wallets to the default profile values for colour, image, and nickname
# TODO: Set created profiles to random values for colour and image
# TODO: Wire up match + any group pages to use the wallet values for a user
# TODO: Ensure that an image and colour are required fields for both profile and wallet
# TODO: Make sure the group page and match page etc are using nicknames etc
@login_required(redirect_field_name="")
def profile_details_default(request):
    # Set user to request.user
    user = request.user

    wallets = user.profile.profiles_wallet.all()

    if request.method == "POST":
        if 'form_name' in request.POST:
            form_name = request.POST['form_name']

            if form_name == "set_default":
                # TODO: Add a popup in html/css/javascript asking the user if they're sure
                for wallet in wallets:
                    wallet.nickname = user.profile.nickname
                    wallet.colour = user.profile.colour
                    wallet.picture_id = user.profile.picture_id
                    wallet.save()
                    # TODO: add success messages and errors
            elif form_name == "nickname":
                if "delete_nickname" in request.POST:
                    if request.POST['delete_nickname']:
                        # Set all other groups data to the default values
                        user.profile.nickname = None
                        user.profile.save()
                else:
                    form_dict = {
                        "nickname": request.POST['nickname']
                    }
                    form = NicknameForm(form_dict)
                    if form.is_valid():
                        nickname = form.cleaned_data['nickname']
                        user.profile.nickname = nickname
                        user.profile.save()
            elif form_name == "location":
                if "delete_location" in request.POST:
                    if request.POST['delete_location']:
                        # Set all other groups data to the default values
                        user.profile.location = None
                        user.profile.save()
                else:
                    form_dict = {
                        "location": request.POST['location']
                    }
                    form = LocationForm(form_dict)
                    if form.is_valid():
                        location = form.cleaned_data['location']
                        user.profile.location = location
                        user.profile.save()
            elif form_name == "picture":
                form_dict = {
                    "picture_id": request.POST['picture_id']
                }
                form = ImageForm(form_dict)
                if form.is_valid():
                    picture_id = form.cleaned_data['picture_id']
                    user.profile.picture_id = picture_id
                    user.profile.save()
            elif form_name == "colour":
                form_dict = {
                    "colour_string": request.POST['colour_string']
                }
                form = ColourForm(form_dict)
                if form.is_valid():
                    colour_string = form.cleaned_data['colour_string']
                    colour_string = colour_string[1:]
                    user.profile.colour = colour_string
                    user.profile.save()

    print(request.POST)
    image_url = user.profile.picture_url

    possible_images = []
    for x in range(number_of_custom_images):
        y = "img/profile_pictures/picture_" + str(x + 1) + ".png"
        y_url = static(y)
        possible_images.append(y_url)
    user_colour = user.profile.colour
    user_nickname = user.profile.nickname
    user_location = user.profile.location

    context = {
        "page_name": "Default",
        "wallets": wallets,
        "image_url": image_url,
        "possible_images": possible_images,
        "user_colour": user_colour,
        "user_nickname": user_nickname,
        "user_location": user_location
    }
    return render(request, "profiles/profileDetails.html", context)


# TODO: Make each group page glow with the colour of the group - In html most likely
@login_required(redirect_field_name="")
def profile_details_group(request, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    # TODO: Replace these try statements with get-object-or-404's? Can the 404 message be stated this way?
    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    if request.method == "POST":
        if 'form_name' in request.POST:
            form_name = request.POST['form_name']

            if form_name == "nickname":
                if "delete_nickname" in request.POST:
                    if request.POST['delete_nickname']:
                        # Set all other groups data to the default values
                        wallet.nickname = None
                        wallet.save()
                else:
                    form_dict = {
                        "nickname": request.POST['nickname']
                    }
                    form = NicknameForm(form_dict)
                    if form.is_valid():
                        nickname = form.cleaned_data['nickname']
                        wallet.nickname = nickname
                        wallet.save()
            elif form_name == "picture":
                form_dict = {
                    "picture_id": request.POST['picture_id']
                }
                form = ImageForm(form_dict)
                if form.is_valid():
                    picture_id = form.cleaned_data['picture_id']
                    wallet.picture_id = picture_id
                    wallet.save()
            elif form_name == "colour":
                form_dict = {
                    "colour_string": request.POST['colour_string']
                }
                form = ColourForm(form_dict)
                if form.is_valid():
                    colour_string = form.cleaned_data['colour_string']
                    colour_string = colour_string[1:]
                    wallet.colour = colour_string
                    wallet.save()
            # Re-fetch the wallet as changes may have been made
            wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)

    wallets = user.profile.profiles_wallet.all()

    image_url = wallet.picture_url

    possible_images = []
    for x in range(number_of_custom_images):
        y = "img/profile_pictures/picture_" + str(x + 1) + ".png"
        y_url = static(y)
        possible_images.append(y_url)
    user_colour = wallet.colour
    user_nickname = wallet.nickname
    user_location = user.profile.location

    context = {
        "page_name": group.name,
        "group_wallet": wallet,
        "wallets": wallets,
        "image_url": image_url,
        "possible_images": possible_images,
        "user_colour": user_colour,
        "user_nickname": user_nickname,
        "user_location": user_location
    }
    return render(request, "profiles/profileDetails.html", context)

