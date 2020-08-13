# -*- coding: utf-8 -*-
import base64
import jwt
import json

from app.model import DidDocument


def get_documents_specific_did(did_publish, did):
    documents = {}
    response = did_publish.get_previous_did_document(did)
    if response["result"]:
        transactions = response["result"]["transaction"]
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
