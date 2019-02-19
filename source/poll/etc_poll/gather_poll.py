#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: gather_poll.py
@time: 2018/10/31
"""
import time
import datetime as dt

from source import config
from source.model.database import Session, GatherStatusEnum
from source.common.chain_driver.erc20_operator.erc20 import ERC20TokenChild
from source.common.utils.log import get_logger

from .base import BaseEtcPoll

# logging
logger = get_logger(__name__, config.log_level)

GAS_PRICE = 10


class GatherPoll(BaseEtcPoll):
    def get_account_info(self, session, address):
        """获取账户私钥密码"""
        address_info = session.query(self.coin_address_coll
                                     ).filter_by(pub_address=address).first()
        password = f'{config.etc_password_prefix}_{address_info.account}'
        private_key = address_info.private_hash
        return password, private_key
    
    def gather(self, session, item):
        """etc 汇聚操作函数"""
        if not item:
            return
        now = dt.datetime.utcnow()
        password, private_key = self.get_account_info(session,
                                                      item.from_address)
        eth = ERC20TokenChild(ipc_path=config.etc_ipc_path,
                              private_key=private_key,
                              password=password,
                              gas_price=GAS_PRICE)
        try:
            amount = item.amount
            tx_id = eth.send_ether(item.to_address, amount)
            logger.info((f"""Etc child withdraw done:
            {item.to_address} {amount}"""))
        except Exception as e:
            logger.exception(e)
        else:
            try:
                item.txid = tx_id
                item.status = GatherStatusEnum.GATHERING
                item.updated_at = now
                session.commit()
            except Exception as e:
                logger.exception("汇聚操作修改状态错误{}".format(e))
                session.rollback()
    
    def poll(self):
        logger.info('----------- etc gather start -----------')
        session = Session()
        while True:
            try:
                coin_transfer_list = session.query(
                    self.coin_transfer_coll).filter_by(
                    status=GatherStatusEnum.GATHER,
                    coin_series=self.coin_category).all()
                for item in coin_transfer_list:
                    self.gather(session, item)
            except Exception as e:
                logger.exception(e)
            time.sleep(10)


def main():
    poll_instance = GatherPoll()
    poll_instance.poll()
