#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
汇聚交易确认监控
@author:ljc
@file: gather_tx_poll.py
@time: 2018/10/24
"""
import time
import datetime

from source import config
from source.model.database import GatherStatusEnum, Session
from source.common.utils.log import get_logger

from .base import BtcPollBase

logger = get_logger(__name__, config.log_level)


class GatherTxPoll(BtcPollBase):
    def check_gather_tx(self, session):
        backend = self.driver
        for i in session.query(self.coin_transfer_col
                               ).filter_by(coin_type=self.coin_category,
                                           status=GatherStatusEnum.GATHERING
                                           ).all():
            logger.debug('check %s' % i)
            confirm_cnt_touchstone = getattr(config,
                                             self.coin_category.lower() +
                                             "_confirms")
        
            tx_id = i.txid
            if not tx_id:
                continue
        
            tx_dict = backend.get_transaction(tx_id)
            confirm_cnt = tx_dict.get('confirmations', 0)
        
            i.confirmation_count = confirm_cnt
            if confirm_cnt >= confirm_cnt_touchstone:
                i.status = GatherStatusEnum.SUCCESS
                logger.debug('check ok transfer %s ' % i)
        
            i.updated_at = datetime.datetime.utcnow()
            i.fee = abs(float(tx_dict.get('fee', 0)))
            i.fee_coin = self.coin_category
        
            if tx_dict.get('abandoned', False):
                i.status = GatherStatusEnum.FAILED
            try:
                session.commit()
            except Exception as e:
                logger.exception("更改汇聚信息时发生错误{}".format(e))
                session.rollback()
    
    def poll(self):
        logger.info("----------- gather tx start -----------")
        session = Session()
        while True:
            try:
                self.check_gather_tx(session)
                time.sleep(5)
            except Exception as e:
                logger.exception(e)
                time.sleep(60)


def main():
    poll_instance = GatherTxPoll()
    poll_instance.poll()
