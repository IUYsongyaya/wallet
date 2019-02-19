# -*- coding: utf-8 -*-
# @File :  recharge_poll.py
# @Author : lh


import time
from source import config
from datetime import datetime
from source.poll import rpc_call
from source.poll.base import CheckRecharge
from source.common.utils.log import get_logger
from source.common.chain_driver.xlm import XlmOP
from source.model.database import (
    Recharge, Account, RechargeStatusEnum, RegisterEnum, AccountBalance,
    InformEnum
)

coin_type = 'XLM'
logger = get_logger('recharge-xlm_poll')


class CheckRechargePoll:
    def check_recharge(self):
        """
        充币检测
        """
        xlm = XlmOP(config, config.xlm_tb_url)
        # 获取oplsit
        logger.info('*' * 20)
        res_list = xlm.get_operations(config.xlm_cb_address)
        for each in res_list:
            logger.info(f'交易xinxi{each}+++++')
            tx_id = each['transaction_hash']
            # 根据交易id获取memo
            tx_data = xlm.get_trans_info(tx_id)
            # huoqu zuixin ledger
            rec = xlm.get_ledgers()
            new_ledgers = rec[0].get('sequence', '')
            comfire_ledgers = new_ledgers - tx_data.get('ledger', '')
            if not comfire_ledgers > config.xlm_confirmation:
                logger.info(f'交易id: {tx_id}冲币失败')
                continue
            memo = tx_data['memo']
            to_address = each.get('to')
            from_address = each.get('from')
            rv = Account.find_one({'coin_type': coin_type,
                                   'pub_address': to_address,
                                   'destination_tag': memo})
            # 不是我们平台创建的地址 continue
            if not rv or not rv['is_used']:
                continue
            recharge_rec = Recharge.find_one({'coin_type': coin_type, 'txid': tx_id})
            if recharge_rec:
                cr = CheckRecharge(rv, config.xlm_confirmation)
                cr.update_confirmations(comfire_ledgers)
            # 如果不存在则往数据库插入此交易记录
            else:
                record = dict()
                record['to_address'] = to_address
                record['amount'] = each['amount']
                record['txid'] = each['transaction_hash']
                record['fee'] = tx_data['fee_paid']
                record['from_address'] = from_address
                record['coin_type'] = coin_type
                if comfire_ledgers >= config.xlm_confirmation:
                    record['status'] = RechargeStatusEnum.SUCCESS
                    record['done_at'] = datetime.utcnow()
                record['confirmation_count'] = comfire_ledgers
                try:
                    # 通知java组充值成功,java组确认再通知我们返回交易id
                    rv = rpc_call.recharge(to_address,
                                           from_address,
                                           record['amount'],
                                           tx_id,
                                           coin_type,
                                           comfire_ledgers,
                                           record['status'],
                                           memo)
                    # 防止因服务器挂掉rv返回空值增加判断
                    if rv == record['txid']:
                        record['informed'] = InformEnum.YES
                except Exception as e1:
                    logger.exception(e1)
                try:
                    Recharge(**record).insert()
                except Exception as e:
                    logger.exception(e)

    def poll(self):
        logger.info("----------- recharge poll  start -----------")
        print("----------- recharge poll  start -----------")
        while True:
            try:
                self.check_recharge()
                CheckRecharge.update_informed(coin_type, 'recharge')
                time.sleep(10)
            except Exception as e:
                logger.exception(e)
                print('----error------------')
                time.sleep(60)


def main():
    check_recharge_poll = CheckRechargePoll()
    check_recharge_poll.poll()


if __name__ == '__main__':
    check_recharge_poll = CheckRechargePoll()
    check_recharge_poll.poll()
