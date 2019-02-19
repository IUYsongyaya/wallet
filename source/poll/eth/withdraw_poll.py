#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: withdraw_poll.py
@time: 2018/09/07
"""
import datetime
from decimal import Decimal, ROUND_DOWN
import time

from web3 import Web3

from source import config
from source.common.utils import log
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.common.chain_driver.erc20_operator.const import DEFAULT_GAS_PRICE
from source.model.database import (Session, InformEnum, TbStatusEnum)
from source.poll.rpc_call import confirm

from .base import ErcTxPoll


logger = log.get_logger(__name__, config.log_level)


SUCCESS = 1

FAIL = -1


class WithdrawPoll(ErcTxPoll):
    """
    提币轮寻类
    """
    
    @staticmethod
    def send_withdraw_notify(withdraw_record):
        try:
            withdraw_record_ = vars(withdraw_record)\
                if withdraw_record else dict()
            transaction_id = withdraw_record_.get('txid', '')
            confirmation = withdraw_record_.get('confirmation_count', 0)
            status = withdraw_record_.get('status', TbStatusEnum.TRANSFER)
            coin_type = withdraw_record_.get('coin_type', '')
            response = confirm(
                txid=transaction_id,
                confirmations=confirmation,
                status=status.value)
            if status.value in [SUCCESS, FAIL]:
                if transaction_id and response.get("result",
                                                   "") == transaction_id:
                    withdraw_record.informed = InformEnum.YES
                else:
                    logger.error('java后台没有确认{}提币通知{}'.format(coin_type, transaction_id))
        except Exception as e:
            logger.exception("java接口调用失败{}".format(e))

    @staticmethod
    def check_success(operator: ERC20Token, item):
        """检查交易是否成功
        :param operator: 区块链驱动
        :param item: 交易信息
        :return:
        """
        res = operator.is_success(operator.get_transaction(item.txid))
        if res:
            return TbStatusEnum.SUCCESS
        else:
            return TbStatusEnum.FAILED

    def monitor_tx_id(self, session, item, monitor_type: str):
        """交易id监控
        :param session: 数据库链接
        :param item: 从区块上获取的交易信息
        :param monitor_type: 监控类型(提币还冲币)
        :return:
        """
        now = datetime.datetime.utcnow()
        operator = self.erc_op_class(provider_endpoint=config.eth_wallet_url)
        try:
    
            (num_confirmations,
             gas_used) = self.get_confirm_info(operator, item)
            coin_info = session.query(
                self.coin_coll).filter_by(**{'coin_type': item.coin_type,
                                             'main_coin': 'ETH'}).first()
            confirm_limit = coin_info.withdrawalConfirmLimit if coin_info else config.eth_confirmations
                
            if item.confirmation_count and num_confirmations == item.confirmation_count:
                return
            
            item.confirmation_count = num_confirmations
            item.updated_at = now
            if num_confirmations >= confirm_limit:
                fee = Web3.fromWei(int(gas_used) * DEFAULT_GAS_PRICE,
                                   'ether').quantize(Decimal('0.00000001'),
                                                     rounding=ROUND_DOWN)
                # 检查是否成功
                status = self.check_success(operator, item)
                item.status = status
                item.fee = fee
                item.fee_coin = 'ETH'
            self.send_withdraw_notify(item)
            if item.status.value == FAIL:
                logger.info(f'fail {item.txid}')
                return
            # 成功
            logger.info(
                f'monitor {item.txid} {num_confirmations} {gas_used}')
        except Exception as e:
            logger.exception("提币交易检测失败{}".format(e))

    def poll(self):
        logger.info("----------- erc_charge_withdraw start -----------")
        session = Session()
        while True:
            try:
                withdraw_list = session.query(self.withdraw_coll).filter_by(
                    **{'coin_series': 'ETH', 'informed': InformEnum.NO}).all()
                for item in withdraw_list:
                    self.monitor_tx_id(session, item, 'withdraw')
                try:
                    session.commit()
                except Exception as e:
                    logger.error("提币轮寻数据库操作失败")
                    logger.exception(e)
                    session.rollback()
                else:
                    logger.info("提币轮寻更新成功")
            except Exception as e:
                logger.exception("提币交易确认轮寻发生错误{}".format(e))
            time.sleep(10)


def main():
    poll_instance = WithdrawPoll()
    poll_instance.poll()
