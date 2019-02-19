#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
更新余额
@author:ljc
@file: update_balance.py
@time: 2018/10/25
"""
import time
import datetime

from source import config

from source.common.utils import log
from source.model.database import Session

from .base import BtcPollBase


logger = log.get_logger(__name__, config.log_level)


class UpdateBalancePoll(BtcPollBase):
    def update_wallet_balance(self, session):
        backend = self.driver
        _doc = dict()
        utc_now = datetime.datetime.utcnow()
        _doc['coin_type'] = '%s_TX' % self.coin_category
        _doc['updated_at'] = utc_now
        _doc['balance'] = float(backend.get_balance())
        _doc['address'] = getattr(
            config, "{}_tb_address".format(self.coin_category.lower()))
        account_balance = session.query(
            self.coin_account_balance_col).filter_by(
            coin_type='%s_TX' % self.coin_category).with_for_update().first()
        if account_balance:
            account_balance.coin_type = _doc['coin_type']
            account_balance.update_at = _doc['updated_at']
            account_balance.balance = _doc['balance']
        else:
            account_balance_ = self.coin_account_balance_col(**_doc)
            session.add(account_balance_)
        try:
            session.commit()
        except Exception as e:
            logger.exception("更新余额表时发生错误{}".format(e))
            session.rollback()
    
    def poll(self):
        logger.info("----------- update balance start -----------")
        session = Session()
        while True:
            try:
                self.update_wallet_balance(session)
                time.sleep(10)
            except Exception as e:
                logger.exception("更新余额缓存表轮寻发生错误{}".format(e))
                time.sleep(60)


def main():
    poll_instance = UpdateBalancePoll()
    poll_instance.poll()
