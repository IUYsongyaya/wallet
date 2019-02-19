#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: recharge_poll.py
@time: 2018/10/29
"""
from source import config
from source.common.chain_driver.bitcoin_operator.bch import BchOP
from source.poll.btc_poll.recharge_poll import RechargePoll


class BchRecharge(RechargePoll):
    def __init__(self):
        super().__init__()
        self.coin_category = "BCH"
        self.driver = BchOP(config)


def main():
    poll_instance = BchRecharge()
    poll_instance.poll()
