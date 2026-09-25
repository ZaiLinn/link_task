from views.base import BaseView
from views.admin.wallet_pay import AdminWalletPayMixin
from views.admin.wallet_merchant import AdminWalletMerchantMixin
from views.admin.wallet_user import AdminWalletUserMixin


class AdminWallet(AdminWalletPayMixin, AdminWalletMerchantMixin, AdminWalletUserMixin, BaseView):
    pass
