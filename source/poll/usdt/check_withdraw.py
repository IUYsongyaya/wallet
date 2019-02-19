# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-28 下午12:04

import time

from source import config
from source.poll.base import CheckWithdraw
from source.common.utils.log import get_logger
from source.common.chain_driver.bitcoin_operator.usdt import USDTOP
from source.model.database import TbRecord, TbStatusEnum, InformEnum


coin_type = 'USDT'
logger = get_logger('check-withdraw-usdt')


def check():
    res = TbRecord.find({'coin_type': coin_type,
                         'status': TbStatusEnum.TRANSFER})
    usdt = USDTOP(config.usdt_rpc_uri, config.timeout)
    for each in res:
        tx_id = each['txid']
        tx_detail = usdt.get_transaction(tx_id)
        confirmation_count = tx_detail.get('confirmation_count')
        cw = CheckWithdraw(each, config.usdt_confirmation)
        cw.update_confirmations(confirmation_count)


if __name__ == '__main__':
    while True:
        try:
            check()
            CheckWithdraw.update_informed(coin_type, 'withdraw')
            time.sleep(10)
        except Exception as e:
            logger.exception(e)
            time.sleep(60)

