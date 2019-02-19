# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-31


import time
from source import config
from source.poll.wallets import WalletWithdraw
from source.model.records import WithdrawRecord
from source.model.database import TbStatusEnum, InformEnum

#
# 业务逻辑:
# 1. 轮询 withdraw 表中所有的提币记录
# 2. 根据提币记录中的 txid, 查询其确认数
# 3. 如果确认数有变化
# 4. 检测交易是否被取消 ( abandoned ? )
# 5. 检查交易确认数是否足够 ( confirmation_count >= confirm_cnt_touchstone ? )
# 6. 将最终状态通知 JAVA,并且更新到 withdraw 表里
#


def main():
    withdraw = WalletWithdraw(config)
    records = WithdrawRecord(config)
    while True:
        for r in records:
            txid = r["txid"]
            print("===============> withdraw poll txid:", txid)
            transaction = withdraw.get_transaction(txid)
            confirmation_count = transaction.get("confirmations", 0)
            
            if confirmation_count != r["confirmation_count"]:
                if transaction.get("abandoned", False):
                    r['status'] = TbStatusEnum.FAILED
                    r['error_msg'] = 'abandoned'

                if confirmation_count >= withdraw.confirm_cnt_touchstone:
                    r['status'] = TbStatusEnum.SUCCESS
                
                r["confirmation_count"] = confirmation_count
                if withdraw.notify(r):
                    r['informed'] = InformEnum.YES
                    records[txid] = r
        
        time.sleep(1)
        print(f"{withdraw.coin_type.upper()} withdraw poll 1 loop done!")


if __name__ == '__main__':
    main()
