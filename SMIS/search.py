from cv.models import CV
from user.models import User, PersonalInfo


def find_image_by_CV_id(cv_id):
    user_obj = User.objects.get(cv__id=cv_id)
    if user_obj:
        return user_obj
    else:
        return None
