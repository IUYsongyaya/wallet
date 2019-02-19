#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: test_create_erc20.py
@time: 2018/09/07
"""
from unittest.mock import Mock, patch
from eth_account import Account
from ethereum.tools import keys

from source.common.address_manager import ErcMongoManager
from source.command.create_address import main


def mock_create_keyfile(password, file_name=None):
    """创建钱包keyfile
    """
    account = Account.create()
    private_key = account.privateKey
    address = account.address
    keyfile_json = keys.make_keystore_json(private_key, password, kdf='scrypt')
    keyfile_json['id'] = str(keyfile_json['id'], encoding='utf-8')
    keyfile_json['address'] = address
    return address, private_key


class TestErc20:
    # def test_distribution_address(self):
    #     remainder = 100003 % 4  # 余数用来判断4个线程是否满足需求
    #     segment = 100003 // 4  # 整数用来判断每个线程中的创建地址数
    #     start_point = 0
    #     while True:
    #         print(start_point, start_point + segment)
    #         start_point += segment
    #         if sum([start_point, segment, remainder]) > 100003:
    #             break
    #     if remainder:
    #         print(100003 - remainder, 100003)

    @patch("source.common.chain_driver.erc20_operator.utils.keyfile_op."
           "create_keyfile", mock_create_keyfile)
    def test_create_address(self):
        manager = ErcMongoManager(Mock(), "ETH")
        address = manager.generate_address(1)
        assert address
        assert isinstance(address, dict)
        keys_ = {"account", "pub_address", "private_hash", "destination_tag",
                 "created_at", "updated_at", "coin_type", "is_used"}
        for i in keys_:
            assert i in address

    @patch("source.common.chain_driver.erc20_operator.utils.keyfile_op."
           "create_keyfile", mock_create_keyfile)
    @patch("source.config.mongo_user", False)
    @patch("sys.argv", ["_", "--coin_name", "ETH", "--num", '10'])
    @patch("pymongo.MongoClient")
    def test_bulk_create(self, mongo_client):
        mock_collection = Mock()
        mock_collection.insert = Mock(return_value=None)
        mongo_client.__getitem__.return_value = mock_collection
        main()

    @patch("source.common.chain_driver.erc20_operator.utils.keyfile_op."
           "create_keyfile", mock_create_keyfile)
    @patch("source.config.mongo_user", False)
    @patch("sys.argv", ["_", "--coin_name", "ETH", "20"])
    @patch("pymongo.MongoClient")
    def test_get_one_address(self, mongo_client):
        mock_collection = Mock()
        address_dict = {"account": "",
                        "pub_address": "",
                        "private_hash": "",
                        "destination_tag": "",
                        "created_at": "",
                        "updated_at": "",
                        "coin_type": "",
                        "is_used": False}
        mock_collection.find_one_and_update = Mock(return_value=address_dict)
        mongo_client.__getitem__ = Mock(return_value=mock_collection)
        manager = ErcMongoManager(mongo_client, "ETH")
        address = manager.get_address()
        assert address == address_dict
