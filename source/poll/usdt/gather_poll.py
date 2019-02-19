# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-28 上午10:11

import time

from source import config
from source.poll.base import get_tb_balance
from source.common.utils.log import get_logger
from source.common.chain_driver.bitcoin_operator import BtcOP
from source.common.chain_driver.bitcoin_operator.usdt import USDTOP
from source.model.database import (
    Gather, AccountBalance, AskFeeStatusEnum, AskFee
)


coin_type = 'USDT'
logger = get_logger('gather-usdt')


def ask_fee(address):
    """usdt转账使用btc作为手续费."""

    rv = AskFee.find_one({'coin_type': 'BTC', 'to_address': address,
                          'status': AskFeeStatusEnum.ASKING})
    if not rv:
        record = {
            'coin_type': 'BTC',
            'to_address': address,
            'amount': config.usdt_fee_min
        }
        AskFee(**record).insert()


def check_fee(address):
    btc_backend = BtcOP(config.usdt_rpc_uri, config.timeout)
    btc_balance = btc_backend.get_balance(btc_backend.getaccount(address))
    return btc_balance > config.usdt_fee_min


def gather():
    rv = AccountBalance.find({'coin_type': coin_type})
    usdt = USDTOP(config.usdt_rpc_uri, config.timeout)
    for each in rv:
        record = {}
        address, balance = each.address, each.balance
        if balance < config.usdt_cb_max:
            continue
        record['from_address'] = address
        tb_balance = get_tb_balance(coin_type)
        if tb_balance > config.usdt_tb_max:
            record['to_address'] = config.usdt_cw_address
        else:
            record['to_address'] = config.usdt_tb_address
        if not check_fee(address):
            ask_fee(address)
            continue
        record['amount'] = balance  # usdt可以全部发送，因为手续费扣的是btc
        record['coin_type'] = coin_type
        record['coin_series'] = 'BTC'
        tx_id = usdt.send_usdt(record['from_address'],
                               record['to_address'],
                               record['amount'])
        each.balance = 0
        AccountBalance.replace_one({'id': each['id']}, each, for_update=True)

        record['txid'] = tx_id
        g = Gather(**record)
        g.insert()


if __name__ == '__main__':
    while True:
        try:
            gather()
            time.sleep(10)
        except Exception as e:
            logger.exception(e)
            time.sleep(60)
