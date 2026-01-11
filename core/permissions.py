AUTHORIZED = set()

def request_permission(user):
    # placeholder – admin approval flow
    print("Permission requested:", user.id)

def has_permission(user_id):
    return user_id in AUTHORIZED
