# 路由
from core.router import Router
from views.admin.index import Admin
from views.admin.settlement import AdminSettlement
from views.admin.user import User
from views.admin.wallet import AdminWallet
from views.admin.withdraw import AdminWithdraw
from views.client.index import Index
from views.client.merchant_wallet import MerchantWallet
from views.client.my_settlement import MySettlement
from views.client.my_task import MyTask
from views.client.my_wallet import MyWallet
from views.client.my_withdraw import MyWithdraw
from views.client.publish_index import PublishIndex
from views.client.publish_list import PublishList
from views.client.publish_post import PublishPostTask
from views.client.publish_settlement import Settlement
from views.client.task_index import TaskIndex


router = Router()
router.add_route('r/首页', Index, 'index')
router.add_route('r/判断角色', Index, 'ifRole')
router.add_route('r/删除当前消息', Index, 'backReview')

router.add_route('r/任务首页', TaskIndex, 'index')
router.add_route('r/任务信息', TaskIndex, 'task_info')
router.add_route('r/任务输入', TaskIndex, 'inputBot')
router.add_route('r/任务领取', TaskIndex, 'task_receive')


router.add_route('r/任务用户中心', MyTask, 'index')
router.add_route('r/任务我的任务', MyTask, 'my_task')
router.add_route('r/任务生成推广消息', MyTask, 'my_Assemble_message')
router.add_route('r/任务我的任务信息', MyTask, 'my_task_info')
router.add_route('r/任务我的任务日志', MyTask, 'my_task_log')
router.add_route('r/任务取消任务', MyTask, 'my_task_cancel')
router.add_route('r/发送群设置', MyTask, 'sendGroupSet')
router.add_route('r/发送群状态', MyTask, 'sendGroupstate')


router.add_route('r/任务结算管理', MySettlement, 'index')
router.add_route('r/任务结算详情', MySettlement, 'settlementInfo')
router.add_route('r/任务结算申诉', MySettlement, 'appeal')



router.add_route('r/任务提现', MyWithdraw, 'index')
router.add_route('r/任务提现详情', MyWithdraw, 'withdrawInfo')
router.add_route('r/任务资金钱包', MyWallet, 'index')
router.add_route('r/任务资金订单详情', MyWallet, 'order_info')
# router.add_route('r/任务提现申请', MyWithdraw, 'withdrawApply')

# ======商家相关
router.add_route('r/商家首页', PublishIndex, 'index')
router.add_route('r/商家发布', PublishPostTask, 'postTask')
router.add_route('r/商家发布输入', PublishPostTask, 'inputBot')
router.add_route('r/商家发布表单', PublishPostTask, 'task_release_form')
router.add_route('r/商家发布选择群', PublishPostTask, 'opt_group')
router.add_route('r/商家发布关联群', PublishPostTask, 'be_group_task')
router.add_route('r/商家发布取消', PublishPostTask, 'task_release_cancel')
router.add_route('r/商家发布提交', PublishPostTask, 'submit_task')
router.add_route('r/商家发布规则', PublishPostTask, 'detect_rule')
router.add_route('r/商家发布私密审核', PublishPostTask, 'set_task_state')


router.add_route('r/商家任务列表', PublishList, 'index')
router.add_route('r/商家任务信息', PublishList, 'task_info')
router.add_route('r/商家任务规则', PublishList, 'detect_rule')
router.add_route('r/商家任务输入', PublishList, 'inputBot')
router.add_route('r/商家任务选择群', PublishList, 'opt_group')
router.add_route('r/商家任务关联群', PublishList, 'be_group_task')
router.add_route('r/商家任务日志', PublishList, 'task_log')
router.add_route('r/商家发布私密审核', PublishList, 'set_task_state')
router.add_route('r/商家任务上线', PublishList, 'online_task')
router.add_route('r/商家任务下线', PublishList, 'offline_task')


router.add_route('r/商家结算管理', Settlement, 'index')
router.add_route('r/商家结算详细', Settlement, 'settlementInfo')
router.add_route('r/商家结算确认', Settlement, 'confirm')
router.add_route('r/商家结算拒绝', Settlement, 'reject')
router.add_route('r/商家结算输入', Settlement, 'inputBot')
# 钱包管理
router.add_route('r/商家钱包', MerchantWallet, 'index')
router.add_route('r/商家钱包输入', MerchantWallet, 'inputBot')
router.add_route('r/商家钱包订单详情', MerchantWallet, 'order_info')
router.add_route('r/商家钱包充值类型', MerchantWallet, 'pay_index')



# 管理员功能路由
# 机器人配置
router.add_route('a/管理首页', Admin, 'index')
router.add_route('a/初始化菜单', Admin, 'initialization')
router.add_route('a/机器人配置', Admin, 'config')
router.add_route('a/修改配置', Admin, 'modifBot')
router.add_route('a/审核拒绝词', Admin, 'reviewRejectionWords')
router.add_route('a/增审核拒绝词', Admin, 'delReviewRejectionWords')
router.add_route('a/删审核拒绝词', Admin, 'delReviewRejectionWords')

# 结算管理
router.add_route('a/管理结算首页', AdminSettlement, 'index')
router.add_route('a/管理结算详情', AdminSettlement, 'settlementInfo')
router.add_route('a/管理结算确认', AdminSettlement, 'confirm')
router.add_route('a/管理偷结算确认', AdminSettlement, 'tou_confirm')
router.add_route('a/管理结算拒绝', AdminSettlement, 'reject')

# 提现管理
router.add_route('a/管理提现首页', AdminWithdraw, 'index')
router.add_route('a/管理提现详情', AdminWithdraw, 'withdrawInfo')
router.add_route('a/管理提现用户详情', AdminWithdraw, 'userInfo')
router.add_route('a/管理提现禁用户', AdminWithdraw, 'banUser')
router.add_route('a/提现用户流水', AdminWithdraw, 'capitalFlow')
router.add_route('a/提现结算历史', AdminWithdraw, 'settlementHistory')
router.add_route('a/提现任务历史', AdminWithdraw, 'taskHistory')
router.add_route('a/提现同意', AdminWithdraw, 'consentWithdraw')
router.add_route('a/提现拒绝', AdminWithdraw, 'taskHistory')
router.add_route('a/管理提现输入', AdminWithdraw, 'inputBot')

# 资金流水
router.add_route('a/资金充值流水', AdminWallet, 'index')
router.add_route('a/资金充值详细', AdminWallet, 'pay_info')
router.add_route('a/资金商家流水', AdminWallet, 'merchant')
router.add_route('a/资金商家详细', AdminWallet, 'merchant_info')
router.add_route('a/资金用户流水', AdminWallet, 'user')
router.add_route('a/资金用户详细', AdminWallet, 'user_info')


router.add_route('a/用户管理', User, 'getUser')#数据抓取
router.add_route('a/用户输入', User, 'inputBot')
router.add_route('a/用户详情', User, 'userInfo')#数据抓取
router.add_route('a/设置管理员', User, 'setAdmin')
router.add_route('a/禁用户', User, 'banUser')
router.add_route('a/返回', User, 'backReview')
router.add_route('a/删除当前消息', User, 'backReview')
router.add_route('a/用户校验流水', User, 'checkCalculation')

#
# router.add_route('a/Bot黑名单', BotBlacklist, 'index')
# router.add_route('a/Bot输入', BotBlacklist, 'botInput')
# router.add_route('a/删Bot黑名单', BotBlacklist, 'delBotBlacklist')
