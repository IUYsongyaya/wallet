#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:zxy
@file: qtum.py
@time: 2018/11/7
"""
import copy
import datetime

from source import config
from source.common.chain_driver.bitcoin_operator import QtumOP

from source.common.address_manager.base import MysqlAddressManager


class AddressManager(MysqlAddressManager):
    def __init__(self, session_factory):
        """
        :param db_connect: 已选择db后的mongo连接,或者是mysqlsession
        """
        super().__init__(session_factory)
        self.coin_type = config.coin_type
        self.chain_api = QtumOP(config.rpc_uri, config.timeout)
    
    def generate_address(self, cnt: int) -> dict:
        """
        产生比特币地址账户
        :param cnt: 编号
        :return:
        """
        now = datetime.datetime.now()
        account_name = '{}_{}_{}_{}'.format(self.coin_type.upper(),
                                            now.strftime('%Y%m%d'),
                                            cnt, now.timestamp())
        ret = copy.deepcopy(self._address_template)
        ret['account'] = account_name
        pub_address = self.chain_api.get_new_address(account_name)
        ret['pub_address'] = pub_address
        ret['private_hash'] = self.encrypt_tool.encrypt(
            self.chain_api.dump_private_key(pub_address))
        ret['coin_type'] = self.coin_type.upper()
        ret['created_at'] = now
        ret['updated_at'] = now
        return ret
