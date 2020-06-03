BRAND_NAME = "Assist REST API"

SECRET_KEY = "assist-restapi-secret-key"

LOG_LEVEL = "DEBUG"

DEBUG = True

CRON_INTERVAL = 10

MONGO = {
    "DATABASE": "assistdb",
    "HOST": "localhost",
    "PORT": 27017,
    "USERNAME": "mongoadmin",
    "PASSWORD": "assistmongo"
}

SERVICE_STATUS_PENDING = "Pending"
SERVICE_STATUS_PROCESSING = "Processing"
SERVICE_STATUS_QUARANTINE = "Quarantined"
SERVICE_STATUS_COMPLETED = "Completed"

DID_SIDECHAIN_RPC_URL = "http://localhost:30113"

NUM_WALLETS = 2
WALLET1 = {
    "address": "EKsSQae7goc5oGGxwvgbUxkMsiQhC9ZfJ3",
    "private_key": "1d5fdc0ad6b0b90e212042f850c0ab1e7d9fafcbd7a89e6da8ff64e8e5c490d2",
    "public_key": "03848390f4a687c247f4f662364c142a060ad10a03749178268decf9461b3c0fa5"
}
WALLET2 = {
    "address": "EKsSQae7goc5oGGxwvgbUxkMsiQhC9ZfJ3",
    "private_key": "1d5fdc0ad6b0b90e212042f850c0ab1e7d9fafcbd7a89e6da8ff64e8e5c490d2",
    "public_key": "03848390f4a687c247f4f662364c142a060ad10a03749178268decf9461b3c0fa5"
}
