#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: base.py
@time: 2018/09/08
"""
import abc

from source.common.chain_driver.erc20_operator.erc20 import ERC20Token
from source.model.database import (TbRecord, Recharge,
                                   Gather, AskFee, Account, CoinSetting)


class BaseErcPoll(abc.ABC):
    def __init__(self):
        # 币种配置信息表
        self.coin_coll = CoinSetting
        # 充值记录表
        self.coin_recharge_coll = Recharge
        # 提现记录表
        self.withdraw_coll = TbRecord
        # 子地址汇集记录表
        self.coin_transfer_coll = Gather
        # 手续费申请表
        self.coin_ask_fee_coll = AskFee
        # 用户地址表
        self.coin_address_coll = Account
        self.erc_op_class = ERC20Token
    
    @abc.abstractmethod
    def poll(self):
        pass
    

class ErcTxPoll(BaseErcPoll, metaclass=abc.ABCMeta):
    @staticmethod
    @abc.abstractmethod
    def check_success(*args, **kwargs):
        pass
    
    @abc.abstractmethod
    def monitor_tx_id(self, *args, **kwargs):
        pass

    @staticmethod
    def get_confirm_info(operator, item):
        receipt = operator.get_transaction_receipt(item.txid)
        current_block_num = operator.get_block_number()
        tx_block_num = int(receipt['blockNumber'])
        num_confirmations = current_block_num - tx_block_num + 1
        gas_used = receipt['gasUsed']
        return num_confirmations, gas_used
