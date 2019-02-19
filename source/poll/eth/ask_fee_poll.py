#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: ask_fee_poll.py
@time: 2018/09/10
"""
import datetime
import time

from web3.utils.encoding import (hexstr_if_str, to_hex)

from source import config
from source.common.utils.log import get_logger
from source.model.database import Session, AskFeeStatusEnum
from source.common.chain_driver.erc20_operator.utils.keyfile_op \
    import load_keyfile

from .base import BaseErcPoll

logger = get_logger(__name__, config.log_level)


class AskFeePoll(BaseErcPoll):
    def ask_fee(self, session, item):
        password = config.eth_password
        private_key = hexstr_if_str(to_hex,
                                    load_keyfile(config.eth_private_key_file,
                                                 password)
                                    )
        now = datetime.datetime.utcnow()
        eth = self.erc_op_class(provider_endpoint=config.eth_wallet_url,
                                private_key=private_key,
                                password=password)
        try:
            amount = item.amount
            tx_id = eth.send_ether(item.to_address, amount)
            logger.info(f'ETH withdraw ask fee done: {item.to_address} '
                        f'{amount}')
        except Exception as e:
            logger.exception("缴费转账时发生错误{}".format(e))
            item.status = AskFeeStatusEnum.ASK_FAILED
            item.updated_at = now
            item.error_msg = e
            try:
                session.commit()
            except Exception as e:
                logger.exception("缴费发生错误时更改状态也错误{}".format(e))
                session.rollback()
        else:
            item.status = AskFeeStatusEnum.WAIT_CONFIRM
            item.updated_at = now
            item.txid = tx_id
            try:
                session.commit()
            except Exception as e:
                logger.exception("缴费成功时更改状态错误{}".format(e))
                session.rollback()

    def poll(self):
        session = Session()
        logger.info('----------- ask_fee start -----------')
        
        while True:
            try:
                coin_ask_fee_list = session.query(
                    self.coin_ask_fee_coll).filter_by(
                    **{'status': AskFeeStatusEnum.ASKING,
                       'coin_series': 'ETH'}).all()
                for item in coin_ask_fee_list:
                    self.ask_fee(session, item)
            except Exception as e:
                logger.exception("缴费轮寻发生错误{}".format(e))
            time.sleep(10)


def main():
    poll_instance = AskFeePoll()
    poll_instance.poll()
