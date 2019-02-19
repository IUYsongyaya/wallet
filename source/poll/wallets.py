# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-2-13
import os
import importlib.util
from source.model.records import WithdrawBalanceRecord
from source.poll.rpc_call import confirm
from source import config
WORKING_PATH = os.path.dirname(__file__)
spec = importlib.util.spec_from_file_location("wallet", f"{WORKING_PATH}/{config.coin_type.lower()}/wallet.py")
wallet_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wallet_module)


class Wallet:
    
    def __init__(self, configure):
        self.configure = configure
        self._coin_type = configure.coin_type
        self._coin_category = configure.coin_category if configure.coin_category else configure.coin_type
        self.confirmation_count = configure.confirmation_count
        
    @property
    def confirm_cnt_touchstone(self):
        return self.confirmation_count
    
    @property
    def coin_type(self):
        return self._coin_type

    @property
    def coin_category(self):
        return self._coin_category


class WalletRecharge(Wallet):
    
    def __init__(self, configure):
        super().__init__(configure)
        self.wallet_impl = wallet_module.WalletRechargeImpl(configure)

    def list_transactions(self):
        return self.wallet_impl.list_transactions()

    def list_transactions_in(self):
        return self.wallet_impl.list_transactions_in()

    def list_transactions_out(self):
        return self.wallet_impl.list_transactions_out()

    def get_transaction(self, txid):
        return self.wallet_impl.get_transaction(txid)

    def filter_transactions(self, trans):
        return self.wallet_impl.filter_transactions(trans)

    def transfer_to(self, account_address, amount):
        return self.wallet_impl.transfer_to(account_address, amount)

    def get_confirmation_count(self, transaction):
        return self.wallet_impl.get_confirmation_count(transaction)

    @staticmethod
    def notify(msg):
        # address = msg.get("address", "")
        # from_address = msg.get("from_address", "")
        # amount = msg.get("amount", "")
        # txid = msg.get("txid", "")
        # coin_type = msg.get("coin_type", "")
        # confirmations = msg.get("confirmations", "")
        # status = msg.get("status", "")
        # destination_tag = msg.get("destination_tag", None)
        # recharge(address, from_address, amount, txid, coin_type, confirmations, status, destination_tag)
        return True
        
    def get_balance(self):
        return self.wallet_impl.get_balance()

    @property
    def balance_max(self):
        return self.configure.cz_max
    
    @property
    def minimum_fee(self):
        return self.configure.fee_min
    
    @property
    def wallet_address(self):
        return self.wallet_impl.wallet_address()


class WalletWithdraw(Wallet):
    
    def __init__(self, configure):
        super().__init__(configure)
        self.wallet_impl = wallet_module.WalletWithdrawImpl(configure)
    
    def list_transactions(self):
        return self.wallet_impl.list_transactions()

    def list_transactions_in(self):
        return self.wallet_impl.list_transactions_in()

    def list_transactions_out(self):
        return self.wallet_impl.list_transactions_out()

    def get_transaction(self, txid):
        return self.wallet_impl.get_transaction(txid)

    def filter_transactions(self, trans):
        return self.wallet_impl.filter_transactions(trans)

    def transfer_to(self, account_address, amount):
        return self.wallet_impl.transfer_to(account_address, amount)
    
    def get_balance(self):
        return self.wallet_impl.get_balance()
    
    def get_confirmation_count(self, transaction):
        return self.wallet_impl.get_confirmation_count(transaction)
    
    @property
    def balance_max(self):
        return self.configure.tb_max
    
    @property
    def wallet_address(self):
        return self.configure.tb_address
    
    @staticmethod
    def notify(msg):
        print("notify ====>", msg)
        return True
        # return confirm(msg["txid"], msg["confirmations"], msg["status"])


class WalletColdRemote(Wallet):
    
    def __init__(self, configure):
        super().__init__(configure)
        self.cw_address = configure.cw_address
    
    @property
    def wallet_address(self):
        return self.cw_address


class WalletWithdrawRemote(Wallet):
    
    def __init__(self, configure):
        super().__init__(configure)
        self.tb_max = self.configure.tb_max
        self.tb_address = self.configure.tb_address
        self.balance_record = WithdrawBalanceRecord(configure)
    
    @property
    def balance_max(self):
        return self.tb_max
    
    @property
    def wallet_address(self):
        return self.tb_address
    
    @property
    def balance(self):
        return self.balance_record.balance


class WalletRechargeRemote(Wallet):
    
    def __init__(self, configure):
        super().__init__(configure)
        self.cb_address = configure.cb_address
    
    @property
    def wallet_address(self):
        return self.cb_address
