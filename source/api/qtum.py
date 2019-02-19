#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:zxy
@file: qtum.py
@time: 2018/11/7
"""
from source import config
from source.model.database import Session, TbRecord
from source.common.address_manager import QtumManager
from source.common.chain_driver.bitcoin_operator import QtumOP
from source.common.utils.log import get_logger
from . import BaseAPI


logger = get_logger(__name__, config.log_level)


class Qtum(BaseAPI):
    def __init__(self):
        super().__init__("QTUM")
        self.manager_class = QtumManager
        self.driver = QtumOP(config.rpc_uri, config.timeout)
    
    def get_address(self, *args, **kwargs):
        manager = self.manager_class(Session)
        address = manager.get_address()
        return {"pub_address": address.get("pub_address", ""),
                "tag": address.get("destination_tag", "")}
    
    def send2address(self, address, amount, *args, **kwargs):
        try:
            tx_hash = self.driver.send2address(address, amount)
            data = {
                'amount': amount,
                'txid': tx_hash,
                'from_address': config.tb_address,
                'coin_type': self.coin_type,
                'to_address': address
            }
            logger.info('withdraw {} to {}'.format(self.coin_type, address))
            document = TbRecord(**data)
            document.insert()
            return tx_hash
        except Exception as e:
            logger.exception(e)
