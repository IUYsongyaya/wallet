# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-31
import abc
from source import config
from source.poll.wallet_interface import WalletInterface
from source.common.chain_driver.erc20_operator.erc20 import ERC20Token, ERC20TokenChild, TransactionManager
from source.model.records import CoinSettingRecord, BlockInfoRecord, RecordNotFound
from source.model.database import Account
from source.common.chain_driver.utils import JSONRPCException
from web3.utils.validation import validate_address
from web3.utils.encoding import hexstr_if_str, to_hex
from source.common.utils.log import get_logger

EmptyTransaction = dict(confirmations=0)
logger = get_logger('eth-wallet')


class WalletImpl(WalletInterface):
    
    CoinSettingRecord = CoinSettingRecord
    Account = Account
    
    def __init__(self, configure):
        self.coin_type = configure.coin_type
        self.block_record = BlockInfoRecord(configure)
        self.token_address = CoinSettingRecord(configure).token_address
        self.wallet_op = ERC20Token()
        self.tb_address = configure.tb_address
        self.confirmation_count = configure.confirmation_count
        try:
            self.block_num, self.block_hash = self.block_record.retrieve_head_block()
        except RecordNotFound as e:
            logger.exception(e)
            self.block_num, self.block_hash = self._retrieve_head_block()
    
    def _retrieve_head_block(self):
        while True:
            try:
                block_num = self.wallet_op.get_block_number()
                block_ = self.wallet_op.get_block(block_num)
            except Exception as e:
                logger.exception(e)
            else:
                block_['hash'] = hexstr_if_str(to_hex, block_['hash'])
                return block_
    
    def list_transactions(self):
        while True:
            next_ = self.wallet_op.get_block(self.block_num + 1)
            if not next_:
                raise StopIteration
        
            # check chain block_record conformity
            if hexstr_if_str(to_hex, next_['parentHash']) == self.block_hash:
                self.block_num = int(next_['number'])
                self.block_hash = int(next_['hash'])
            else:
                rollback_num = self.block_num - self.confirmation_count
                rollback_ = self.wallet_op.get_block(rollback_num)
                self.block_num = hexstr_if_str(to_hex, rollback_['number'])
                self.block_hash = hexstr_if_str(to_hex, rollback_['hash'])
        
            txids = self.wallet_op.get_block_tx_id_list(self.block_num)
            for txid in txids:
                tran = self.wallet_op.get_transaction_data(txid)
                yield tran
        
            self.block_record.save_head_block(dict(block_num=self.block_num, block_hash=self.block_hash))

    def list_transactions_in(self):
        for tran in self.list_transactions():
            if tran["category"] == "receive":
                yield tran
    
    def list_transactions_out(self):
        for tran in self.list_transactions():
            if tran["category"] == "send":
                yield tran
    
    def get_transaction(self, txid):
        try:
            tran = self.wallet_op.get_transaction(txid)
        except JSONRPCException as e:
            tran = EmptyTransaction
            # logger.error("No such transaction by txid:", txid)
            # logger.exception(e)
        return tran
    
    def get_balance(self):
        raise Exception("No get balance for eth by wallet")
    
    def transfer_to(self, account_address, amount):
        raise Exception("No transfer to for eth by wallet")

    def list_sub_accounts(self):
        sub_accounts = self.Account.find({"coin_type": self.coin_type, "is_used": True})
        if not sub_accounts:
            raise StopIteration
        for s in sub_accounts:
            yield SubAccount(self, s.to_dict())


class SubAccount:
    
    def __init__(self, wallet_impl, account_info):
        self.wallet_impl = wallet_impl
        self.web3 = wallet_impl.wallet_op.web3
        self.private_hash = account_info['private_hash']
        self.destination_tag = account_info['destination_tag']
        self.pub_address = account_info['pub_address']
        self.password = account_info['password']
        validate_address(self.web3.toChecksumAddress(self.pub_address))
        self.transfer_op = TransactionManager(self.web3,
                                              private_key=self.private_hash,
                                              address=self.pub_address,
                                              password=self.password)

    def transfer_to(self, account_address, amount):
        address = self.web3.toChecksumAddress(account_address)
        validate_address(address)
        if amount <= 0:
            raise ValueError('amount must be positive')
        return self.transfer_op.send_transaction(address, amount)
    
    def get_balance(self):
        return self.wallet_impl.wallet_op.get_address_ether_balance(self.pub_address)
    

class WalletRechargeImpl(WalletImpl):
    Account = Account
    
    def __init__(self, configure):
        super().__init__(configure)
    
    def filter_transactions(self, trans):
        for tran in trans:
            if self.Account.find_one({'pub_address': tran["address"], "coin_type": self.coin_type}):
                if tran['from_address'] != self.tb_address:
                    yield tran
    
    def wallet_address(self):
        return "Eth recharge wallet"

    def get_balance(self):
        raise Exception("No get balance for Eth Wallet")

    def transfer_to(self, account_address, amount):
        raise Exception("No transfer to for Eth Wallet")


class WalletWithdrawImpl(WalletImpl):
    
    def __init__(self, configure):
        super().__init__(configure)
    
    def filter_transactions(self, trans):
        yield from trans
    
    def wallet_address(self):
        return "Eth withdraw wallet"

    def get_balance(self):
        raise Exception("No get balance for Eth Wallet")

    def transfer_to(self, account_address, amount):
        raise Exception("No transfer to for Eth Wallet")