# -*- coding: utf-8 -*-
import requests

from app import log
import datetime
from app.api.common import BaseResource
from app.model import DidDocument

from app.service import DidSidechainRpc

LOG = log.get_logger()


class GetDidDocumentsFromDid(BaseResource):
    """
    Handle for endpoint: /v1/documents/did/{did}
    """

    def on_get(self, req, res, did):
        LOG.info(f'Enter /v1/documents/did/{did}')
        did_sidechain_rpc = DidSidechainRpc()
        did = did.replace("did:elastos:", "").split("#")[0]

        result = get_did_documents(did_sidechain_rpc, did)

        self.on_success(res, result)


class GetDidDocumentsFromCryptoname(BaseResource):
    """
    Handle for endpoint: /v1/documents/crypto_name/{crypto_name}
    """

    def on_get(self, req, res, crypto_name):
        LOG.info(f'Enter /v1/documents/crypto_name/{crypto_name}')
        did_sidechain_rpc = DidSidechainRpc()
        did = did_sidechain_rpc.get_did_from_cryptoname(crypto_name)

        result = {}
        if did:
            did = did.replace("did:elastos:", "").split("#")[0]
            result = get_did_documents(did_sidechain_rpc, did)

        self.on_success(res, result)


def get_did_documents(did_sidechain_rpc, did):
    result = {}
    rows = DidDocument.objects(did=did)
    if rows:
        row = rows[0]
        row.num_searches += 1
        row.last_searched = datetime.datetime.utcnow()
        row.save()
        result = row.as_dict()
    else:
        documents = did_sidechain_rpc.get_documents_specific_did(did)
        if documents:
            row = DidDocument(
                did=did,
                documents=documents,
                num_searches=1,
                last_searched=datetime.datetime.utcnow()
            )
            row.save()
            result = row.as_dict()
    return result