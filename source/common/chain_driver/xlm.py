# -*- coding: utf-8 -*-
# @File :  xlm_poll.py
# @Author : lh
# @time : 18-11-12 下午8:47
from pprint import pprint
import json
# from source import config
from stellar_base.builder import Builder
from stellar_base.horizon import horizon_livenet, horizon_testnet
from stellar_base.keypair import Keypair
from stellar_base.memo import TextMemo
from stellar_base.operation import CreateAccount
from stellar_base.transaction import Transaction
from stellar_base.transaction_envelope import TransactionEnvelope
from stellar_base.utils import StellarMnemonic
from stellar_base.address import Address
from stellar_base.horizon import Horizon

from source.common.utils.log import get_logger

logger = get_logger('create-account-xlm_poll')


class XlmOP:
    def __init__(self, rpc_uri, timeout):
        self.client = Horizon(horizon=rpc_uri, timeout=timeout)  # 测试节点
        self.rpc_uri = rpc_uri
        # self.client = Horizon(horizon=horizon_livenet()) # 正式链

    def generate_pri_keys(self):
        """
        生成随机公钥私钥
        """
        # sm = StellarMnemonic()
        # secret_phrase = sm.generate()
        # kp = Keypair.deterministic(secret_phrase)
        kp = Keypair.random()
        publickey = kp.address().decode()
        seed = kp.seed().decode()
        return seed, publickey

    def create_account(self, old_account_seed, new_account_address, amount, memo):
        """
        用已有账户创建新账户
        """
        horizon = self.client
        account_seed = old_account_seed
        old_account_keypair = Keypair.from_seed(account_seed)
        account_addr = new_account_address
        start_amount = amount  # Your new account minimum balance (in XLM) to transfer over
        # create the CreateAccount operation
        opts = {
            'destination': account_addr,
            'starting_balance': start_amount
        }
        op = CreateAccount(
            opts
        )
        # create a memo
        txt_memo = TextMemo(memo)

        # Get the current sequence of the source account by contacting Horizon. You
        # should also check the response for errors!
        try:
            sequence = horizon.account(old_account_keypair.address().decode()).get('sequence')
        except Exception as e:
            logger.exception(e)
        # Create a transaction with our single create account operation, with the
        # default fee of 100 stroops as of this writing (0.00001 XLM)
        trans_ops = {
            'sequence': sequence,
            'memo': txt_memo,
            'operations': [op]

        }
        tx = Transaction(
            source=old_account_keypair.address().decode(),
            opts=trans_ops
        )
        env_opts = {
            'network_id': 'TESTNET'
        }
        envelope = TransactionEnvelope(tx=tx, opts=env_opts)
        # Sign the transaction envelope with the source keypair
        envelope.sign(old_account_keypair)

        # Submit the transaction to Horizon
        te_xdr = envelope.xdr()
        response = horizon.submit(te_xdr)
        return response

    def get_balance(self, publickey):
        """
        获取余额
        """
        res_obj = self.client.account(publickey)
        pprint(res_obj)
        # res = json.dumps(res_obj)
        balance = res_obj.get('balances', '')[0].get('balance', '')
        return balance

    def get_account_info(self, address):
        """
        获取账户信息
        """
        account_info = self.client.account(address)
        res = json.dumps(account_info)
        return res

    def create_transaction(self, from_address, to_address, amount, memo):
        """
        创建一笔交易
        :param from_address: 发起账户的私钥
        :param to_address:  目的账户的公钥
        :return: response
        """
        builder = Builder(secret=from_address, horizon_uri=self.rpc_uri)
        builder_memo = builder.add_text_memo(memo)
        builder_memo.append_payment_op(
            destination=to_address, amount=amount, asset_code='XLM')
        builder.sign()
        response = builder.submit()
        return response

    def get_transactions(self, publickey, cursor='now'):
        """
        获取交易列表
        """
        assert publickey and isinstance(publickey, str)
        params = {
            'order': 'desc',
            'limit': '200',
            'cursor': cursor
        }
        trras_res = self.client.account_transactions(publickey, params=params)
        pprint(trras_res)
        return trras_res.get('_embedded').get('records')

    def get_trans_info(self, txid):
        """
        获取交易信息
        """
        trans_res = self.client.transaction(txid)
        return trans_res

    def get_ledgers(self, cursor='now'):
        """
        获取当前区块信息
        """
        param = {
            'order': 'desc',
            'limit': '200',
            'cursor': cursor
        }
        res = self.client.ledgers(**param)
        return res['_embedded']['records']

    def get_account_payments(self, address, cursor='now'):
        param = {
            'order': 'desc',
            'limit': '200',
            'cursor': cursor,
            'address': address
        }
        res = self.client.account_payments(**param)
        return res

    def get_operations(self, address, cursor='now'):

        res_list = []
        for i in range(50):
            params = {
                'order': 'desc',
                'limit': '200',
                'cursor': cursor,
            }
            res = self.client.account_operations(address, params=params)
            pprint(res)
            if res:
                target = res.get('_embedded', '').get('records', '')
                if target:
                    res_list.extend([i for i in target if i.get('type', '') == 'payment'])
                    last_elm = target[-1]
                    cursor = last_elm['paging_token']
            else:
                break
        return res_list

    # def get_operations(self, address, cursor='now'):
    #     param = {
    #         'order': 'desc',
    #         'limit': '200',
    #         'cursor': cursor
    #     }
    #     res = self.client.account_operations(address, params=param)
    #     return res


if __name__ == '__main__':
    # rpc_uri = 'http://192.168.83.64:8000'
    rpc_uri = 'http://47.106.171.140:8000/'
    xlm = XlmOP(rpc_uri, 1000)
    # 创建地址
    # pprint(xlm.generate_pri_keys())
    # 创建账户
    # pprint(xlm.create_account('SAQ5RQZTFEARCE4ETHYNCGAOWKBZP2KJVP64IRSZKCOTNMPAVORYV46A',
    #                           'GB2FP2C4ZWFGYAPGPQVJQPWKPZ2SP4OCAALHGOVNIH5JMQATFOCIOJ4M',
    #                           '1',
    #                           'sjf'))
    # 查询余额
    # pprint(xlm.get_balance('GDDFGRIEHTRI2PUX2IPNU67QK3NMMQRE3ZNA4GGSBNBDI6VADJHNAUXU'))
    # pprint(xlm.get_balance('GB2FP2C4ZWFGYAPGPQVJQPWKPZ2SP4OCAALHGOVNIH5JMQATFOCIOJ4M'))
    # 创建交易
    # pprint(xlm.create_transaction('SB3MBO4MNEXOHZQJE6Z25LMEGZZUL5RMISXAN4KUHTUNKOCW6LQOKKTB',
    #                               config.xlm_cb_address,
    #                               10,
    #                               '100099'))
    # 获取当前区块数
    # pprint(xlm.get_ledgers())
    # 获取交易信息列表
    pprint(xlm.get_transactions('GDDFGRIEHTRI2PUX2IPNU67QK3NMMQRE3ZNA4GGSBNBDI6VADJHNAUXU'))
    # 查询某个交易hash信息
    # pprint(xlm.get_trans_info('f12610053f180f4b59cde17f889bc9d20ba0b8181ef4b47799b1f7316f217688'))
    # pprint(xlm.client.transactions())
    # 查询账户交易信息
    # pprint(xlm.get_account_payments('GBXNDLEZQ4TL4ZLMQW3JBRPACTY4XXZN2TTVQ5QTLOY3B4OTI5BW57SH'))
    # 查看账户操作信息
    # pprint(xlm.get_operations('GBXNDLEZQ4TL4ZLMQW3JBRPACTY4XXZN2TTVQ5QTLOY3B4OTI5BW57SH'))

    # cursor = 'now'
    # pub_address = 'GBXNDLEZQ4TL4ZLMQW3JBRPACTY4XXZN2TTVQ5QTLOY3B4OTI5BW57SH'
    # res_list = []
    # for i in range(50):
    #     res = xlm.get_transactions(pub_address, cursor)
    #     if res:
    #         res_list.extend(res)
    #         cursor = res[-1]['paging_token']
    #     else:
    #         break
    # pprint(res_list)

    # cursor = 'now'
    # rec_lsit = []
    # for i in range(50):
    #     res = xlm.get_ledgers(cursor)
    #     if res:
    #         rec_lsit.extend(res)
    #         cursor = rec_lsit[-1]['paging_token']
    #         print('loop', res)
    #     else:
    #         print('break', res)
    #         break
    # # pprint(rec_lsit)
    # pprint(rec_lsit[0]['sequence'])
    # pprint(rec_lsit[-1]['sequence'])
