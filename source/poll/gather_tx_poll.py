# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-31

import time
from source import config
from decimal import Decimal
from source.model.database import GatherStatusEnum
from source.model.records import GatheringRecord
from source.poll.wallets import WalletWithdraw

#
# 业务逻辑:
# 1. 轮询 gather 表中所有的转账记录
# 2. 根据转账记录中的 txid, 查询其确认数
# 3. 如果确认数有变化
# 4. 检测交易是否被取消 ( abandoned ? )
# 5. 检查交易确认数是否足够 ( confirmation_count >= confirm_cnt_touchstone ? )
# 6. 更新转账最终状态到  gather 表里
#


def main():
    withdraw = WalletWithdraw(config)
    records = GatheringRecord(config)

    while True:
        for r in records:
            txid = r["txid"]
            transaction = withdraw.get_transaction(txid)
            confirmation_count = transaction.get("confirmations", 0)
            
            if confirmation_count != r["confirmation_count"]:
                if transaction.get("abandoned", False):
                    r['status'] = GatherStatusEnum.FAILED
                
                if confirmation_count >= withdraw.confirm_cnt_touchstone:
                    r['status'] = GatherStatusEnum.SUCCESS
                    
                r["confirmation_count"] = confirmation_count
                r['fee'] = abs(Decimal(transaction.get('fee', 0)))
                records[txid] = r

        time.sleep(1)
        print(f"{withdraw.coin_type.upper()} withdraw gather poll 1 loop done!")


if __name__ == '__main__':
    main()
