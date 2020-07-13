from decouple import config

BRAND_NAME = "Assist REST API"

SECRET_KEY = config('SECRET_KEY')

PRODUCTION = config('PRODUCTION', default=False, cast=bool)

LOG_LEVEL = "DEBUG"

DEBUG = True

CRON_INTERVAL = config('CRON_INTERVAL', default=100, cast=int)

MONGO = {
    "DATABASE": config('MONGO_DATABASE'),
    "HOST": config('MONGO_HOST'),
    "PORT": config('MONGO_PORT', default=27017, cast=int),
    "USERNAME": config('MONGO_USERNAME'),
    "PASSWORD": config('MONGO_PASSWORD')
}

SERVICE_STATUS_PENDING = "Pending"
SERVICE_STATUS_PROCESSING = "Processing"
SERVICE_STATUS_QUARANTINE = "Quarantined"
SERVICE_STATUS_COMPLETED = "Completed"

DID_SIDECHAIN_RPC_URL = config('DID_SIDECHAIN_RPC_URL')

# Service Types
SERVICE_DIDPUBLISH = "did_publish"
SERVICE_MEDIAUPLOAD = "media_upload"  # Unused service

# Service Limits
SERVICE_DIDPUBLISH_DAILY_LIMIT = config("DID_PUBLISH_DAILY_LIMIT", default=5, cast=int)

def get_wallets():
    wallets = []
    i = 1
    while True:
        address = config("WALLET{0}_ADDRESS".format(i), default=None)
        private_key = config("WALLET{0}_PRIVATE_KEY".format(i), default=None)
        public_key = config("WALLET{0}_PUBLIC_KEY".format(i), default=None)
        if not address:
            break
        else:
            wallet = {
                "address": address,
                "private_key": private_key,
                "public_key": public_key
            }
            wallets.append(wallet)
        i += 1
    return wallets


# Retrieve wallet details
WALLETS = get_wallets()
NUM_WALLETS = len(WALLETS)

