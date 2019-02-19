# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 18-11-6


"""
== Blockchain ==
callcontract "address" "data" ( address )
getaccountinfo "address"
getbestblockhash
getblock "blockhash" ( verbosity )
getblockchaininfo
getblockcount
getblockhash height
getblockheader "hash" ( verbose )
getchaintips
getchaintxstats ( nblocks blockhash )
getdifficulty
getmempoolancestors txid (verbose)
getmempooldescendants txid (verbose)
getmempoolentry txid
getmempoolinfo
getrawmempool ( verbose )
getstorage "address"
gettransactionreceipt "hash"
gettxout "txid" n ( include_mempool )
gettxoutproof ["txid",...] ( blockhash )
gettxoutsetinfo
listcontracts (start maxDisplay)
preciousblock "blockhash"
pruneblockchain
savemempool
searchlogs <fromBlock> <toBlock> (address) (topics)
verifychain ( checklevel nblocks )
verifytxoutproof "proof"
waitforlogs (fromBlock) (toBlock) (filter) (minconf)

== Control ==
getmemoryinfo ("mode")
help ( "command" )
logging ( <include> <exclude> )
stop
uptime

== Generating ==
generate nblocks ( maxtries )
generatetoaddress nblocks address (maxtries)

== Mining ==
getblocktemplate ( TemplateRequest )
getmininginfo
getnetworkhashps ( nblocks height )
getstakinginfo
getsubsidy [nTarget]
prioritisetransaction <txid> <dummy value> <fee delta>
submitblock "hexdata"  ( "dummy" )

== Network ==
addnode "node" "add|remove|onetry"
clearbanned
disconnectnode "[address]" [nodeid]
getaddednodeinfo ( "node" )
getconnectioncount
getnettotals
getnetworkinfo
getpeerinfo
listbanned
ping
setban "subnet" "add|remove" (bantime) (absolute)
setnetworkactive true|false

== Rawtransactions ==
combinerawtransaction ["hexstring",...]
createrawtransaction [{"txid":"id","vout":n},...] {"address":amount,"data":"hex",...} ( locktime ) ( replaceable )
decoderawtransaction "hexstring" ( iswitness )
decodescript "hexstring"
fromhexaddress "hexaddress"
fundrawtransaction "hexstring" ( options iswitness )
gethexaddress "address"
getrawtransaction "txid" ( verbose "blockhash" )
sendrawtransaction "hexstring" ( allowhighfees )
signrawtransaction "hexstring" ( [{"txid":"id","vout":n,"scriptPubKey":"hex","redeemScript":"hex"},...] ["privatekey1",...] sighashtype )

== Util ==
createmultisig nrequired ["key",...]
estimatefee nblocks
estimatesmartfee conf_target ("estimate_mode")
signmessagewithprivkey "privkey" "message"
validateaddress "address"
verifymessage "address" "signature" "message"

== Wallet ==
abandontransaction "txid"
abortrescan
addmultisigaddress nrequired ["key",...] ( "account" "address_type" )
backupwallet "destination"
bumpfee "txid" ( options )
createcontract "bytecode" (gaslimit gasprice "senderaddress" broadcast)
dumpprivkey "address"
dumpwallet "filename"
encryptwallet "passphrase"
getaccount "address"
getaccountaddress "account"
getaddressesbyaccount "account"
getbalance ( "account" minconf include_watchonly )
getnewaddress ( "account" "address_type" )
getrawchangeaddress ( "address_type" )
getreceivedbyaccount "account" ( minconf )
getreceivedbyaddress "address" ( minconf )
gettransaction "txid" ( include_watchonly ) (waitconf)
getunconfirmedbalance
getwalletinfo
importaddress "address" ( "label" rescan p2sh )
importmulti "requests" ( "options" )
importprivkey "qtumprivkey" ( "label" ) ( rescan )
importprunedfunds
importpubkey "pubkey" ( "label" rescan )
importwallet "filename"
keypoolrefill ( newsize )
listaccounts ( minconf include_watchonly)
listaddressgroupings
listlockunspent
listreceivedbyaccount ( minconf include_empty include_watchonly)
listreceivedbyaddress ( minconf include_empty include_watchonly)
listsinceblock ( "blockhash" target_confirmations include_watchonly include_removed )
listtransactions ( "account" count skip include_watchonly)
listunspent ( minconf maxconf  ["addresses",...] [include_unsafe] [query_options])
listwallets
lockunspent unlock ([{"txid":"txid","vout":n},...])
move "fromaccount" "toaccount" amount ( minconf "comment" )
removeprunedfunds "txid"
rescanblockchain ("start_height") ("stop_height")
reservebalance [<reserve> [amount]]
sendfrom "fromaccount" "toaddress" amount ( minconf "comment" "comment_to" )
sendmany "fromaccount" {"address":amount,...} ( minconf "comment" ["address",...] replaceable conf_target "estimate_mode")
sendmanywithdupes "fromaccount" {"address":amount,...} ( minconf "comment" ["address",...] )
sendtoaddress "address" amount ( "comment" "comment_to" subtractfeefromamount replaceable conf_target "estimate_mode")
sendtocontract "contractaddress" "data" (amount gaslimit gasprice senderaddress broadcast)
setaccount "address" "account"
settxfee amount
signmessage "address" "message"
"""

import json
import pytest
import requests
from common.chain_driver.utils import *

MAIN_NET_PORT = 3889
TEST_NET_PORT = 13889

user = "zxy"
password = "19831116zxy"
host = "127.0.0.1"
port = TEST_NET_PORT
url = 'http://{}:{}@{}:{}'.format(user, password, host, port)
headers = {'content-type': 'application/json'}
timeout = 300


def pytest_namespace():
	return dict(proxy=None)


pytest.proxy = AuthProxy(url, timeout=timeout)


class TestRPC:
	
	def test_help(self):
		method = "help"
		payload = json.dumps({"method": method, "jsonrpc": "2.0"})
		rsp = requests.post(url, data=payload, headers=headers)
		assert rsp.status_code == 200
		# print(rsp.json()['result'])

	def test_help_with_authproxy(self):
		print("block count:", pytest.proxy.help())
	
	def test_getblockcount_with_authproxy(self):
		print("block count:", pytest.proxy.getblockcount())


