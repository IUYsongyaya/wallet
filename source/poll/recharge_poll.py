# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-29

import time
from source import config
from decimal import Decimal
from source.common.utils.log import get_logger
from source.model.records import RechargeRecord
from source.poll.wallets import WalletRecharge
from source.model.database import RechargeStatusEnum, InformEnum

logger = get_logger('recharge-poll')

# 业务逻辑:
# 1. 轮询询区块链上所有的充值本钱包的交易记录 ( transaction )
# 2. 检查当前交易是否已记入表内,如果未记入表内则插入一条记录
# 3. 如果当前交易确认数有变化 并且当前交易未经通知 Java
# 4. 检查当前交易是否被取消( abandoned ? )
# 5. 检测当前交易确认数是否足够 ( >= confirm_cnt_touchstone ? )
# 6. 通知 JAVA 确认数有变化 和 交易的最终状态

# Recharge wallet
# DEBUG:source.common.chain_driver.utils:-1-> getnewaddress ["QTUM_20190213_0_1550045763.492328"]
# DEBUG:source.common.chain_driver.utils:<-1- "qJkRgdNg65x41P5friw6sJQS4iLzoEtknE"
# DEBUG:source.common.chain_driver.utils:-2-> dumpprivkey ["qJkRgdNg65x41P5friw6sJQS4iLzoEtknE"]
# DEBUG:source.common.chain_driver.utils:<-2- "cNMbrjecRwexmSpQLqRVBPvGEJL3pxQDBDWCbhsJ5Hqoss1GVEen"

# Withdraw Wallet
# WARNING:root:item:database_uri not in qtum.json, try env
# DEBUG:source.common.chain_driver.utils:-1-> getnewaddress ["QTUM_20190214_0_1550131852.770854"]
# DEBUG:source.common.chain_driver.utils:<-1- "qbHxhBw63td4TD2AkprJzptsG3ZcxDhLis"
# DEBUG:source.common.chain_driver.utils:-2-> dumpprivkey ["qbHxhBw63td4TD2AkprJzptsG3ZcxDhLis"]
# DEBUG:source.common.chain_driver.utils:<-2- "cTgWebpdRPBDZQbr7Y9v6ENT9fh7de8dnRTQD6esyvYM44mE11Pz"


# Cold Wallet
# qXZXC6BzXhb1LBp2Q7Huq3xScfHbth74pi


def main():
    recharge = WalletRecharge(config)
    records = RechargeRecord(config)
    while True:
        for transaction in recharge.filter_transactions(recharge.list_transactions_in()):
            txid = transaction["txid"]
            r = records[txid]
            print(
                f"txid: {txid}, to_address:{transaction['address']}, confirmations: {transaction['confirmations']}, "
                f"amount:{Decimal(transaction['amount'])}")
            if r:
                confirmation_count = transaction["confirmations"]
                informed = r['informed']
                print(f"informed:{informed} cur:{confirmation_count} vs dst:{r['confirmation_count']}")
                if confirmation_count != r["confirmation_count"] and not informed:
                    r['confirmation_count'] = confirmation_count
                    if transaction.get('abandoned', False):
                        r['status'] = RechargeStatusEnum.FAILED
                    
                    if confirmation_count >= recharge.confirm_cnt_touchstone:
                        r['status'] = RechargeStatusEnum.SUCCESS
                    
                    if recharge.notify(r):
                        if r['status'] == RechargeStatusEnum.FAILED or r['status'] == RechargeStatusEnum.SUCCESS:
                            r['informed'] = InformEnum.YES
                    else:
                        logger.warning("Recharge notify java failed!")
                    records[txid] = r
            else:
                records.insert(transaction)
        
        time.sleep(1)
        print(f"{recharge.coin_type.upper()} recharge poll 1 loop done!")


if __name__ == '__main__':
    main()
