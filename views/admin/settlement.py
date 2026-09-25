from views.base import BaseView
from views.admin.settlement_list import AdminSettlementListMixin
from views.admin.settlement_detail import AdminSettlementDetailMixin
from views.admin.settlement_actions import AdminSettlementActionMixin


class AdminSettlement(AdminSettlementListMixin, AdminSettlementDetailMixin, AdminSettlementActionMixin, BaseView):
    pass
