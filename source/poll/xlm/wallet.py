# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-31

from source.poll.wallet_interface import WalletInterface
from source.common.chain_driver.xlm import XlmOP
from source.model.database import Account
import abc


class WalletImpl(WalletInterface):
    def __init__(self, configure):
        self.coin_type = configure.coin_type
        self.tb_address = configure.tb_address
        self.cb_address = configure.cb_address
        rpc_uri = "http://%s:%s" % (configure.rpc_host, configure.rpc_port)
        self.wallet_op = XlmOP(rpc_uri=rpc_uri, timeout=configure.timeout)
    
    def list_transactions(self):
        trans = self.wallet_op.get_operations(self.wallet_address())
        ledgers = self.wallet_op.get_ledgers()
        latest_ledger = ledgers[0].get('sequence', '')
        if not trans:
            raise StopIteration
        for tran in trans:
            tran_ = dict()
            txid = tran['transaction_hash']
            tx_data = self.wallet_op.get_trans_info(txid)
            tran_['txid'] = txid
            tran_['confirmations'] = latest_ledger - tx_data.get('ledger', latest_ledger)
            tran_['destination_tag'] = tx_data['memo']
            tran_['address'] = tran['to']
            tran_['from_address'] = tran['from']
            tran_['fee'] = tran['fee_paid']
            tran_['amount'] = tran['amount']
            yield tran_
    
    def list_transactions_in(self):
        for tran in self.list_transactions():
            if tran["address"] == self.wallet_address():
                yield tran
    
    def list_transactions_out(self):
        for tran in self.list_transactions():
            if tran["from_address"] == self.wallet_address():
                yield tran
    
    def filter_transactions(self, trans):
        pass
    
    def get_transaction(self, txid):
        tx_data = self.wallet_op.get_trans_info(txid)
        return tx_data

    @abc.abstractmethod
    def transfer_to(self, account_address, amount):
        pass
    
    @abc.abstractmethod
    def get_balance(self):
        pass

    @abc.abstractmethod
    def wallet_address(self):
        pass


class WalletRechargeImpl(WalletImpl):
    Account = Account
    
    def __init__(self, configure):
        super().__init__(configure)
        self.cb_address = configure.cb_address
        
    def filter_transactions(self, trans):
        for tran in trans:
            if self.Account.find_one({"coin_type": self.coin_type, 'destination_tag': tran['destination_tag']}):
                yield tran

    def transfer_to(self, account_address, amount):
        return self.wallet_op.create_transaction(self.wallet_address(), account_address, amount,
                                                 'Gather from Recharge Wallet')
    
    def get_balance(self):
        return self.wallet_op.get_balance(self.cb_address)

    def wallet_address(self):
        return self.cb_address


class WalletWithdrawImpl(WalletImpl):
    
    def __init__(self, configure):
        super().__init__(configure)
    
    def filter_transactions(self, trans):
        yield from trans

    def get_balance(self):
        return self.wallet_op.get_balance(self.tb_address)
    
    def wallet_address(self):
        return self.tb_address

    def transfer_to(self, account_address, amount):
        assert 0, "No transfer from WalletWithdraw by this api"
