import falcon
from .createTransaction import CreateTransaction
from .verifyTransaction import VerifyTransaction
from .database      import meta

api = application = falcon.API()

api.add_route('/create', CreateTransaction())
api.add_route('/verify', VerifyTransaction())
