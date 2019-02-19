#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: charge_withdraw_poll.py
@time: 2018/10/31
"""
import time
import datetime as dt
from decimal import Decimal, ROUND_DOWN

from web3 import Web3
from eth_utils import to_checksum_address


from source import config
from source.model.database import (TbStatusEnum, RechargeStatusEnum,
                                   AskFeeStatusEnum,
                                   GatherStatusEnum, InformEnum, Session)
from source.common.chain_driver.erc20_operator.const import DEFAULT_GAS_PRICE
from source.common.utils.log import get_logger
from source.poll.rpc_call import confirm, recharge

from .base import BaseEtcTxPoll


# logging
logger = get_logger(__name__, config.log_level)

SUCCESS = 1

FAIL = -1


class ChargeWithdrawPoll(BaseEtcTxPoll):
    @staticmethod
    def send_recharge_notify(session, recharge_record):
        try:
            recharge_record_ = vars(recharge_record) \
                if recharge_record else dict()
            recharge_address = recharge_record_.get('to_address', '')
            recharge_amount = recharge_record_.get('amount', 0)
            transaction_id = recharge_record_.get('txid', '')
            coin_type = recharge_record_.get('coin_type', '')
            from_address = recharge_record_.get('from_address', '')
            confirmations = recharge_record_.get("confirmation_count", 0)
            status = recharge_record_.get("status",
                                          RechargeStatusEnum.RECHARGE)
            response = recharge(address=recharge_address,
                                from_address=from_address,
                                amount=recharge_amount,
                                txid=transaction_id,
                                coin_type=coin_type,
                                confirmations=confirmations,
                                status=status.value)
            if transaction_id and response == transaction_id:
                if status.value in [SUCCESS, FAIL]:
                    try:
                        recharge_record.informed = InformEnum.YES
                        session.commit()
                    except Exception as e:
                        logger.exception("修改充币通知状态失败{}".format(e))
                        session.rollback()
                    else:
                        logger.info('已成功修改充币状态')
                logger.info('已成功通知充币交易{}'.format(response))
            else:
                logger.error('java后台没有确认{}提币通知{}'.format(coin_type,
                                                         transaction_id))
        except Exception as e:
            logger.exception(e)
    
    @staticmethod
    def send_withdraw_notify(session, withdraw_record):
        try:
            if not withdraw_record:
                return
            withdraw_record_ = vars(withdraw_record) \
                if withdraw_record else dict()
            transaction_id = withdraw_record_.get("txid", "")
            confirmation = withdraw_record_.get("confirmation_count", 0)
            status = withdraw_record.get("status", TbStatusEnum.TRANSFER)
            coin_type = withdraw_record.get("coin_type", "")
            response = confirm(
                txid=transaction_id,
                confirmations=confirmation,
                status=status)
            if transaction_id and response == transaction_id:
                logger.info('已成功通知充币交易{}'.format(response))
                if status.value in [SUCCESS, FAIL]:
                    try:
                        withdraw_record.informed = InformEnum.YES
                        session.commit()
                    except Exception as e:
                        logger.exception("修改提币通知状态失败{}".format(e))
                        session.rollback()
                    else:
                        logger.info('已成功修改充币通知状态')
            else:
                logger.error('java后台没有确认{}提币通知{}'.format(coin_type,
                                                         transaction_id))
        except Exception as e:
            logger.exception(e)
    
    def create_gather(self, session, coin_type, from_address,
                      to_address, amount, status):
        """创建子钱包汇聚"""
        try:
            now = dt.datetime.utcnow()
            from_address = to_checksum_address(from_address)
            to_address = to_checksum_address(to_address)
            gather_data = dict()
            gather_data["amount"] = amount
            gather_data["status"] = status
            gather_data["create_at"] = now
            gather_data["updated_at"] = now
            gather_data["from_address"] = from_address
            gather_data["to_address"] = to_address
            gather_data["coin_type"] = coin_type
            gather_data["coin_series"] = self.coin_category
            coll = self.coin_transfer_coll(**gather_data)
            session.add(coll)
            session.commit()
            logger.info(
                f'create child transfer: {from_address} {to_address} {amount}')
        except Exception as e:
            logger.exception("创建{}汇聚失败{}".format(from_address, e))
            session.rollback()
            raise
    
    def check_gather(self, session, item, monitor_type):
        """检查是否汇聚"""
        if monitor_type == 'withdraw':
            return
        operator = self.erc_op_class(ipc_path=config.etc_ipc_path,
                                     address=item.to_address)
        is_ask_fee = session.query(
            self.coin_ask_fee_coll).filter(
            self.coin_ask_fee_coll.to_address == item.to_address,
            self.coin_ask_fee_coll.status.in_((AskFeeStatusEnum.ASKING,
                                               AskFeeStatusEnum.WAIT_CONFIRM))
        ).first()
        if is_ask_fee:
            return
        
        is_withdraw = session.query(
            self.coin_transfer_coll).filter(
            self.coin_transfer_coll.from_address == item.to_address,
            self.coin_transfer_coll.status.in_((GatherStatusEnum.GATHER_NO_FEE,
                                                GatherStatusEnum.GATHER,
                                                GatherStatusEnum.GATHERING))
        ).first()
        if is_withdraw:
            return
    
        master_operator = self.erc_op_class(ipc_path=config.etc_ipc_path,
                                            address=to_checksum_address(
                                                config.etc_tb_address)
                                            )
        
        hw_transhold = float(config.etc_cz_max)
        cw_transhold = float(config.etc_tb_max)
        # ETC处理
        child_balance = float(operator.get_ether_balance())
        if child_balance + float(config.etc_fee_min) < hw_transhold:
            return
        
        wallet_balance = float(master_operator.get_ether_balance())
        wallet_address = config.etc_tb_address if (
                wallet_balance < cw_transhold) else \
            config.etc_cw_address
        self.create_gather(session,
                           item.coin_type,
                           item.to_address,
                           wallet_address,
                           child_balance - float(config.etc_fee_min),
                           GatherStatusEnum.GATHER)

    @staticmethod
    def check_success(operator, item, monitor_type):
        """检查交易是否成功
        :param operator: 区块链驱动
        :param item: 交易信息
        :param monitor_type: 交易类型
        :return:
        """
        res = operator.is_success(operator.get_transaction(item.txid))
        if res:
            if monitor_type == "recharge":
                return RechargeStatusEnum.SUCCESS
            else:
                return TbStatusEnum.SUCCESS
        else:
            if monitor_type == "recharge":
                return RechargeStatusEnum.FAILED
            else:
                return TbStatusEnum.FAILED
        
    def monitor_tx_id(self, session, item, monitor_type):
        """交易id监控"""
        now = dt.datetime.utcnow()
        operator = self.erc_op_class(ipc_path=config.etc_ipc_path)
        try:
            (num_confirmations,
             gas_used) = self.get_confirm_info(operator, item)
            coin_info = session.query(
                self.coin_coll).filter_by(coin_type=item.coin_type).first()
            confirm_limit = config.etc_confirmations
            if coin_info:
                confirm_limit = coin_info.withdrawalConfirmLimit \
                    if monitor_type == 'withdraw' else \
                    coin_info.chargeConfirmLimit
            
            if num_confirmations == item.confirmation_count:
                return
            item.confirmation_count = num_confirmations
            item.updated_at = now
            if num_confirmations >= confirm_limit:
                fee = float(
                    Web3.fromWei(int(gas_used) * DEFAULT_GAS_PRICE,
                                 'ether').quantize(Decimal('0.00000001'),
                                                   rounding=ROUND_DOWN))
                # 检查是否成功
                status = self.check_success(operator, item, monitor_type)
                item.status = status
                item.fee = fee
                item.fee_coin = self.coin_category
                
            try:
                session.commit()
            except Exception as e:
                logger.exception("修改充提币记录发生错误{}".format(e))
                session.rollback()
            else:
                self.check_gather(session, item, monitor_type)
                if monitor_type == 'recharge':
                    self.send_recharge_notify(session, item)
                if monitor_type == 'withdraw':
                    self.send_withdraw_notify(session, item)
                if item.status.value == FAIL:
                    logger.info(f"{monitor_type}fail {item.txid}")
                    return
                # 成功
                logger.info(
                    f'monitor {item.txid} {num_confirmations} {gas_used}')
        except Exception as e:
            logger.exception(e)

    def poll(self):
        logger.info('------ etc charge withdraw transaction start ---------')
        session = Session()
        while True:
            try:
                withdraw_list = session.query(
                    self.withdraw_coll).filter_by(
                    informed=InformEnum.NO,
                    coin_series=self.coin_category).all()
                recharge_list = session.query(
                    self.coin_recharge_coll).filter_by(
                    informed=InformEnum.NO,
                    coin_series=self.coin_category).all()
                for item in recharge_list:
                    self.monitor_tx_id(session, item,
                                       'recharge')
                for item in withdraw_list:
                    self.monitor_tx_id(session, item,
                                       'withdraw')
            except Exception as e:
                logger.exception("充提币交易轮寻发生错误{}".format(e))
            time.sleep(10)


def main():
    poll_instance = ChargeWithdrawPoll()
    poll_instance.poll()
