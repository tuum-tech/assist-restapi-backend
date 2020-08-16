# -*- coding: utf-8 -*-

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
        did = did.replace("did:elastos:", "").split("#")[0]
        rows = DidDocument.objects(did=did)
        if rows:
            row = rows[0]
            row.num_searches += 1
            row.last_searched = datetime.datetime.utcnow()
        else:
            did_sidechain_rpc = DidSidechainRpc()
            row = DidDocument(
                did=did,
                documents=did_sidechain_rpc.get_documents_specific_did(did),
                num_searches=1,
                last_searched=datetime.datetime.utcnow()
            )
        row.save()
        self.on_success(res, row.as_dict())