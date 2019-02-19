# -*- coding: utf-8 -*-
# @File :  withdraw_poll.py
# @Author : lh

# 提币检测
import time
from source import config
from source.common.chain_driver.xlm import XlmOP
from source.poll.base import CheckWithdraw
from source.common.utils.log import get_logger
from source.model.database import TbRecord, TbStatusEnum

coin_type = 'XLM'
default_interval = 10
logger = get_logger('check-xlm_poll-tb')


class CheckWithDraw:
    def check_withdraw(self):
        res_list = TbRecord.find({'coin_type': coin_type,
                                  'status': TbStatusEnum.TRANSFER})
        xlm = XlmOP(config, config.xlm_tb_url)
        for each in res_list:
            tx_id = each['id']
            tx_res = xlm.get_trans_info(tx_id)
            tx_ledger = tx_res.get('ledger')
            # 获取当前最新区块数
            ledger_res = xlm.get_ledgers()
            new_ledger = ledger_res[0]['sequence']
            confirm_ledger = new_ledger - tx_ledger
            if confirm_ledger >= config.xlm_confirmation:
                tb = CheckWithdraw(each, confirm_ledger)
                tb.update_confirmations(confirm_ledger)

    def poll(self):
        logger.info("----------- check_withdraw start -----------")
        while True:
            try:
                self.check_withdraw()
                CheckWithdraw.update_informed(coin_type, 'withdraw')
                time.sleep(10)
            except Exception as e:
                logger.exception(e)
                time.sleep(60)


def main():
    check_withdraw1 = CheckWithDraw()
    check_withdraw1.poll()


if __name__ == '__main__':
    check_withdraw1 = CheckWithDraw()
    check_withdraw1.poll()
