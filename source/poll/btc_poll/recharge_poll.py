#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
比特币冲币检测
@author:ljc
@file: recharge_poll.py
@time: 2018/10/23
"""
import time
import datetime

from source import config
from source.common.utils import log
from source.model.database import InformEnum, RechargeStatusEnum, Session
from source.poll.rpc_call import recharge

from .base import BtcPollBase


logger = log.get_logger(__name__, config.log_level)


class RechargePoll(BtcPollBase):
    def send_recharge_notify(self, session, recharge_record_):
        try:
            recharge_record = vars(recharge_record_) \
                if recharge_record_ else dict()
            recharge_address = recharge_record.get('to_address', '')
            recharge_amount = recharge_record.get('amount', 0)
            transaction_id = recharge_record.get('txid', '')
            from_address = recharge_record.get('from_address', '')
            confirmations = recharge_record.get("confirmation_count", 0)
            status = recharge_record.get("status",
                                         RechargeStatusEnum.RECHARGE)
            response = recharge(address=recharge_address,
                                from_address=from_address,
                                amount=recharge_amount,
                                txid=transaction_id,
                                coin_type=self.coin_category,
                                confirmations=confirmations,
                                status=status.value)
            if transaction_id and response == transaction_id:
                logger.info('已成功通知充币交易{}'.format(response))
                if status.value in [RechargeStatusEnum.SUCCESS.value,
                                    RechargeStatusEnum.FAILED.value]:
                    try:
                        recharge_record_.informed = InformEnum.YES
                        session.commit()
                    except Exception as e:
                        logger.exception("修改充值记录是否通知字段失败{}".format(e))
                        session.rollback()
                    else:
                        logger.info('已成功修改充币交易状态')
            else:
                logger.error('java后台没有确认{}冲币通知{}'.format(
                    self.coin_category, transaction_id))
        except Exception as e:
            logger.exception("java借口调用失败{}".format(e))
        
    def check_recharge(self, session):
        backend = self.driver
        for transaction in backend.list_transactions():
            _doc = dict()
            now = datetime.datetime.utcnow()
            # 如果冲币不合法跳过
            # btc / ltc有abandoned, usdt 有valid字段, bch 没有相关字段
            if transaction.get('abandoned', False):
                logger.warning('recharge abandoned: %s' % transaction)
                continue
            if not transaction.get('valid', True):
                logger.warning('recharge invalid: %s' % transaction)
                continue
            # 非冲币，不处理
            if transaction.get('category') == 'send':
                continue
            # ''默认账户和usdt转出没有在coin address中，不是冲币
            transaction['amount'] = float(transaction.get('amount'))
            recharge_record_ = session.query(
                self.coin_recharge_col
            ).filter_by(**{'txid': transaction['txid'],
                           'coin_type': self.coin_category,
                           'informed': InformEnum.NO}).first()
            recharge_record = vars(recharge_record_) \
                if recharge_record_ else dict()
    
            if recharge_record:
                # 更新充值表
                if recharge_record_.confirmation_count == transaction.get(
                        'confirmations'):
                    continue
                status = recharge_record.get('status',
                                             RechargeStatusEnum.RECHARGE)
                if status.value >= RechargeStatusEnum.SUCCESS.value:
                    continue
                coin_obj = session.query(self.coin_setting_col).filter_by(
                    **{'coin_type': self.coin_category}).first()
                coin_config = vars(coin_obj) if coin_obj else dict()
                confirm_cnt_touchstone = coin_config.get(
                    'chargeConfirmLimit') if coin_obj \
                    else getattr(config,
                                 self.coin_category.lower() +
                                 "_confirms")
            
                recharge_record_.confirmation_count = \
                    transaction.get('confirmations')
            
                if transaction.get('abandoned', False):
                    logger.warn('update abandoned: {}'.format(
                        transaction.get('txid')))
                    recharge_record_.status = RechargeStatusEnum.FAILED
            
                if transaction.get('confirmations', 0
                                   ) >= confirm_cnt_touchstone:
                    recharge_record_.status = RechargeStatusEnum.SUCCESS
                    logger.info('check done: %s' % recharge_record)
                recharge_record_.updated_at = now
            else:
                _doc['to_address'] = transaction['address']
                _doc['created_at'] = now
                _doc['updated_at'] = now
                _doc['amount'] = transaction.get('amount')
                _doc['txid'] = transaction.get('txid')
                _doc['coin_type'] = self.coin_category
                _doc['coin_series'] = self.coin_category
                _doc['confirmation_count'] = \
                    transaction.get('confirmations')
                _doc['source_tag'] = str()
                _doc['destination_tag'] = str()
                confirm_num = getattr(config,
                                      self.coin_category.lower() +
                                      "_confirms")
                if transaction.get('confirmations', 0) >= confirm_num:
                    _doc['status'] = RechargeStatusEnum.SUCCESS
                recharge_record_ = self.coin_recharge_col(**_doc)
                session.add(recharge_record_)
            try:
                session.commit()
            except Exception as e:
                logger.exception("更新充值表发送错误{}".format(e))
                session.rollback()
            else:
                recharge_record_ = session.query(
                    self.coin_recharge_col
                ).filter_by(**{'txid': transaction['txid'],
                               'coin_type': self.coin_category,
                               'informed': InformEnum.NO}).first()
                self.send_recharge_notify(session, recharge_record_)

    def poll(self):
        logger.info("----------- recharge start -----------")
        session = Session()
        while True:
            try:
                self.check_recharge(session)
                time.sleep(5)
            except Exception as e:
                logger.exception("冲币轮寻发生错误{}".format(e))
                time.sleep(30)
            

def main():
    poll_instance = RechargePoll()
    poll_instance.poll()
