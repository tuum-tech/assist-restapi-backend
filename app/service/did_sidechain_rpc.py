# -*- coding: utf-8 -*-

import base64
import json
import requests

from app import log, config

LOG = log.get_logger()


class DidSidechainRpc(object):

    def __init__(self):
        self.did_sidechain_rpc_url = config.DID_SIDECHAIN_RPC_URL

    def get_did_from_cryptoname(self, crypto_name):
        LOG.info("Retrieving DID from cryptoname..")
        try:
            crypto_name_url = f"https://{crypto_name}.elastos.name/did"
            response = requests.get(crypto_name_url, timeout=config.REQUEST_TIMEOUT).text
            return response
        except Exception as e:
            LOG.info(f"Error while getting DID from cryptoname: {e}")
            return None

    def get_block_count(self):
        LOG.info("Retrieving current block count..")
        payload = {
            "method": "getblockcount",
        }
        try:
            response = requests.post(self.did_sidechain_rpc_url, json=payload, timeout=config.REQUEST_TIMEOUT).json()
            return response
        except Exception as e:
            LOG.info(f"Error while getting block count: {e}")
            return None

    def get_balance(self, address):
        LOG.info("Retrieving current balance on DID sidechain..")
        payload = {
            "method": "getreceivedbyaddress",
            "params": {"address": address}
        }
        balance = 0
        try:
            response = requests.post(self.did_sidechain_rpc_url, json=payload, timeout=config.REQUEST_TIMEOUT).json()
            if response and response["result"]:
                balance = response["result"]
        except Exception as e:
            LOG.info(f"Error while retrieving balance for an address: {e}")
        return balance

    def resolve_did(self, did):
        LOG.info("Resolving DID to ensure the DID document is valid...")
        payload = {
            "method": "resolvedid",
            "params": {
                "did": did,
                "all": True
            }
        }
        document = {}
        try:
            response = requests.post(self.did_sidechain_rpc_url, json=payload, timeout=config.REQUEST_TIMEOUT).json()
            if response and response["result"]:
                document = response["result"]
        except Exception as e:
            LOG.info(f"Error while resolving DID: {e}")
        return document

    def get_raw_transaction(self, txid):
        LOG.info("Retrieving transaction from the DID sidechain...")
        payload = {
            "method": "getrawtransaction",
            "params": {
                "txid": txid,
                "verbose": True
            }
        }
        try:
            response = requests.post(self.did_sidechain_rpc_url, json=payload, timeout=config.REQUEST_TIMEOUT).json()
            return response
        except Exception as e:
            LOG.info(f"Error while getting raw transaction for a txid: {e}")
            return None

    def send_raw_transaction(self, transactions):
        LOG.info("Sending transactions to the DID sidechain...")
        payload = {
            "method": "sendrawtransaction",
            "params": transactions
        }
        try:
            response = requests.post(self.did_sidechain_rpc_url, json=payload, timeout=config.REQUEST_TIMEOUT).json()
            return response
        except Exception as e:
            LOG.info(f"Error while sending transactions to the DID sidechain: {e}")
            return None

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

    def get_utxos(self, addresses):
        payload = {
            "method": "listunspent",
            "params": {
                "addresses": addresses
            }
        }
        try:
            response = requests.post(self.did_sidechain_rpc_url, json=payload, timeout=config.REQUEST_TIMEOUT).json()
            lowest_value = 0
            for x in response["result"]:
                if (float(x["amount"]) > 0.000001) and (lowest_value == 0 or (float(x["amount"]) < lowest_value)):
                    lowest_value = float(x["amount"])
                    selected_response = x
            return selected_response["txid"], selected_response["assetid"], selected_response["amount"], selected_response[
                "vout"]
        except Exception as e:
            LOG.info(f"Error while getting UTXOs from the DID sidechain: {e}")
            return None, None, None, None