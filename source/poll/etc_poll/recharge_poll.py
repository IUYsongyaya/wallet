#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: recharge_poll.py
@time: 2018/10/30
"""
import datetime as dt
import time

from web3.utils.encoding import (hexstr_if_str, to_hex)

from source import config
from source.model.database import Session, RechargeStatusEnum, InformEnum
from source.common.utils.log import get_logger
from source.poll.rpc_call import recharge

from .base import BaseEtcPoll

# logging
logger = get_logger(__name__, config.log_level)


class RechargePoll(BaseEtcPoll):
    def __init__(self):
        super().__init__()

    def init_block_info(self, session):
        """第一次初始化数据库区块信息"""
        block_info = session.query(
            self.block_info_coll).filter_by(
            coin_type=self.coin_category).first()
        if block_info:
            return
        while True:
            try:
                operator = self.erc_op_class(ipc_path=config.etc_ipc_path)
                info = operator.get_block(int(operator.get_block_number()))
                block_info = {'block_num': int(info['number']),
                              'block_hash': hexstr_if_str(to_hex, info['hash']
                                                          ),
                              'coin_type': self.coin_category}
                block = self.block_info_coll(**block_info)
                session.add(block)
                session.commit()
                logger.info('etc_block_info init success')
                return
            except Exception as e:
                logger.error("etc初始化区块失败{}".format(e))
                session.rollback()
            time.sleep(15)

    def check_block(self, block_info, operator):
        """检查区块是否回滚"""
        if not block_info:
            return False
        info = operator.get_block(int(block_info.block_num) + 1)
        if not info:
            return False
        if hexstr_if_str(to_hex, info['parentHash']
                         ) == block_info.block_hash:
            checked_block = {'block_num': int(info['number']),
                             'block_hash': hexstr_if_str(to_hex, info['hash']),
                             'coin_type': self.coin_category}
        else:
            new_block_info = {
                'coin': self.coin_category,
                'block_num': int(block_info.block_num
                                 ) - int(config.etc_confirmations),
            }
            roll_back_info = operator.get_block(new_block_info['block_num'])
            new_block_info['block_hash'] = hexstr_if_str(
                to_hex, roll_back_info['hash'])
            # self.block_info_coll.update_one({'coin_type': self.coin_category},
            #                                 {'$set': new_block_info})
            checked_block = {'block_num': int(roll_back_info['number']),
                             'block_hash': hexstr_if_str(to_hex, roll_back_info['hash']),
                             'coin_type': self.coin_category}
        return checked_block
        
    @staticmethod
    def is_in_black_list(tx_data, is_not_offline):
        """检查黑名单"""
        try:
            black_list = [config.etc_tb_address]
            if tx_data.from_address in black_list and is_not_offline:
                return True
        except Exception as e:
            logger.exception(e)
            logger.error(f'black list check error: {tx_data.from_address}')
            return True
        return False

    def tx_process(self, session, tx_id, operator):
        """交易处理函数"""
    
        tx_data = operator.get_transaction_data(tx_id)
        now = dt.datetime.utcnow()
        user_info = session.query(
            self.coin_address_coll).filter_by(
            pub_address=tx_data.to_address).first()
        if not user_info:
            return
        # 是否为用户线下交易(从平台内一个账户提  ll币到另外一个账户)
        is_not_offline = 0 < float(tx_data.ether_amount
                                   ) <= float(config.etc_fee_min)
        if self.is_in_black_list(tx_data, is_not_offline):
            return

        recharge_record = session.query(self.coin_recharge_coll
                                        ).filter_by(txid=tx_id).first()
        if recharge_record:
            return
        data = dict()
        data['amount'] = float(tx_data.ether_amount)
        data['txid'] = tx_id
        data['created_at'] = now,
        data['status'] = RechargeStatusEnum.RECHARGE
        data['done_at'] = ''
        data['confirmation_count'] = tx_data.num_confirmations
        data['updated_at'] = now
        data['from_address'] = tx_data.from_address
        data['to_address'] = tx_data.to_address
        data['destination_tag'] = ''
        data['coin_type'] = self.coin_category
        data['coin_series'] = self.coin_category,
        data['comment'] = '',
        data['informed'] = InformEnum.NO
        logger.info(
            (f"""{data["coin_type"]} {data["amount"]}
            {data["confirmation_count"]}"""))
        recharge_record = self.coin_recharge_coll(**data)
        try:
            session.add(recharge_record)
            session.commit()
        except Exception as e:
            logger.exception("插入冲币记录发生错误{}".format(e))
            session.rollback()
            raise
        else:
            recharge(address=data['to_address'],
                     from_address=data['from_address'],
                     amount=data['amount'],
                     txid=data['txid'],
                     coin_type=data['coin_type'],
                     confirmations=data['confirmation_count'],
                     status=0)

    def poll(self):
        logger.info('-----------etc_recharge start-----------')
        session = Session()
        self.init_block_info(session)
        while True:
            try:
                operator = self.erc_op_class(ipc_path=config.etc_ipc_path)
                # 获取区块信息及交易列表
                block_info = session.query(
                    self.block_info_coll).filter_by(
                    coin_type=self.coin_category).first()
                checked_block_info = self.check_block(block_info, operator)
                if not checked_block_info:
                    continue
                tx_list = operator.get_block_tx_id_list(
                    checked_block_info['block_num'])
                # 遍历交易列表
                for tx_id in tx_list:
                    self.tx_process(session, hexstr_if_str(to_hex, tx_id),
                                    operator)
                logger.info(
                    f'pull block finished: {checked_block_info["block_num"]}')
            except Exception as e:
                logger.exception(e)
            else:
                # 存储交易区块信息
                block_info.block_num = checked_block_info['block_num']
                block_info.block_hash = checked_block_info['block_hash']
                try:
                    session.commit()
                except Exception as e:
                    logger.exception("检查回滚区块时发生错误{}".format(e))
                    session.rollback()
            time.sleep(3)


def main():
    poll_instance = RechargePoll()
    poll_instance.poll()
