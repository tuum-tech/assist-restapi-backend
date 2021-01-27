# -*- coding: utf-8 -*-

import json
import falcon

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict


OK = {"status": falcon.HTTP_200, "code": 200}

ERR_UNKNOWN = {"status": falcon.HTTP_500, "code": 500, "title": "Unknown Error"}

ERR_AUTH_REQUIRED = {
    "status": falcon.HTTP_401,
    "code": 99,
    "title": "Authentication Required",
}

ERR_INVALID_PARAMETER = {
    "status": falcon.HTTP_400,
    "code": 88,
    "title": "Invalid Parameter",
}

ERR_DAILY_LIMIT_REACHED = {
    "status": falcon.HTTP_429,
    "code": 77,
    "title": "Daily limit reached",
}

ERR_NOT_FOUND = {"status": falcon.HTTP_404, "code": 10, "title": "No result found"}


ERR_USER_NOT_EXISTS = {
    "status": falcon.HTTP_404,
    "code": 21,
    "title": "User Not Exists",
}


class AppError(Exception):
    def __init__(self, error=ERR_UNKNOWN, description=None):
        self.error = error
        self.error["description"] = description

    @property
    def code(self):
        return self.error["code"]

    @property
    def title(self):
        return self.error["title"]

    @property
    def status(self):
        return self.error["status"]

    @property
    def description(self):
        return self.error["description"]

    @staticmethod
    def handle(exception, req, res, error=None):
        res.status = exception.status
        meta = OrderedDict()
        meta["code"] = exception.code
        meta["message"] = exception.title
        if exception.description:
            meta["description"] = exception.description
        res.body = json.dumps({"meta": meta})


class InvalidParameterError(AppError):
    def __init__(self, description=None):
        super().__init__(ERR_INVALID_PARAMETER)
        self.error["description"] = description


class DailyLimitReachedError(AppError):
    def __init__(self, description=None):
        super().__init__(ERR_DAILY_LIMIT_REACHED)
        self.error["description"] = description


class NotFoundError(AppError):
    def __init__(self, method=None, url=None):
        super().__init__(ERR_NOT_FOUND)
        if method and url:
            self.error["description"] = "method: %s, url: %s" % (method, url)


class UserNotExistsError(AppError):
    def __init__(self, description=None):
        super().__init__(ERR_USER_NOT_EXISTS)
        self.error["description"] = description


class UnauthorizedError(AppError):
    def __init__(self, description=None):
        super().__init__(ERR_AUTH_REQUIRED)
        self.error["description"] = description