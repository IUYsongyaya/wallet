# -*- coding: utf-8 -*-
# @File :  gather_poll.py
# @Author : lh

import time
from source import config
from source.poll.base import get_tb_balance
from source.common.utils.log import get_logger
from source.common.chain_driver.xlm import XlmOP
from source.model.database import Gather

coin_type = 'XLM'
logger = get_logger('gather-xlm_poll')


class GatherPoll:
    def gather(self):
        xlm = XlmOP(config, config.xlm_cb_url)
        cb_balance = float(xlm.get_balance(config.xlm_cb_address))
        # 如果获取提币服务器节点上的提币余额失败，则获取余额表里面的提币钱包余额数据
        tb_balance = get_tb_balance(coin_type)
        record = {'coin_type': coin_type}
        if cb_balance < config.xlm_cb_max:
            return
        if tb_balance < config.xlm_tb_max:
            record['to_address'] = config.xlm_tb_address
        else:
            record['to_address'] = config.xlm_cw_address
        record['amount'] = cb_balance - config.xlm_cb_reserve
        record['from_address'] = config.xlm_cb_address
        try:
            trans_res = xlm.create_transaction(config.xlm_cb_address,
                                               record['to_address'],
                                               record['amount'],
                                               memo='gather')

            record['txid'] = trans_res['hash']
            g = Gather(**record)
            g.insert()
        except Exception as e:
            logger.exception(e)

    def poll(self):
        logger.info("----------- gather start -----------")
        while True:
            try:
                self.gather()
                time.sleep(10)
            except Exception as e:
                logger.exception(e)
                time.sleep(60)


def main():
    gather_poll = GatherPoll()
    gather_poll.poll()


if __name__ == '__main__':
    gather_poll = GatherPoll()
    gather_poll.poll()
