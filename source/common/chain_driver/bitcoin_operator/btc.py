#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: btc.py
@time: 2018/10/23
"""
from source.common.chain_driver.utils import AuthProxy
from source.exception import BalanceNotSufficientError


class BtcOP:
    
    """btc rpc operations
    """
    def __init__(self, rpc_uri, timeout):
        self.connection = AuthProxy(rpc_uri, timeout=timeout)

    # def get_account_address(self, account=''):
    #     """获得账户的地址，如果account为空则返回默认账户的地址
    #     """
    #     assert isinstance(account, str)
    #     return self.connection.getaccountaddress(account)# 接口弃用

    def get_account(self, address=''):
        """获得地址的账户
        """
        assert isinstance(address, str)
        return self.connection.getaccount(address)

    def get_balance(self, account=''):
        """查询余额
        """
        assert isinstance(account, str)

        if account:
            balance = self.connection.getbalance(account)
        else:
            balance = self.connection.getbalance()

        return balance

    def list_accounts(self):
        """查询账户
        """
        return self.connection.listaccounts()

    def send2address(self, bit_coin_address, amount):
        """转账
        """
        # 检查参数
        assert bit_coin_address and amount
        assert isinstance(bit_coin_address, str)

        # 查询余额
        balance = self.get_balance()

        if amount > balance:
            raise BalanceNotSufficientError(amount, balance)

        tx_hash = self.connection.sendtoaddress(bit_coin_address, amount)

        return tx_hash

    def get_new_address(self, account=''):
        """得到新地址
        """
        assert isinstance(account, str)

        if account:
            btc_address = self.connection.getnewaddress(account)
        else:
            btc_address = self.connection.getnewaddress()

        return btc_address

    def list_transactions(self):
        """获取钱包交易信息
            [{
              "account": "from_wx3",
              "address": "moAtJvLFNGmMGzVUKtcTc1L11HZGmxPMze",
              "category": "receive",
              "amount": 0.16249190,
              "label": "from_wx3",
              "vout": 2,
              "confirmations": 1268,
              "blockhash": "0000000000000140a1c3727f1db30286e62691383e3712f5cb96e6dc25aff470",
              "blockindex": 22,
              "blocktime": 1525185105,
              "txid": "fbf669af6bf01cbbe436e330dce0bf728e1bc61857087d1d36edaea3852319c0",
              "walletconflicts": [
              ],
              "time": 1525185065,
              "timereceived": 1525185065,
              "bip125-replaceable": "no"
              },
              ...]
        """
        trans = self.connection.listtransactions('*', 10)
        return trans

    def list_received_by_address(self):
        """获取钱包收到的充值
        {"address": "mgjwnow8SxtmhhTLDkoxDLbXf7inXU7eWc",
         "account": "to",
         "amount": 3.77813046,
         "confirmations": 839,
         "label": "to",
         "txids": [
          "72158132dad3f1fbd271c989b4e01e2dbd380b1df96c27da3d3e06fd2a416a01",
          "ab144598bd6e8c259a2181914eca5cecc1bca1d7294f52c1899dd1fb2423040b",
          "b98f80be74319cc07a065a7e4cf3548a2301e306f121c0695d264ad767d90b11",
          "aa92664fb961baf35b6e1840985c771fdb983e969c7f87c7573cc0949335e315",
          "5ffa57cb8cae3b35ed127892e16897a6bb6666c1b50e95a394dff107b5e12d1c"]
          }
        """
        return self.connection.listreceivedbyaddress()

    def set_tx_fee(self, amount=0.00000001):
        """设置交易费

        not use for now
        """
        assert isinstance(amount, (int, float))
        assert amount and amount > 0

        self.connection.settxfee(amount)

    def move(self, from_account, to_account, amount):
        """钱包内账户建转移
        """
        assert isinstance(amount, (int, float))
        assert from_account and to_account and amount and amount > 0

        self.connection.move(from_account, to_account, amount)

    def generate(self, amount=1):
        """regtest 产生1个新块
        """
        assert isinstance(amount, (int, float))
        assert amount and amount > 0

        self.connection.generate(amount)

    def get_raw_transaction(self, tx_hash):
        """取原始交易
        """
        assert tx_hash and isinstance(tx_hash, str)

        return self.connection.getrawtransaction(tx_hash)

    def get_wallet_info(self):
        """获取钱包信息
        """
        return self.connection.getwalletinfo()

    def get_block_chain_info(self):
        """获取钱包信息"""
        return self.connection.getblockchaininfo()

    def get_network_info(self):
        """获取钱包信息
        """
        return self.connection.getnetworkinfo()

    def get_block_count(self):
        """获取区块数量
        """
        return self.connection.getblockcount()

    def get_transaction(self, txid):
        """获取交易信息
        """
        assert txid and isinstance(txid, str)

        return self.connection.gettransaction(txid)

    def dump_private_key(self, pub):
        """导出私钥
        """
        assert pub and isinstance(pub, str)

        return self.connection.dumpprivkey(pub)

    def import_private_key(self, priv):
        """导入私钥
        """
        assert priv and isinstance(priv, str)

        return self.connection.dumpprivkey(priv)
