# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-11-10 上午10:28

from datetime import datetime

from source.poll import rpc_call
from source.common.utils.log import get_logger
from source.model.database import (
    TbRecord, TbStatusEnum, InformEnum, Recharge, RechargeStatusEnum,
    AccountBalance
)


logger = get_logger('update-withdraw-status')


class Base(object):
    __type__ = ('withdraw', 'recharge')

    def __init__(self, item, confirmations, _type):
        assert _type in Base.__type__
        self.item = item
        self.confirmations = confirmations
        self.type = _type

    @property
    def success(self):
        if self.type == 'withdraw':
            return TbStatusEnum.SUCCESS
        else:
            return RechargeStatusEnum.SUCCESS

    def set_success(self):
        if self.type == 'recharge':
            self.item['status'] = RechargeStatusEnum.SUCCESS
        else:
            self.item['status'] = TbStatusEnum.SUCCESS

    def save_item(self):
        if self.type == 'recharge':
            Recharge.replace_one({'id': self.item['id']}, self.item)
        else:
            TbRecord.replace_one({'id': self.item['id']}, self.item)

    def update_confirmations(self, confirmations):
        if self.item['confirmation_count'] != confirmations:
            self.item['confirmation_count'] = confirmations
            if confirmations >= self.confirmations:
                self.set_success()
                status = self.item['status']
            else:
                status = 0
            try:
                rv = self.notify(self.item['txid'], confirmations, status)
                if rv == self.item['txid'] and status == self.success:
                    self.item['informed'] = InformEnum.YES
            except Exception as e:
                logger.error(f'调用confirm接口失败.{self.item}')
                logger.exception(e)
            try:
                self.item['updated_at'] = datetime.utcnow()
                self.save_item()
            except Exception as e:
                logger.error(f'写入数据库失败{self.item}')
                logger.exception(e)

    @classmethod
    def update_informed(cls, coin_type, _type):
        assert _type in cls.__type__
        if _type == 'withdraw':
            success_status = TbStatusEnum.SUCCESS
            inform_list = TbRecord.find({
                'status': success_status, 'coin_type': coin_type,
                'informed': InformEnum.NO
            })
        else:
            success_status = RechargeStatusEnum.SUCCESS
            inform_list = Recharge.find({
                'status': success_status, 'coin_type': coin_type,
                'informed': InformEnum.NO
            })
        for each in inform_list:
            tx_id = each['txid']
            try:
                if _type == 'withdraw':
                    rv = rpc_call.confirm(tx_id, each['confirmation_count'],
                                          success_status, coin_type)
                elif _type == 'recharge':
                    to_address = each['to_address']
                    from_address = each['from_address']
                    amount = each['amount']
                    destination_tag = each['destination_tag']
                    confirmations = each['confirmation_count']
                    rv = rpc_call.recharge(to_address, from_address, amount,
                                           tx_id, coin_type, confirmations,
                                           success_status, destination_tag)
                if rv == tx_id:
                    each['informed'] = InformEnum.YES
            except Exception as e:
                logger.error(f'调用confirm接口失败.{self.item}')
                logger.exception(e)
            try:
                TbRecord.replace_one({'id': each['id']}, each)
            except Exception as e:
                logger.error(f'写入数据库失败{each}')
                logger.exception(e)

    def notify(self, tx_id, confirmations, status=0):
        """
        发送通知到java服务器
        :param tx_id: 交易哈希
        :param confirmations: 确认数
        :param status: 状态，如果确认数还不够，此参数不传，如果确认数足够则发送TbStatusEnum.SUCCESS
        :return:
        """
        coin_type = self.item['coin_type']
        if self.type == 'withdraw':
            return rpc_call.confirm(tx_id, confirmations, status, coin_type)
        else:
            to_address = self.item['to_address']
            from_address = self.item['from_address']
            amount = self.item['amount']
            destination_tag = self.item['destination_tag']
            return rpc_call.recharge(to_address, from_address, amount, tx_id,
                                     coin_type, confirmations, status,
                                     destination_tag)


class CheckRecharge(Base):
    def __init__(self, item, confirmations):
        super().__init__(item, confirmations, 'recharge')


class CheckWithdraw(Base):
    def __init__(self, item, confirmations):
        super().__init__(item, confirmations, 'withdraw')


def get_tb_balance(coin_type):
    if not coin_type.endswith('_TX'):
        coin_type = coin_type + '_TX'
    rv = AccountBalance.find_one({'coin_type': coin_type})
    return rv.balance if rv else 0
