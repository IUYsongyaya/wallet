# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-23 下午3:09

from abc import ABC, abstractmethod


class BaseAPI(ABC):

    def __init__(self, coin_type):
        self.coin_type = coin_type

    @abstractmethod
    def get_address(self, *args, **kwargs):
        """"""

    @abstractmethod
    def send2address(self, *args, **kwargs):
        """"""
