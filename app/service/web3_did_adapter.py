from toolz.itertoolz import cons
from web3.contract import Contract
from app import log, config
from web3 import Web3

from app.model import WalletInfo

from pymongo import MongoClient

import json

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
        self.sidechain_rpc = config.DID_SIDECHAIN_RPC_URL
        self.contract_address = config.DID_CONTRACT_ADDRESS
        self.chainId = config.DID_CHAIN_ID
        self.did_sidechain_fee = 0.000001

    def create_transaction(self, wallet, nonce, payload):
        try:
            w3 = Web3(Web3.HTTPProvider(self.sidechain_rpc))
            contract: Contract = w3.eth.contract(address=self.contract_address, abi=self.PUBLISH_CONTRACT_ABI)
            pvt_key = w3.eth.account.decrypt(wallet, "password")

            if not isinstance(payload, str):
                json_payload = json.dumps(payload)
            else:
                json_payload = payload

            cdata = contract.encodeABI(fn_name="publishDidTransaction", args=[json_payload])

            tx = {
                "data": cdata,
                "to": self.contract_address,
                'gas': 3000000,
                'gasPrice': w3.toWei('1', 'gwei'),
                'nonce': nonce,
                'chainId': self.chainId
            }

            signed = w3.eth.account.sign_transaction(tx, pvt_key)

            return signed
        except Exception as e:
            LOG.info(f"Error creating transaction: {str(e)}")
            return None

    def increment_nonce(self, wallet_address):

        nonce = 0
        wallet_info = WalletInfo.objects(address=wallet_address)

        if len(wallet_info) == 0:
            row = WalletInfo(address=wallet_address)
        else:
            row = wallet_info[0]
            nonce = row.nonce + 1

        row.nonce = nonce
        row.save()

        LOG.info("New nonce: " + str(nonce))

        return nonce
