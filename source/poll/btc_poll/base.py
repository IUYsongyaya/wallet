#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: base.py
@time: 2018/10/23
"""
from abc import ABC, abstractmethod

from source import config
from source.common.chain_driver.bitcoin_operator import BtcOP
from source.model.database import (Recharge, Gather,
                                   AccountBalance, Account,
                                   TbRecord, CoinSetting)


class BtcPollBase(ABC):
    def __init__(self):
        self.coin_category = "BTC"
        self.driver = BtcOP(config)
        self.coin_recharge_col = Recharge
        self.coin_address_col = Account
        self.coin_setting_col = CoinSetting
        self.coin_account_balance_col = AccountBalance
        self.coin_transfer_col = Gather
        self.coin_withdraw_col = TbRecord
        
    @abstractmethod
    def poll(self):
        pass
