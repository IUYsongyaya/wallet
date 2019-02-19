# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-31
import abc


class WalletInterface(abc.ABC):
    
    @abc.abstractmethod
    def list_transactions(self):
        pass
    
    @abc.abstractmethod
    def list_transactions_in(self):
        pass
    
    @abc.abstractmethod
    def list_transactions_out(self):
        pass
    
    @abc.abstractmethod
    def get_balance(self):
        pass
    
    @abc.abstractmethod
    def get_transaction(self, txid):
        pass

    @abc.abstractmethod
    def filter_transactions(self, trans):
        pass

    @abc.abstractmethod
    def transfer_to(self, account_address, amount):
        pass

    @abc.abstractmethod
    def wallet_address(self):
        pass


