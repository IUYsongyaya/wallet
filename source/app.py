#!usr/bin/env python
# -*- coding:utf-8 _*-
# @Author  : ymy
# @Time    : 2018/9/4 上午9:58

from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from jsonrpc import JSONRPCResponseManager, dispatcher

from source.option import option


class Adapter(object):
    def __init__(self, coin_type):
        self.coin_type = coin_type
        self.ins = option[self.coin_type]['api_manager']

    def get_address(self, *args, **kwargs):
        return self.ins.get_address(*args, **kwargs)

    def send2address(self, *args, **kwargs):
        return self.ins.send2address(*args, **kwargs)


def get_address(coin_type):
    """生成一个钱包地址

    Args:
        coin_type (str): 币种类型.
    Returns:
        str: 返回新的地址

    Examples::

        zcbasfjwh98hh
    """
    coin_type = coin_type.upper()
    adapter = Adapter(coin_type)
    return adapter.get_address()


def send2address(address, amount, coin_type='', **kwargs):
    """
    提币请求

    Args:
        address (str): 接收方地址.
        amount (float): 数量.
        coin_type (str): 币种名称, 以太坊代币需要该参数.
    Returns:
        string: 交易哈希

    Examples::

        txsaud9saghos8
    """
    coin_type = coin_type.upper()
    adapter = Adapter(coin_type)
    return adapter.send2address(address, amount, coin_type, **kwargs)


@Request.application
def application(request):
    dispatcher["get_address"] = get_address
    dispatcher["sendtoaddress"] = send2address

    response = JSONRPCResponseManager.handle(
        request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


if __name__ == '__main__':
    run_simple('localhost', 4000, application)
