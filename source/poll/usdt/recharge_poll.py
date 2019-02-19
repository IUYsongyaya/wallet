# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-9-7 下午3:56

# 充币检测
import time
from datetime import datetime

from source import config
from source.poll import rpc_call
from source.poll.base import CheckRecharge
from source.common.utils.log import get_logger
from source.common.chain_driver.bitcoin_operator.usdt import USDTOP
from source.model.database import (
    Recharge, Account, RechargeStatusEnum, RegisterEnum, AccountBalance,
    InformEnum
)


coin_type = 'USDT'
property_id = 31
logger = get_logger('recharge-usdt')


def update_address_balance():
    rv = Recharge.find_one(
        {'coin_type': coin_type, 'register': RegisterEnum.NO}
    )
    for each in rv:
        address = each['to_address']
        amount = rv['amount']
        res = Recharge.find_one({'coin_type': coin_type, 'address': address})
        if res:
            record = {
                'address': address,
                'balance': amount,
                'coin_type': coin_type
            }
            ab = AccountBalance(**record)
            ab.insert()
        else:
            res['balance'] = res['balance'] + amount
            AccountBalance.replace_one({'id': res['id']}, res, for_update=True)


def check_recharge():
    u = USDTOP(config.usdt_rpc_uri, config.timeout)
    for each in u.list_transactions():
        record = {}
        if each.get('abandoned', False):
            logger.warning('recharge abandoned: {}'.format(each))
            continue
        if not each.get('valid', True):
            logger.warning('recharge invalid: {}'.format(each))
            continue
        if each.get('propertyid') != property_id:
            continue
        if each.get('category') == 'send':
            continue
        to_address = each.get('referenceaddress')
        rv = Account.find_one({'coin_type': coin_type,
                               'pub_address': to_address})
        if not rv or not rv.get('is_used'):
            continue
        tx_id = each['txid']
        confirmation_count = each['confirmation_count']
        rv = Recharge.find_one({'coin_type': coin_type, 'txid': tx_id})
        if rv:
            cr = CheckRecharge(rv, config.usdt_confirmation)
            cr.update_confirmations(confirmation_count)
        else:
            record['to_address'] = to_address
            record['amount'] = each['amount']
            record['txid'] = each['txid']
            record['fee'] = each['fee']
            record['from_address'] = each['sendingaddress']
            record['coin_type'] = coin_type
            record['coin_series'] = 'BTC'
            if confirmation_count > config.usdt_confirmation:
                record['status'] = RechargeStatusEnum.SUCCESS
                record['done_at'] = datetime.utcnow()
            record['confirmation_count'] = confirmation_count
            try:
                rv = rpc_call.recharge(to_address,
                                       record['from_address'],
                                       record['amount'],
                                       record['txid'],
                                       coin_type,
                                       confirmation_count,
                                       record['status'])
                if rv == record['txid']:
                    record['informed'] = InformEnum.YES
            except Exception as e1:
                logger.exception(e1)

            Recharge(**record).insert()


if __name__ == '__main__':
    while True:
        try:
            check_recharge()
            update_address_balance()
            CheckRecharge.update_informed(coin_type, 'recharge')
            time.sleep(10)
        except Exception as e:
            logger.exception(e)
            time.sleep(60)


