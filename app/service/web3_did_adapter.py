from toolz.itertoolz import cons
import web3
from web3.contract import Contract
from web3.types import GasPriceStrategy
from app import log, config
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy, slow_gas_price_strategy, medium_gas_price_strategy
import statistics
from app.model import WalletInfo

from pymongo import MongoClient

import json

import requests

LOG = log.get_logger()


class Web3DidAdapter(object):
    PUBLISH_CONTRACT_ABI = [
        {
            "inputs": [],
            "stateMutability": "nonpayable",
            "payable": False,
            "type": "constructor"
        },
        {
            "inputs": [
                {
                    "internalType": "string",
                    "name": "data",
                    "type": "string"
                }
            ],
            "name": "publishDidTransaction",
            "outputs": [],
            "stateMutability": "nonpayable",
            "payable": False,
            "type": "function"
        }
    ]

    def __init__(self):
        self.sidechain_rpc = config.DID_SIDECHAIN_RPC_URL_ETH
        self.contract_address = config.DID_CONTRACT_ADDRESS
        self.chainId = config.DID_CHAIN_ID
        self.did_sidechain_fee = 0.000001

    def create_transaction(self, wallet, nonce, payload):
        try:
            w3 = Web3(Web3.HTTPProvider(self.sidechain_rpc))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            contract: Contract = w3.eth.contract(address=self.contract_address, abi=self.PUBLISH_CONTRACT_ABI)
            pvt_key = w3.eth.account.decrypt(wallet, config.WALLETSV2_PASS)

            wallet_address = Web3.toChecksumAddress(f'0x{json.loads(wallet)["address"]}')

            w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

            if not isinstance(payload, str):
                json_payload = json.dumps(payload)
            else:
                json_payload = payload

            estimated_gas = contract.functions.publishDidTransaction(json_payload).estimateGas({'from': wallet_address})

            cdata = contract.encodeABI(fn_name="publishDidTransaction", args=[json_payload])

            tx = {
                "data": cdata,
                "to": self.contract_address,
                'gas': estimated_gas,
                'gasPrice': w3.eth.gas_price,
                'nonce': nonce,
                'chainId': self.chainId
            }

            signed = w3.eth.account.sign_transaction(tx, pvt_key)

            return signed
        except Exception as e:
            LOG.info(f"Error creating transaction: {str(e)}")
            return None

    def estimate_gas_price(self):
        w3 = Web3(Web3.HTTPProvider(self.sidechain_rpc))
        pending_transactions = w3.provider.make_request("parity_pendingTransactions", [])
        gas_prices = []
        gases = []
        for tx in pending_transactions["result"[:10]]:
            gas_prices.append(int((tx["gasPrice"]), 16))
            gases.append(int((tx["gas"]), 16))

        return statistics.median(gas_prices)

    def increment_nonce(self, wallet_address):

        nonce = 0

        w3 = Web3(Web3.HTTPProvider(self.sidechain_rpc))

        nonce = w3.eth.get_transaction_count(Web3.toChecksumAddress(f"0x{wallet_address}"))

        return nonce
