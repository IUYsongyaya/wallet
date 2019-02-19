# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-11-7 下午7:57

from datetime import datetime

from source import config
from source.common.utils.log import get_logger
from source.model.database import AccountBalance
from source.common.chain_driver.bitcoin_operator.usdt import USDTOP


logger = get_logger('update-usdt-balance')


def update():
    usdt = USDTOP(config.usdt_rpc_uri, config.timeout)
    tb_balance = usdt.get_address_balance(config.usdt_tb_address)
    record = {
        'coin_type': 'USDT_TX',
        'updated_at': datetime.utcnow(),
        'balance': float(tb_balance)
    }
    AccountBalance.find_one_and_update({'coin_type': 'USDT_TX'}, record)


if __name__ == '__main__':
    while True:
        try:
            update()
        except Exception as e:
            logger.exception(e)
