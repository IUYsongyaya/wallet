# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-30

import time

import logging
from decimal import Decimal
from source import config
from source.poll.wallets import WalletRecharge, WalletWithdrawRemote, WalletColdRemote
from source.model.records import GatherRecord

# 业务逻辑:
# 1. 检查冲币钱包余额是否超出
# 2. 检查提币钱包余额是否超出
# 3. 如果提币钱包余额未超出,将冲币钱包的币转账到提币钱包
# 4. 如果提币钱包余额超出,将冲币钱包的币转账到冷钱包
# 5. 记录转账到数据库


def main():
    recharge = WalletRecharge(config)
    withdraw = WalletWithdrawRemote(config)
    cold = WalletColdRemote(config)
    records = GatherRecord(config)
    while True:
        if recharge.get_balance() > Decimal(recharge.balance_max):
            from_ = recharge.wallet_address
            amount_ = recharge.get_balance() - Decimal(recharge.minimum_fee)
            print("withdraw balance[%u] vs balance_max[%s]" % (withdraw.balance, withdraw.balance_max))
            print("recharge left:", amount_)
            if amount_ > 0:
                if withdraw.balance < withdraw.balance_max:
                    to_ = withdraw.wallet_address
                    print("=> gather to withdraw wallet address: %s" % to_)
                else:
                    to_ = cold.wallet_address
                    print("=> gather to cold wallet address:%s" % to_)
                
                try:
                    txid_ = recharge.transfer_to(to_, amount_)
                except Exception as e:
                    logging.error(f"gather {amount_} to {to_} failed")
                    logging.exception(e)
                else:
                    records.insert(dict(
                        txid=txid_,
                        amount=amount_,
                        from_address=from_,
                        to_address=to_))
        
        time.sleep(1)
        print(f"{recharge.coin_type.upper()} gather gather poll 1 loop done!")


if __name__ == '__main__':
    main()
