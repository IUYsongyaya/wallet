#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: update_balance.py.py
@time: 2018/10/29
"""
from source import config
from source.common.chain_driver.bitcoin_operator.bch import BchOP
from source.poll.btc_poll.update_balance import UpdateBalancePoll


class BchUpdateBalance(UpdateBalancePoll):
    def __init__(self):
        super().__init__()
        self.coin_category = "BCH"
        self.driver = BchOP(config)


def main():
    poll_instance = BchUpdateBalance()
    poll_instance.poll()
