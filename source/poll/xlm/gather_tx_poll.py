# -*- coding: utf-8 -*-
# @File :  gather_tx_poll.py
# @Author : lh

import time
import traceback

from source import config
from source.common.utils.log import get_logger
from source.model.database import Gather, GatherStatusEnum
from source.common.chain_driver.xlm import XlmOP

coin_type = 'XLM'
logger = get_logger('check-gather-xlm_poll')


class CheckGather:
    def check_gather_tx(self):
        xlm = XlmOP(config, config.xlm_tb_url)
        rec_list = Gather.find({'coin_type': coin_type,
                                'status': GatherStatusEnum.GATHER})
        try:
            for each in rec_list:
                tx_id = each['txid']
                res = xlm.get_trans_info(tx_id)
                each['fee'] = res.get('fee_paid')
                each['fee_coin'] = coin_type
                # 最新区块数减去创建交易所在区块的差值当作确认数
                trans_ldger = res.get('')
                ledger_res = xlm.get_ledgers()
                new_ledger = ledger_res[0]['sequence']
                # 获取区块确认数
                confirmation_count = new_ledger - trans_ldger
                each['confirmation_count'] = confirmation_count
                if confirmation_count >= config.xlm_confirmation:
                    each['status'] = GatherStatusEnum.SUCCESS
                    Gather.replace_one({'id': each['id']}, each)
        except Exception as e:
            logger.error(traceback.format_exc(e))

    def poll(self):
        logger.info("----------- check_gather start -----------")
        try:
            self.check_gather_tx()
            time.sleep(10)
        except Exception as e:
            logger.exception(e)
            time.sleep(60)


def main():
    check_gather = CheckGather()
    check_gather.poll()


if __name__ == '__main__':
    check_gather = CheckGather()
    check_gather.poll()
