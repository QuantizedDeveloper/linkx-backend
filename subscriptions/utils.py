from django.utils import timezone


def freelancer_has_access(profile):
    if profile.status == "trial_active":
        return True

    if hasattr(profile.user, "subscription"):
        sub = profile.user.subscription
        return sub.active and sub.expires_at > timezone.now()

    return False
    