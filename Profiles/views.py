from django.shortcuts import render, get_object_or_404
from Profiles.models import Wallet, Profile, number_of_custom_images
from django.http import Http404
from Groups.models import CommunityGroup
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.templatetags.staticfiles import static

# Create your views here.
def landingPage(request):
    context = {

    }
    return render(request, 'profiles/landingPage.html', context)


@login_required(redirect_field_name="")
def profile_details_default(request):
    # Set user to request.user
    user = request.user

    wallets = user.profile.profiles_wallet.all()

    image = "img/profile_pictures/picture_" + str(user.profile.picture_id) + ".png"
    image_url = static(image)
    possible_images = []
    for x in range(number_of_custom_images):
        y = "img/profile_pictures/picture_" + str(x+1) + ".png"
        y_url = static(y)
        possible_images.append(y_url)
    print(request.POST)
    user_colour = user.profile.colour
    user_nickname = user.profile.nickname
    location = user.profile.location
    context = {
        "wallets": wallets,
        "image_url": image_url,
        "possible_images": possible_images,
        "user_colour": user_colour,
        "user_nickname": user_nickname,
        "location": location
    }
    return render(request, "profiles/profileDetails.html", context)


@login_required(redirect_field_name="")
def profile_details_group(request, group_id):
    # Set user to request.user
    user = request.user

    group = get_object_or_404(CommunityGroup, id=group_id)

    try:
        wallet = Wallet.objects.get(group=group, profile=user.profile, status=Wallet.active)
    except Wallet.DoesNotExist:
        raise Http404('You are not a member of this group.')

    wallets = user.profile.profiles_wallet.all()

    image = "img/profile_pictures/picture_" + str(wallet.picture_id) + ".png"

    image_url = static(image)
    context = {
        "group": group,
        'wallet': wallet,
        "wallets": wallets,
        "image_url": image_url
    }
    return render(request, "profiles/profileDetails.html", context)

