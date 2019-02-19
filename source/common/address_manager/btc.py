#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: btc.py
@time: 2018/10/23
"""
import copy
import datetime

from source import config
from source.common.chain_driver.bitcoin_operator import BtcOP

from .base import MysqlAddressManager


class BtcManager(MysqlAddressManager):
    def __init__(self, session_factory):
        """
        :param session_factory: mysql_session_maker
        """
        super().__init__(session_factory)
        self.coin_category = "BTC"
        self.chain_api = BtcOP(config)
    
    def generate_address(self, cnt: int) -> dict:
        """
        产生比特币地址账户
        :param cnt: 编号
        :return:
        """
        now = datetime.datetime.now()
        account_name = '{}_{}_{}_{}'.format(self.coin_category,
                                            now.strftime('%Y%m%d'),
                                            cnt, now.timestamp())
        ret = copy.deepcopy(self._address_template)
        ret['account'] = account_name
        pub_address = self.chain_api.get_new_address(account_name)
        ret['pub_address'] = pub_address
        ret['private_hash'] = self.encrypt_tool.encrypt(
            self.chain_api.dump_private_key(pub_address))
        ret['coin_type'] = self.coin_category
        ret['created_at'] = now
        ret['updated_at'] = now
        return ret
