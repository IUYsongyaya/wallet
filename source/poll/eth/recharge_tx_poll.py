#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author:ljc
@file: recharge_tx_poll.py
@time: 2019/01/22
"""
import datetime
from decimal import Decimal, ROUND_DOWN
import time

from eth_utils import to_checksum_address
from web3 import Web3

from source import config
from source.common.utils import log
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.common.chain_driver.erc20_operator.const import DEFAULT_GAS_PRICE
from source.model.database import (Session,
                                   AskFeeStatusEnum, InformEnum,
                                   GatherStatusEnum,
                                   RechargeStatusEnum)
from source.poll.rpc_call import recharge

from .base import ErcTxPoll

logger = log.get_logger(__name__, config.log_level)

SUCCESS = 1

FAIL = -1


class RechargeTxPoll(ErcTxPoll):
    """
    充币交易轮寻类
    """
    
    @staticmethod
    def send_recharge_notify(recharge_record):
        try:
            recharge_record_ = vars(recharge_record) \
                if recharge_record else dict()
            recharge_address = recharge_record_.get('to_address', '')
            recharge_amount = recharge_record_.get('amount', 0)
            transaction_id = recharge_record_.get('txid', '')
            coin_type = recharge_record_.get('coin_type', '')
            from_address = recharge_record_.get('from_address', '')
            confirmations = recharge_record_.get('confirmation_count', 0)
            recharge_status = recharge_record_.get('status',
                                                   RechargeStatusEnum.RECHARGE)
            response = recharge(address=recharge_address,
                                from_address=from_address,
                                amount=float(recharge_amount),
                                txid=transaction_id,
                                coin_type=coin_type,
                                confirmations=confirmations,
                                status=recharge_status.value
                                )
            if transaction_id and response.get("result",
                                               "") == transaction_id:
                logger.info('已成功通知充币交易{}'.format(response))
                if recharge_status.value in [SUCCESS, FAIL]:
                    recharge_record.informed = InformEnum.YES
            else:
                logger.error('java后台没有确认{}冲币通知{}'.format(
                    coin_type, transaction_id))
        except Exception as e:
            logger.exception('java接口调用失败{}'.format(e))
    
    def create_fee_ask(self, session, coin_type, to_address):
        """创建手续费申请
        :param session: mysql会话
        :param coin_type: 币种类型,除了eth外也肯能是token
        :param to_address: 缴费对方地址
        """
        now = datetime.datetime.utcnow()
        from_address = to_checksum_address(config.eth_tb_address)
        ask_fee_ob = self.coin_ask_fee_coll(**{
            'amount': float(config.eth_fee_min),
            'status': AskFeeStatusEnum.ASKING,
            'created_at': now,
            'updated_at': now,
            'from_address': from_address,
            'to_address': to_address,
            'coin_type': coin_type,
            'coin_series': 'ETH'})
        session.add(ask_fee_ob)
    
    def create_gather(self, session, coin_type,
                      from_address, to_address,
                      amount, status):
        """
        创建钱包汇聚申请
        :param session:
        :param coin_type:
        :param from_address:
        :param to_address:
        :param amount:
        :param status:
        """
        now = datetime.datetime.utcnow()
        from_address = to_checksum_address(from_address)
        to_address = to_checksum_address(to_address)
        gather_record = self.coin_transfer_coll(**{
            "amount": amount,
            "status": status,
            "created_at": now,
            "updated_at": now,
            "from_address": from_address,
            "to_address": to_address,
            "coin_type": coin_type,
            "coin_series": "ETH",
        })
        session.add(gather_record)
    
    def check_gather(self, session, item):
        """检查是否汇聚
        :param session: 数据库链接session
        :param item: 交易信息
        :return:
        """
        coin_info = session.query(
            self.coin_coll).filter_by(**{'coin_type': item.coin_type,
                                         'main_coin': 'ETH'}).first()
        token_address = coin_info.token_address \
            if item.coin_type != 'ETH' else None
        
        operator = self.erc_op_class(provider_endpoint=config.eth_wallet_url,
                                     address=item.to_address,
                                     contract_address=token_address)
        
        is_ask_fee = session.query(
            self.coin_ask_fee_coll).filter(
            self.coin_ask_fee_coll.to_address == item.to_address,
            self.coin_ask_fee_coll.status.in_((AskFeeStatusEnum.ASKING,
                                               AskFeeStatusEnum.WAIT_CONFIRM))
        ).first()
        if is_ask_fee:
            return
        is_withdraw = session.query(self.coin_transfer_coll).filter(
            self.coin_transfer_coll.from_address == item.to_address,
            self.coin_transfer_coll.status.in_((GatherStatusEnum.GATHER_NO_FEE,
                                                GatherStatusEnum.GATHER,
                                                GatherStatusEnum.GATHERING))
        ).first()
        if is_withdraw:
            return
        
        master_operator = self.erc_op_class(provider_endpoint=config.eth_wallet_url,
                                            contract_address=token_address,
                                            address=to_checksum_address(
                                                config.eth_tb_address))
        
        eth_balance = Decimal(str(operator.get_ether_balance()))
        cz_max = config.eth_cz_max.get(item.coin_type
                                       ) or coin_info.cz_max
        tb_max = config.eth_tb_max.get(item.coin_type
                                       ) or coin_info.tb_max
        hw_transhold = Decimal(str(cz_max))
        cw_transhold = Decimal(str(tb_max))
        # 代币处理
        if token_address:
            token_balance = operator.get_address_token_balance(
                item.to_address, int(coin_info.token_unit))
            eth_hot_wallet = to_checksum_address(config.eth_tb_address)
            wallet_token_balance = master_operator.get_address_token_balance(
                eth_hot_wallet, int(coin_info.token_unit))
            
            if token_balance < hw_transhold:
                logger.info(
                    f"token_balance: {token_balance} wallet_token_balance:"
                    f" {wallet_token_balance}")
                return
            
            wallet_address = config.eth_tb_address if (
                    wallet_token_balance < cw_transhold) \
                else config.eth_cw_address
            
            if eth_balance < config.eth_fee_min:
                self.create_gather(
                    session, item.coin_type, item.to_address,
                    wallet_address, token_balance,
                    GatherStatusEnum.GATHER_NO_FEE)
                self.create_fee_ask(session, item.coin_type,
                                    item.to_address)
                return
            self.create_gather(
                session, item.coin_type, item.to_address,
                wallet_address, token_balance, GatherStatusEnum.GATHER)
            return
        
        # ETH处理
        child_balance = Decimal(str(operator.get_ether_balance()))
        if child_balance + Decimal(str(config.eth_fee_min)) < hw_transhold:
            return
        
        wallet_balance = Decimal(str(master_operator.get_ether_balance()))
        wallet_address = config.eth_tb_address if (
                wallet_balance < cw_transhold) \
            else config.eth_cw_address
        self.create_gather(session, item.coin_type,
                           item.to_address,
                           wallet_address,
                           child_balance - Decimal(str(config.eth_fee_min)),
                           GatherStatusEnum.GATHER)
    
    @staticmethod
    def check_success(operator: ERC20Token, item):
        """检查交易是否成功
        :param operator: 区块链驱动
        :param item: 交易信息
        :return:
        """
        res = operator.is_success(operator.get_transaction(item.txid))
        if res:
            return RechargeStatusEnum.SUCCESS
        else:
            return RechargeStatusEnum.FAILED
    
    def monitor_tx_id(self, session, item):
        """交易id监控
        :param session: 数据库链接
        :param item: 从区块上获取的交易信息
        :return:
        """
        now = datetime.datetime.utcnow()
        operator = self.erc_op_class(provider_endpoint=config.eth_wallet_url)
        try:
            
            (num_confirmations,
             gas_used) = self.get_confirm_info(operator, item)
            coin_info = session.query(
                self.coin_coll).filter_by(**{'coin_type': item.coin_type,
                                             'main_coin': 'ETH'}).first()
            confirm_limit = coin_info.chargeConfirmLimit if coin_info else config.eth_confirmations
            
            if item.confirmation_count and num_confirmations == item.confirmation_count:
                return
            
            item.confirmation_count = num_confirmations
            item.updated_at = now
            if num_confirmations >= confirm_limit:
                fee = Web3.fromWei(int(gas_used) * DEFAULT_GAS_PRICE,
                                   'ether').quantize(Decimal('0.00000001'),
                                                     rounding=ROUND_DOWN)
                # 检查是否成功
                status = self.check_success(operator, item)
                item.status = status
                item.fee = fee
                item.fee_coin = 'ETH'
                self.check_gather(session, item)
                self.send_recharge_notify(item)
                if item.status.value == FAIL:
                    logger.info(f'fail {item.txid}')
                    return
                # 成功
                logger.info(
                    f'monitor {item.txid} {num_confirmations} {gas_used}')
        except Exception as e:
            logger.exception("充币交易检测失败{}".format(e))
    
    def poll(self):
        logger.info("----------- erc_recharge_tx start -----------")
        session = Session()
        while True:
            try:
                recharge_list = session.query(self.coin_recharge_coll
                                              ).filter_by(
                    **{'coin_series': 'ETH', 'informed': InformEnum.NO}).all()
                for item in recharge_list:
                    self.monitor_tx_id(session, item)
                try:
                    session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error("冲币执行数据库commit失败")
                    logger.exception(e)
                else:
                    logger.info("冲币更新数据成功")
            except Exception as e:
                logger.exception("充币交易确认轮寻发生错误{}".format(e))
            time.sleep(10)


def main():
    poll_instance = RechargeTxPoll()
    poll_instance.poll()
