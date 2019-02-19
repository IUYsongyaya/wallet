#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author:ljc
@file: ask_fee_tx_poll.py
@time: 2019/01/23
"""
import datetime
from decimal import Decimal, ROUND_DOWN
import time

from web3 import Web3

from source import config
from source.common.utils import log
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.common.chain_driver.erc20_operator.const import DEFAULT_GAS_PRICE
from source.model.database import Session, GatherStatusEnum, AskFeeStatusEnum

from .base import ErcTxPoll

logger = log.get_logger(__name__, config.log_level)

Fail = -1


class AskFeeTxPoll(ErcTxPoll):
    """
    缴费交易状态检测轮寻
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
            return AskFeeStatusEnum.SUCCESS
        else:
            return AskFeeStatusEnum.FAILED
    
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
                gather_record = session.query(
                    self.coin_transfer_coll
                ).filter_by(from_address=item.to_address,
                            status=GatherStatusEnum.GATHER_NO_FEE
                            ).with_for_update().first()
                gather_record.status = GatherStatusEnum.GATHER
            else:
                item.confirmation_count = num_confirmations
                item.updated_at = now
                logger.info(f"monitor {item.txid} {num_confirmations}")
        except Exception as e:
            logger.exception(e)
    
    def poll(self):
        logger.info("----------- eth_askfee_tx_listener start -----------")
        session = Session()
        while True:
            try:
                coin_ask_fee_list = session.query(
                    self.coin_ask_fee_coll).filter_by(
                    status=AskFeeStatusEnum.WAIT_CONFIRM, coin_series="ETH").all()
                for item in coin_ask_fee_list:
                    self.monitor_tx_id(session, item)
                try:
                    session.commit()
                except Exception as e:
                    logger.error("缴费交易轮寻更新数据库失败")
                    logger.exception(e)
                    session.rollback()
            except Exception as e:
                logger.exception("缴费交易轮寻发生错误{}".format(e))
            time.sleep(10)


def main():
    poll_instance = AskFeeTxPoll()
    poll_instance.poll()
