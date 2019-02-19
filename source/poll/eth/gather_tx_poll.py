#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: gather_tx_poll.py
@time: 2018/09/08
"""
import datetime
from decimal import Decimal, ROUND_DOWN
import time

from web3 import Web3

from source import config
from source.common.utils import log
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.common.chain_driver.erc20_operator.const import DEFAULT_GAS_PRICE
from source.model.database import Session, GatherStatusEnum

from .base import ErcTxPoll

logger = log.get_logger(__name__, config.log_level)

Fail = -1


class GatherTXPoll(ErcTxPoll):
    """
    地址汇聚检测和缴费检测轮寻
    """
    @staticmethod
    def check_success(operator: ERC20Token, item):
        """检查是否成功
        :param operator: 区块链接口
        :param item: 交易信息
        :return:
        """
        res = operator.is_success(operator.get_transaction(item.txid))
        if res:
            return GatherStatusEnum.SUCCESS
        else:
            return GatherStatusEnum.FAILED

    def monitor_tx_id(self, session, item):
        """交易id监控
        :param session: mysql会话
        :param item: 交易信息
        :return:
        """
        now = datetime.datetime.utcnow()
        operator = self.erc_op_class(provider_endpoint=config.eth_wallet_url)
        try:
            (num_confirmations,
             gas_used) = self.get_confirm_info(operator, item)
            coin_info = session.query(
                self.coin_coll).filter_by(coin_type=item.coin_type,
                                          main_coin="ETH").first()
            confirm = config.eth_confirmations
            if coin_info:
                confirm = coin_info.withdrawalConfirmLimit or confirm
            if item.confirmation_count == num_confirmations:
                return
            if num_confirmations >= confirm:
                fee = Web3.fromWei(int(gas_used) * DEFAULT_GAS_PRICE,
                                   'ether').quantize(Decimal('0.00000001'),
                                                     rounding=ROUND_DOWN)
                status = self.check_success(operator, item)
                item.confirmation_count = num_confirmations
                item.fee = fee
                item.fee_coin = "ETH"
                item.status = status
                item.updated_at = now
                item.done_at = now
                if status.value == Fail:
                    logger.info(f'fail {item.txid}')
                    return
            
                logger.info(
                    f'monitor {item.txid} {num_confirmations} {gas_used}')
            else:
                item.confirmation_count = num_confirmations
                item.updated_at = now
                logger.info(f"monitor {item.txid} {num_confirmations}")
        except Exception as e:
            logger.exception(e)

    def poll(self):
        logger.info("----------- eth_gather_tx_listener start -----------")
        session = Session()
        while True:
            try:
                transfer_list = session.query(
                    self.coin_transfer_coll).filter_by(
                    status=GatherStatusEnum.GATHERING,
                    coin_series="ETH").all()
                for item in transfer_list:
                    self.monitor_tx_id(session, item)
                try:
                    session.commit()
                except Exception as e:
                    logger.error("汇聚交易数据库操作时发生错误")
                    logger.exception(e)
                    session.rollback()
            except Exception as e:
                logger.exception("汇聚交易轮寻发生错误{}".format(e))
            time.sleep(10)


def main():
    poll_instance = GatherTXPoll()
    poll_instance.poll()
