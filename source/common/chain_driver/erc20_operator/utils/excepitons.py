# encoding=utf-8
"""异常声明模块

@date: 2018.04.29
"""


class EthJsonRpcError(Exception):
    """以太坊jsonrpc错误类
    """
    pass


class BadStatusCodeError(EthJsonRpcError):
    """错误状态码
    """
    pass


class BadJsonError(EthJsonRpcError):
    """错误的json类型转换
    """
    pass


class BadResponseError(EthJsonRpcError):
    """错误的响应结果
    """
    pass


class ConnectionError(EthJsonRpcError):
    """连接异常
    """
    pass


class ERC20Error(Exception):
    """ERC20异常类
    """
    pass


class ERC20ConfigurationError(ERC20Error):
    """ERC20配置错误
    """
    pass
