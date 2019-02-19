#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: gather_tx_poll.py
@time: 2018/10/31
"""
import time
import datetime as dt
from decimal import Decimal, ROUND_DOWN

from web3 import Web3

from source import config
from source.model.database import GatherStatusEnum, Session
from source.common.chain_driver.erc20_operator.const import DEFAULT_GAS_PRICE
from source.common.utils.log import get_logger

from .base import BaseEtcTxPoll

# logging
logger = get_logger(__name__, config.log_level)


class GatherTxPoll(BaseEtcTxPoll):
    @staticmethod
    def check_success(operator, item):
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
        """交易id监控"""
        now = dt.datetime.utcnow()
        operator = self.erc_op_class(ipc_path=config.etc_ipc_path)
        try:
            (num_confirmations,
             gas_used) = self.get_confirm_info(operator, item)
            
            coin_info = session.query(self.coin_coll
                                      ).filter_by(coin_type=item.coin_type
                                                  ).first()
            confirm = config.etc_confirmations
            if coin_info:
                confirm = coin_info.withdrawalConfirmLimit \
                          or config.etc_confirmations
            if item.confirmation_count == num_confirmations:
                return
            if num_confirmations >= confirm:
                fee = float(Web3.fromWei(int(gas_used) * DEFAULT_GAS_PRICE,
                                         'ether'
                                         ).quantize(Decimal('0.00000001'),
                                                    rounding=ROUND_DOWN))
                status = self.check_success(operator, item)
                item.status = status
                item.confirmation_count = num_confirmations
                item.fee = fee
                item.fee_coin = self.coin_category
                item.updated_at = now
                item.done_at = now
                if status == GatherStatusEnum.FAILED:
                    logger.info(f'fail {item.txid}')
            else:
                item.confirmation_count = num_confirmations
                item.updated_at = now
                logger.info(f"monitor {item.txid} {num_confirmations}")
            try:
                session.commit()
            except Exception as e:
                logger.exception("汇聚{}修改状态发生错误{}".format(item.txid,
                                                         e))
                session.rollback()
        except Exception as e:
            logger.exception(e)
    
    def poll(self):
        logger.info("--------- etc gather_transaction listen start ---------")
        session = Session()
        while True:
            try:
                transfer_list = session.query(
                    self.coin_transfer_coll).filter_by(
                    status=GatherStatusEnum.GATHERING,
                    coin_series=self.coin_category).all()
                for item in transfer_list:
                    self.monitor_tx_id(session, item)
            except Exception as e:
                logger.exception(e)
            time.sleep(10)


def main():
    poll_instance = GatherTxPoll()
    poll_instance.poll()
