# -*- coding: utf-8 -*-

from app import log
from app import config

LOG = log.get_logger()

def init_session():
    LOG.info("Connecting to database..")

    mongo.connect(
        config.MONGO['DATABASE'],
        host = config.MONGO['HOST'],
        port = config.MONGO['PORT'],
        username = config.MONGO['USERNAME'],
        password = config.MONGO['PASSWORD']
    )