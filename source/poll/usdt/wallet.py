# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-31
import abc
import copy
from source.poll.wallet_interface import WalletInterface
from source.common.chain_driver.bitcoin_operator import USDTOP
from source.model.database import Account
from source.common.chain_driver.utils import JSONRPCException
from source.common.utils.log import get_logger

PROPERTY_ID = 31
EmptyTransaction = dict(confirmations=0)
logger = get_logger("qtum-wallet")


class WalletImpl(WalletInterface):

    def __init__(self, configure):
        self.coin_type = configure.coin_type
        self.wallet_op = USDTOP(configure.rpc_uri, timeout=configure.timeout)

    def list_transactions(self):
        trans = self.wallet_op.list_transactions()
        if not trans:
            raise StopIteration
        for tran in trans:
            tran['address'] = tran['referenceaddress']
            yield tran

    def list_transactions_in(self):
        for tran in self.list_transactions():
            if tran["category"] == "receive":
                yield tran

    def list_transactions_out(self):
        for tran in self.list_transactions():
            if tran["category"] == "send":
                yield tran
    
    @abc.abstractmethod
    def filter_transactions(self, trans):
        pass

    def get_transaction(self, txid):
        try:
            tran = self.wallet_op.get_transaction(txid)
        except JSONRPCException as e:
            tran = EmptyTransaction
            # logger.error("No such transaction by txid:", txid)
            # logger.exception(e)
        return tran

    def get_balance(self):
        return self.wallet_op.get_balance()

    def transfer_to(self, account_address, amount):
        return self.wallet_op.send2address(account_address, amount)

    @abc.abstractmethod
    def wallet_address(self):
        pass
    

class WalletRechargeImpl(WalletImpl):
    Account = Account
    
    def __init__(self, configure):
        super().__init__(configure)
    
    def filter_transactions(self, trans):
        for tran in trans:
            if tran.get('valid', False) and tran.get('propertyid', 0) == PROPERTY_ID:
                if self.Account.find_one({'pub_address': tran["address"], "coin_type": self.coin_type}):
                    yield tran

    def wallet_address(self):
        return "Qtum recharge wallet"


class WalletWithdrawImpl(WalletImpl):
    
    def __init__(self, configure):
        super().__init__(configure)
    
    def filter_transactions(self, trans):
        yield from trans

    def wallet_address(self):
        return "Qtum withdraw wallet"
