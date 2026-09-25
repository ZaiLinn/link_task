from views.base import BaseView
from views.admin.withdraw_list import AdminWithdrawListMixin
from views.admin.withdraw_user import AdminWithdrawUserMixin
from views.admin.withdraw_actions import AdminWithdrawActionMixin


class AdminWithdraw(AdminWithdrawListMixin, AdminWithdrawUserMixin, AdminWithdrawActionMixin, BaseView):
    pass
