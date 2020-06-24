from decouple import config

BRAND_NAME = "Assist REST API"

SECRET_KEY = config('SECRET_KEY')

LOG_LEVEL = "DEBUG"

DEBUG = True

CRON_INTERVAL = 10

MONGO = {
    "DATABASE": config('MONGO_DATABASE'),
    "HOST": config('MONGO_HOST'),
    "PORT": config('MONGO_PORT'),
    "USERNAME": config('MONGO_USERNAME'),
    "PASSWORD": config('MONGO_PASSWORD')
}

SERVICE_STATUS_PENDING = "Pending"
SERVICE_STATUS_PROCESSING = "Processing"
SERVICE_STATUS_QUARANTINE = "Quarantined"
SERVICE_STATUS_COMPLETED = "Completed"

DID_SIDECHAIN_RPC_URL = config('DID_SIDECHAIN_RPC_URL')

def get_wallets():
    wallets = []
    i = 1
    while(True):
        address = config("WALLET{0}_ADDRESS".format(i), default=None)
        private_key = config("WALLET{0}_PRIVATE_KEY".format(i), default=None)
        public_key = config("WALLET{0}_PUBLIC_KEY".format(i), default=None)
        if(not address):
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