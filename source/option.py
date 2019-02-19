# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-23 下午2:39

from source.api.eth import Eth
from source.api.etc import Etc
from source.api.btc import Btc
from source.api.bch import Bch
from source.api.qtum import Qtum
from source.common.address_manager import ErcManager
from source.common.address_manager import BchManager
from source.common.address_manager import BtcManager
from source.common.address_manager import QtumManager
from source.common.address_manager import EtcManager


option = dict()

option['ETH'] = {'api_manager': Eth('ETH'), 'address_class': ErcManager}
option['BTC'] = {'api_manager': Btc(), 'address_class': BtcManager}
option['BCH'] = {'api_manager': Bch(), 'address_class': BchManager}
option['ETC'] = {'api_manager': Etc(), 'address_class': EtcManager}
option['QTUM'] = {'api_manager': Qtum(), 'address_class': QtumManager}

# add other coin config
# ...
# ...
