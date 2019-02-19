# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-28 上午10:53

import time
from source import config

from source.common.utils.log import get_logger
from source.model.database import Gather, GatherStatusEnum
from source.common.chain_driver.bitcoin_operator.usdt import USDTOP


coin_type = 'USDT'
logger = get_logger('check-gather-usdt')


def check():
    usdt = USDTOP(config.usdt_rpc_uri, config.timeout)
    record = Gather.find({'coin_type': coin_type,
                          'status': GatherStatusEnum.GATHER})
    for each in record:
        tx_id = each['txid']
        rv = usdt.get_transaction(tx_id)
        each['fee'] = rv.get('fee')
        each['fee_coin'] = coin_type
        confirmation_count = rv.get('confirmation_count')
        each['confirmation_count'] = confirmation_count
        if confirmation_count > config.usdt_confirmation:
            each['status'] = GatherStatusEnum.SUCCESS
        if rv.get('abandoned', False):
            each['status'] = GatherStatusEnum.FAILED
        Gather.replace_one({'_id': each['_id']}, each)


if __name__ == '__main__':
    while True:
        try:
            check()
            time.sleep(10)
        except Exception as e:
            logger.exception(e)
            time.sleep(60)
