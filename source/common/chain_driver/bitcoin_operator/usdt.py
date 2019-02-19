from source.exception import BalanceNotSufficientError
from source.common.chain_driver.bitcoin_operator.btc import BtcOP


class USDTOP(BtcOP):
    def __init__(self, uri, timeout):
        super().__init__(uri, timeout)
        # self.connection = AuthProxy(uri, timeout)
        self.property_id = 31  # 代币的id，USDT为 31

    def get_address_balance(self, address):
        assert isinstance(address, str)
        property_id = self.property_id
        balance_dict = self.connection.omni_getbalance(address, property_id)
        return balance_dict

    def send_usdt(self, from_address, to_address, amount, redeemaddress=''):
        """
        @param from_address: str, 发送地址
        @param to_address: str, 接收地址
        @param amount: str, 数量 ***

        # RPC中可选参数
        @param propertyid: int, 代币的id， USDT为 31
        @param redeemaddress: str, 可以使用这笔交易钱的地址，默认为发送者
        @param referenceamount: str, a bitcoin amount that is sent to the receiver (minimal by default)
        """
        amount = float(amount)
        assert from_address and to_address and amount
        assert isinstance(from_address, str) and isinstance(to_address, str)
        balance = self.get_balance(from_address).get('balance', '0')
        if amount > float(balance):
            raise BalanceNotSufficientError(amount, balance)
        amount = '%.8f' % amount
        # 试过用当前默认钱包用户地址不起作用
        #default_account_address = self.getaccountaddress()
        if redeemaddress:
            tx_hash = self.connection.omni_send(from_address,
                                                to_address,
                                                self.property_id,
                                                amount,
                                                redeemaddress)
        else:
            tx_hash = self.connection.omni_send(from_address,
                                                to_address,
                                                self.property_id,
                                                amount)
        return tx_hash

    def get_transaction(self, txid):
        assert txid and isinstance(txid, str)
        return self.connection.omni_gettransaction(txid)

    def list_transactions(self):
        return self.connection.omni_listtransactions('*', 10000)
