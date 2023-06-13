class OkexException(Exception):
    def __init__(self):
        super().__init__(self)


class OkexAPIException(OkexException):
    def __init__(self, status, json):
        if "code" in json.keys():
            self.code = json["code"]
            self.message = json["msg"]
        else:
            self.code = "None"
            self.message = "System error"
        self.status_code = status

    def __str__(self):  # pragma: no cover
        return f"API Request Error(error_code={self.code}): {self.message}"


class OkexRequestException(OkexException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"OkexRequestException: {self.message}"


class OkexParamsException(OkexException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"OkexParamsException: {self.message}"
