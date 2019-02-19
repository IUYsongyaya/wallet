# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-31


import time
from source import config
from source.model.records import WithdrawBalanceRecord
from source.poll.wallets import WalletWithdraw


# 业务逻辑:
# 1. 从区块链上获取钱包的余额, 将余额更新到数据库表里

def main():
    withdraw = WalletWithdraw(config)
    record = WithdrawBalanceRecord(config)
    while True:
        balance = withdraw.get_balance()
        print("balance:", balance)
        record.balance = balance
        print(f"{withdraw.coin_type.upper()} balance update poll 1 loop done!")
        time.sleep(1)


if __name__ == '__main__':
    main()
