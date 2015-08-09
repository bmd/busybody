
class AbstractDatabaseConnector:
    """
    DBInterface defines the interface for busybody classes
    that interact directly with the applications data store.

    The interface is designed to be generic and provide a
    backend-agnostic way to hook busybody up to data stores.

    Minimally, a child class must override ALL DbInterface's
    methods.
    """
    def __init__(self):
        raise NotImplementedError

    def insert_user_record(self, email, response):
        raise NotImplementedError

    def log_failure(self, email, failure_response):
        raise NotImplementedError
