from views.base import BaseView
from views.admin.user_list import AdminUserListMixin
from views.admin.user_actions import AdminUserActionMixin
from views.admin.user_wallet import AdminUserWalletMixin


class User(AdminUserListMixin, AdminUserActionMixin, AdminUserWalletMixin, BaseView):
    pass
