#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
钱包汇聚检查
@author:ljc
@file: gather_poll.py
@time: 2018/10/24
"""
import time
import datetime
from decimal import Decimal

from source import config
from source.common.utils import log
from source.model.database import Session, GatherStatusEnum

from .base import BtcPollBase


logger = log.get_logger(__name__, config.log_level)


class GatherPoll(BtcPollBase):
    def check_do_gather(self, session):
        """检查账户需要转移否，需要插入transfer记录"""
        backend = self.driver
        locale_balance = backend.get_balance()
        cz_max = getattr(config, self.coin_category.lower() + "_cz_max")
        # 如果大于充值钱包保留数量
        if locale_balance > Decimal(cz_max):
            now = datetime.datetime.utcnow()
            _doc = dict()
            _doc['coin_type'] = self.coin_category
            _doc['created_at'] = now
            _doc['updated_at'] = now

            tb_max = getattr(config, self.coin_category.lower() + "_tb_max")
            tb_balance_record = session.query(
                self.coin_account_balance_col
            ).filter_by(coin_type=self.coin_category + "_TX").first()
            tb_balance_dict = vars(tb_balance_record) \
                if tb_balance_record else dict()
            tb_balance = tb_balance_dict.get('balance', 0)
            amount = locale_balance - Decimal(
                getattr(config, self.coin_category.lower() + "_fee_min"))
        
            if tb_balance > tb_max:
                # 大于阈值转冷钱包
                _doc['to_address'] = getattr(config,
                                             self.coin_category.lower() +
                                             "_cw_address")
            else:
                _doc['to_address'] = getattr(config,
                                             self.coin_category.lower() +
                                             "_tb_address")

            txid = backend.send2address(_doc['to_address'], amount)
            try:
                _doc['amount'] = float(amount)
                _doc['txid'] = txid
                # _doc['from_address'] = backend.get_account_address() # 接口弃用
                _doc['status'] = GatherStatusEnum.GATHERING
                gather_record = self.coin_transfer_col(**_doc)
                session.add(gather_record)
                session.commit()
                logger.debug('done transfer btc to btc_tb: %s' % _doc)
            except Exception as e:
                logger.exception("插入汇聚记录失败{}, 汇聚交易id为{}".format(
                    e, txid))
                session.rollback()

    def poll(self):
        logger.info("----------- gather start -----------")
        session = Session()
        while True:
            try:
                self.check_do_gather(session)
                time.sleep(60 * 10)
            except Exception as e:
                logger.exception("汇聚轮寻发生错误{}".format(e))
                time.sleep(60 * 10)


def main():
    poll_instance = GatherPoll()
    poll_instance.poll()
