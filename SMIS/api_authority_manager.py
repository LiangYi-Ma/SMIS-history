"""
@file_intro:权限管理
@creation_date:
@update_date:
@author:Yaqi Meng
"""


class AuthorityManager:
    def __init__(self, user_obj):
        self.user = user_obj

    def is_staff(self):
        return self.user.is_staff or self.user.is_superuser

    def get_role(self):
        if self.user.is_superuser:
            return "superuser"
        elif self.user.is_staff:
            return "staff"
        else:
            return "general user"
