# -*- coding: utf-8 -*-
# @File :  update_balance.py
# @Author : lh
import time

from source import config
from source.common.chain_driver.xlm import XlmOP
from source.common.utils.log import get_logger
from source.model.database import AccountBalance

from datetime import datetime

logger = get_logger('update-xlm_poll-balance')


class UpdateBalance:
    def update_balance(self):
        xlm = XlmOP(config, config.xlm_cb_url)
        tb_balance = xlm.get_balance(config.xlm_tb_address)
        record = {
            'coin_type': 'XLM',
            'updated_at': datetime.utcnow(),
            'balance': float(tb_balance)
        }
        AccountBalance.find_one_and_update({'coin_type': 'XLM'}, record)

    def poll(self):
        logger.info(f'-----update balance start----------')
        while True:
            try:
                self.update_balance()
                time.sleep(10)
            except Exception as e:
                logger.exception(e)


def main():
    update_balance_obj = UpdateBalance()
    update_balance_obj.poll()


if __name__ == '__main__':
    update_balance_obj = UpdateBalance()
    update_balance_obj.poll()
