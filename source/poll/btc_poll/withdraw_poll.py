#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
检测提币是否成功
@author:ljc
@file: withdraw_poll.py
@time: 2018/10/25
"""
import time
import datetime

from source import config
from source.common.utils import log
from source.model.database import TbStatusEnum, Session, InformEnum
from source.poll.rpc_call import confirm

from .base import BtcPollBase


logger = log.get_logger(__name__, config.log_level)


class WithdrawPoll(BtcPollBase):
    def send_withdraw_notify(self, session, withdraw_record_id):
        try:
            withdraw_record = session.query(
                self.coin_withdraw_col).filter_by(
                id=withdraw_record_id).first()
            transaction_id = withdraw_record.txid
            confirmation = withdraw_record.confirmation_count
            status = withdraw_record.status
            response = confirm(
                txid=transaction_id,
                confirmations=confirmation,
                status=status.value)
            if transaction_id and response == transaction_id:
                logger.info('已成功通知充币交易{}'.format(response))
                if status.value in [TbStatusEnum.SUCCESS.value,
                                    TbStatusEnum.FAILED.value]:
                    try:
                        withdraw_record.informed = InformEnum.YES
                        session.commit()
                    except Exception as e:
                        logger.exception("更新提币通知状态失败{}".format(e))
                        session.rollback()
                    else:
                        logger.info('已成功更新充币状态{}'.format(response))
            else:
                logger.error('java后台没有确认{}提币通知{}'.format(
                    self.coin_category, transaction_id))
        except Exception as e:
            logger.exception("java接口调用失败{}".format(e))
    
    def check_withdraw(self, session):
        """提币交易确认检查"""
        withdraw_record = session.query(self.coin_withdraw_col
                                        ).filter_by(
            coin_type=self.coin_category, informed=InformEnum.NO).first()
        if not withdraw_record:
            return
        backend = self.driver
        coin_config = session.query(
            self.coin_setting_col).filter_by(
            coin_type=self.coin_category).first()
        coin_obj = vars(coin_config) if coin_config else dict()
        confirm_cnt_touchstone = coin_obj.get('withdrawalConfirmLimit'
                                              ) \
            if coin_obj else getattr(config,
                                     self.coin_category.lower() +
                                     "_confirms")
        tx_id = withdraw_record.txid
        if not tx_id:
            logger.error("提币记录中没有交易id")
            return
        tx_dict = backend.get_transaction(tx_id)
        confirm_cnt = tx_dict.get('confirmations', 0)
        if withdraw_record.confirmation_count != confirm_cnt:
            withdraw_record.confirmation_count = confirm_cnt
            withdraw_record.updated_at = datetime.datetime.utcnow()
            if confirm_cnt >= confirm_cnt_touchstone:
                withdraw_record.fee = abs(float(tx_dict.get('fee', 0)))
                withdraw_record.fee_coin = self.coin_category
                withdraw_record.status = TbStatusEnum.SUCCESS
                if tx_dict.get('abandoned', False):
                    withdraw_record.status = TbStatusEnum.FAILED
            record_id = withdraw_record.id
            try:
                session.commit()
            except Exception as e:
                logger.exception("提币发生异常{}, 交易id为{}".format(e,
                                                            tx_id))
                session.rollback()
            else:
                self.send_withdraw_notify(session, record_id)
    
    def poll(self):
        logger.info("----------- withdraw check start -----------")
        session = Session()
        while True:
            try:
                self.check_withdraw(session)
            except Exception as e:
                logger.exception("提币轮寻发生错误{}".format(e))
                time.sleep(2)


def main():
    poll_instance = WithdrawPoll()
    poll_instance.poll()
