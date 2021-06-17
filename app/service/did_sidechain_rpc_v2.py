# -*- coding: utf-8 -*-

from web3.main import Web3
from web3.types import NodeInfo
from app.service.web3_did_adapter import Web3DidAdapter
import base64
import json
import requests

from app import log, config

LOG = log.get_logger()


class DidSidechainRpcV2(object):
    def __init__(self):
        self.sidechain_rpc = config.DID_SIDECHAIN_RPC_URL_ETH
        self.contract_address = config.DID_CONTRACT_ADDRESS

    def get_did_from_cryptoname(self, crypto_name):
        LOG.info("Retrieving DID from cryptoname..")
        try:
           
            crypto_name_url = f"https://{crypto_name}.elastos.name/did"
            response = requests.get(crypto_name_url, timeout=config.REQUEST_TIMEOUT).text
            return response
        except Exception as e:
            LOG.info(f"Error while getting DID from cryptoname: {e}")
            return None

    def get_block_count(self) -> int :
        LOG.info("Get block count...")
        try:
            w3 = Web3(Web3.HTTPProvider(self.sidechain_rpc))
            currentBlock = w3.eth.get_block_number()
            LOG.info("Actual block number: " + str(currentBlock))
            return currentBlock
        except Exception as e:
            LOG.info(f"Error while getting block count: {e}")
            return None

    def get_balance(self, address):
        LOG.info(f"Retrieving current balance on DID sidechain for address {address}")
        balance = 0
        try:
            w3 = Web3(Web3.HTTPProvider(self.sidechain_rpc)) 
            balance = int(w3.eth.get_balance(Web3.toChecksumAddress(address)))

        except Exception as e:
            LOG.info(f"Error while retrieving balance for an address: {e}")
        return balance

    def resolve_did(self, did):
        LOG.info(f"Resolving DID {did} to ensure the DID document is valid...")
        payload = {
            "method": "did_resolveDID",
            "params": [{
                "did": did
            }],
            "id": "1"
        }
        try:
            response = requests.post(self.sidechain_rpc, json=payload, timeout=config.REQUEST_TIMEOUT).json()
            LOG.info(response)
            if response and response["result"]:
                document = response["result"]
        except Exception as e:
            LOG.info(f"Error while resolving DID: {e}")
        return document

    def get_raw_transaction(self, txid):
        LOG.info("Retrieving transaction from the DID sidechain...")
       
        try:
            w3 = Web3(Web3.HTTPProvider(self.sidechain_rpc))
            confirmations = 0
            status = None
            tx = w3.eth.get_transaction_receipt(txid)
            if tx:
                status = tx.get("status")
                currentBlock = w3.eth.get_block_number()
                confirmations = currentBlock - tx.get("blockNumber")
            return {
                "status": status,
                "confirmations": str(confirmations)
            }
        except Exception as e:
            LOG.info(f"Error while getting raw transaction for a txid: {e}")
            return None

    def send_raw_transaction(self, signed_transaction):
        LOG.info("Sending transaction to the DID sidechain...")
      
        try:
            w3 = Web3(Web3.HTTPProvider(self.sidechain_rpc))
            tx = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            return {
                "tx_id": tx.hex(),
                "error": None
            }
        except ValueError as e:
            LOG.info(f"Error while sending transactions to the DID sidechain: {e}")
            return {
                "tx_id": None,
                "error": json.loads(str(e).replace("'",'"'))
            }

    def get_documents_specific_did(self, did):
        documents = {}
        result = self.resolve_did(did)
        if result:
            transactions = result.get("transaction", None)
            if not transactions:
                return documents
            # Only deal with the last 5 DID documents
            for tx in transactions[:5]:
                # Need to add some extra padding so TypeError is not thrown sometimes
                payload = base64.b64decode(tx["operation"]["payload"] + "===").decode("utf-8")
                payload_json = json.loads(payload)

                verifiable_creds = []
                if "verifiableCredential" in payload_json.keys():
                    creds = payload_json["verifiableCredential"]
                    for cred in creds:
                        verifiable_cred = {
                            "id": cred["id"],
                            "issuance_date": cred["issuanceDate"],
                            "subject": cred["credentialSubject"],
                            "expiration_date": cred["expirationDate"],
                            "type": cred["type"]
                        }
                        if "issuer" in cred.keys():
                            verifiable_cred["issuer"] = cred["issuer"]
                        verifiable_creds.append(verifiable_cred)

                documents[tx["txid"]] = {
                    "published": tx["timestamp"],
                    "verifiable_creds": verifiable_creds
                }
        return documents

    