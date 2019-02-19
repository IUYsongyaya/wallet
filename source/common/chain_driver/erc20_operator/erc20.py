# encoding=utf-8
"""erc20: ERC20Token基础模块

@date: 2018.04.27
@last_modified: 2018.04.30
"""
import re
from decimal import Decimal

import rlp
from web3 import Web3
from eth_keys import keys
from eth_utils import encode_hex
from ethereum.transactions import Transaction
from ethereum.abi import encode_abi, decode_abi
from eth_keys.exceptions import ValidationError
from web3.utils.transactions import get_buffered_gas_estimate
from web3.utils.validation import validate_abi, validate_address
from web3.utils.encoding import (hexstr_if_str, to_bytes)

from .abi import ERC20_ABI, ERC20_TRANSFER_ABI_PREFIX
from .provider import RetryHTTPProvider
from .utils.keyfile_op import load_keyfile
from .utils.tools import to_unit, from_unit
from .utils.excepitons import ERC20ConfigurationError
from .const import DEFAULT_GAS_PRICE, DEFAULT_GAS_PER_TX


class TransactionData(object):
    """交易数据模型
    """
    from_address = None
    to_address = None
    token_address = None
    ether_amount = 0
    token_amount = 0
    num_confirmations = -1


class ERC20Token(object):
    """erc20token基础封装
    """

    def __init__(self,
                 ipc_path='',
                 address=None,
                 provider_endpoint='',
                 contract_address='',
                 contract_abi=ERC20_ABI,
                 gas_price=None,
                 gas_limit=None,
                 password='',
                 private_key='',
                 keyfile=''):
        provider = self._get_provider(provider_endpoint, ipc_path)
        try:
            validate_abi(contract_abi)
        except BaseException:
            raise ERC20ConfigurationError('abi配置异常')

        if gas_price and not (isinstance(gas_price, int)
                              or isinstance(gas_price, float)):
            raise ERC20ConfigurationError('gas price 必须为int or float')

        if gas_limit and not isinstance(gas_limit, int):
            raise ERC20ConfigurationError('gat limit 必须分为int')

        self.web3 = Web3(provider)
        if not self.web3.isConnected():
            raise ERC20ConfigurationError('不能连接到 provider endpoint')
        self.token_contract = self.web3.eth.contract(
            self.web3.toChecksumAddress(contract_address),
            abi=contract_abi) if contract_address else None
        self.address = address
        self.private_key = private_key

        if keyfile:
            try:
                self.private_key = load_keyfile(keyfile, password)
            except Exception as e:
                raise ERC20ConfigurationError(f'不能加载私钥文件: {str(e)}')
        if self.private_key:
            try:
                private_key_bytes = hexstr_if_str(to_bytes, self.private_key)
                pk = keys.PrivateKey(private_key_bytes)
                self.address = self.web3.eth.defaultAccount = pk.public_key.to_checksum_address(
                )
            except ValidationError as e:
                raise ERC20ConfigurationError(f'不能加载私钥: {str(e)}')

        if self.private_key:
            self._tx_manager = TransactionManager(
                self.web3, self.private_key, self.address, gas_price, gas_limit, password)

    def get_block_number(self):
        """获取当前区块号
        """
        return int(self.web3.eth.blockNumber)

    def get_block(self, block_num: int):
        """获取指定区块信息
        """
        return self.web3.eth.getBlock(block_num)

    def get_block_tx_id_list(self, block_num: int):
        """获取指定区块号上所有交易id
        """
        return self.web3.eth.getBlock(block_num).get('transactions')

    def get_ether_balance(self):
        """获取钱包ether余额
        """
        if not self.address:
            raise ERC20ConfigurationError('私钥配置异常')
        return self.web3.fromWei(
            self.web3.eth.getBalance(self.address), 'ether')

    def get_token_balance(self):
        """获取钱包token余额
        """
        if not self.address:
            raise ERC20ConfigurationError('私钥配置异常')
        return self.web3.fromWei(self.token_contract.call().balanceOf(
            self.address), 'ether')

    def get_address_ether_balance(self, address):
        """获取指定公钥地址的余额
        """
        address = self.web3.toChecksumAddress(address)
        validate_address(address)
        return self.web3.fromWei(self.web3.eth.getBalance(address), 'ether')

    def get_address_token_balance(self, address, unit):
        """获取指定公钥地址的余额
        """
        address = self.web3.toChecksumAddress(address)
        validate_address(address)
        return from_unit(self.token_contract.call().balanceOf(address), unit)

    def send_ether(self, address, amount):
        """从钱包中发起一笔ether交易到指定地址
        """
        if not self.address:
            raise ERC20ConfigurationError('私钥配置异常')
        address = self.web3.toChecksumAddress(address)
        validate_address(address)
        if amount <= 0:
            raise ValueError('amount must be positive')
        return self._tx_manager.send_transaction(address, amount)

    def send_tokens(self, address, amount, uint):
        """从钱包中发起一笔代币交易导致定地址
        """
        if not self.address:
            raise ERC20ConfigurationError('私钥配置异常')
        address = self.web3.toChecksumAddress(address)
        validate_address(address)
        if amount <= 0:
            raise ValueError('amount must be positive')
        hex_data = self._encode_transaction_data(
            'transfer', params=[address, to_unit(amount, uint)])
        data = hexstr_if_str(to_bytes, hex_data)
        return self._tx_manager.send_transaction(self.token_contract.address,
                                                 0, uint, data)

    def get_transaction_data(self, tx_id, unit=None):
        """获取提供的交易ID的交易数据
        """
        tx_data = TransactionData()
        try:
            tx = self.web3.eth.getTransaction(tx_id)
            if not tx:
                return tx_data
            tx_data.from_address = tx['from']
            tx_data.to_address = tx['to']
            tx_data.ether_amount = self.web3.fromWei(tx['value'], 'ether')
            if not tx.get('blockNumber'):
                tx_data.num_confirmations = 0
            else:
                tx_block_number = int(tx['blockNumber'])
                cur_block_number = int(self.web3.eth.blockNumber)
                tx_data.num_confirmations = cur_block_number - tx_block_number + 1
                tx_data.block_hash = tx['blockHash']
                tx_data.block_num = tx_block_number
            tx_input = tx.get('input')
            if tx_input and (tx_input.lower().startswith(
                    ERC20_TRANSFER_ABI_PREFIX.lower())):
                to, amount = decode_abi(['address', 'uint256'], hexstr_if_str(
                    to_bytes, tx_input[len(ERC20_TRANSFER_ABI_PREFIX):]))
                tx_data.to_address = self.web3.toChecksumAddress(to)
                tx_data.token_amount = from_unit(amount, unit) if unit else Decimal(str(amount))
                tx_data.token_address = tx['to']
        except BaseException:
            pass
        return tx_data

    def get_transaction(self, tx_id):
        """获取交易信息
        """
        return self.web3.eth.getTransaction(tx_id)

    def get_transaction_receipt(self, tx_id):
        """获取交易收据数据
        """
        return self.web3.eth.getTransactionReceipt(tx_id)

    def _encode_transaction_data(self, func, params):
        """ABI编码工具函数
        """
        data_perfix = ERC20_TRANSFER_ABI_PREFIX
        data = encode_abi(['address', 'uint256'], params).hex()
        res = f'{data_perfix}{data}' if data_perfix.startswith(
            '0x') else f'0x{data_perfix}{data}'
        return res

    def _get_provider(self, provider_endpoint='', ipc_path=''):
        """provider配置
        """
        try:
            if provider_endpoint:
                return RetryHTTPProvider(provider_endpoint)
            if ipc_path:
                return Web3.IPCProvider(ipc_path=ipc_path, timeout=60)
        except BaseException:
            raise ERC20ConfigurationError('配置provider异常')

    def is_success(self, tx):
        """判断是否成功
        """
        # 拜占庭 fork 后有个 status 字段
        receipt = self.get_transaction_receipt(tx['hash'])
        if not receipt:
            return False
        if 'status' in receipt:
            return receipt['status'] in ('0x1', 1)
        if not receipt['blockNumber']:
            # 尚未被包含进 block
            return False
        gas_left = tx['gas'] - receipt['gasUsed']
        if gas_left > 0:
            # gas 未用完
            return True
        elif gas_left < 0:
            return False

        try:
            resp = self.web3.manager.request_blocking(
                'debug_traceTransaction', [tx['hash']])
        except Exception as e:
            print(f'debug_traceTransaction({tx["hash"]}): {e}')
            return False

        if len(resp.get('structLogs', [])) > 0:
            err = resp['structLogs'][-1]['error'].lower()
            if re.search(r'out of gas|invalid jump destination', err):
                return False
        return True


class ERC20TokenChild(ERC20Token):
    """兼容子钱包的sendRawTranscation
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send_ether(self, address, amount):
        """从钱包中发起一笔ether交易到指定地址
        """
        if not self.address:
            raise ERC20ConfigurationError('私钥配置异常')
        address = self.web3.toChecksumAddress(address)
        validate_address(address)
        if amount <= 0:
            raise ValueError('amount must be positive')
        return self._tx_manager.send_raw_transaction(address, amount)

    def send_tokens(self, address, amount, uint):
        """从钱包中发起一笔代币交易导致定地址
        """
        if not self.address:
            raise ERC20ConfigurationError('私钥配置异常')
        address = self.web3.toChecksumAddress(address)
        validate_address(address)
        if amount <= 0:
            raise ValueError('amount must be positive')
        hex_data = self._encode_transaction_data(
            'transfer', params=[address, to_unit(amount, uint)])
        data = hexstr_if_str(to_bytes, hex_data)
        return self._tx_manager.send_raw_transaction(
            self.token_contract.address, 0, uint, data)


class TransactionManager(object):
    """交易管理
    """

    def __init__(
            self,
            web3,
            private_key,
            address,
            gas_price,
            gas_limit,
            password):
        self.web3 = web3
        self.private_key = private_key
        self.address = address
        self.local_nonce = self.web3.eth.getTransactionCount(self.address)
        self.gas_limit = gas_limit
        self.password = password

        if gas_price:
            self.gas_price = int(gas_price * 10**9)
        else:
            self.gas_price = DEFAULT_GAS_PRICE or self.web3.eth.gasPrice

    def send_transaction(self, address, amount, unit=None, data=bytes()):
        """发送交易
        """
        value = to_unit(amount, unit) if unit else self.web3.toWei(
            amount, 'ether')
        params = {
            'to': address,
            'from': self.address,
            'value': value,
            'gasPrice': self.gas_price,
            'gas': self.estimate_tx_gas({
                'to': address,
                'from': self.address,
                'value': value,
                'data': data
            })
        }
        if amount == 0:
            params['data'] = data
        self.web3.personal.unlockAccount(self.address, self.password, 10)
        tx_id = self.web3.eth.sendTransaction(params)

        return tx_id.hex()

    def send_raw_transaction(self, address, amount, unit=None, data=bytes()):
        """发送raw交易
        """
        remote_nonce = self.web3.eth.getTransactionCount(
            self.address, 'pending')
        nonce = max(self.local_nonce, remote_nonce)
        value = to_unit(amount, unit) if unit else self.web3.toWei(
            amount, 'ether')
        tx = Transaction(
            nonce=nonce,
            gasprice=self.gas_price,
            startgas=self.estimate_tx_gas({
                'to': address,
                'from': self.address,
                'value': value,
                'data': data
            }),
            to=address,
            value=value,
            data=data,
        )
        signed_tx = tx.sign(self.private_key)
        raw_tx_hex = self.web3.toHex(rlp.encode(signed_tx))
        tx_id = self.web3.eth.sendRawTransaction(raw_tx_hex)
        # send successful, increment nonce.
        self.local_nonce = nonce + 1
        return tx_id.hex()

    def estimate_tx_gas(self, tx):
        """
        估算交易gas。
        如果有预定义的限制，请将其返回。
        否则要求API估算gas并增加一个安全缓冲区。
        """
        if self.gas_limit:
            return self.gas_limit
        gas_buffer = 10000 if tx.get('data') else 5000
        try:
            if tx['data']:
                tx['data'] = encode_hex(tx['data'])
            return get_buffered_gas_estimate(
                self.web3, tx, gas_buffer=gas_buffer)
        except Exception:
            return DEFAULT_GAS_PER_TX
