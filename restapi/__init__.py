import falcon
from .createTransaction import CreateTransaction
from .verifyTransaction import VerifyTransaction

from falcon_cors import CORS

cors = CORS(
    allow_all_origins=True,
    allow_all_headers=True,
    allow_all_methods=True)

api = falcon.API(middleware=[cors.middleware])

api.add_route('/create', CreateTransaction())
api.add_route('/verify', VerifyTransaction())
