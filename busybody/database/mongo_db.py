import logging

from ..utils import Colors
from db_interface import AbstractDatabaseConnector

logger = logging.getLogger(__name__)


class MongoDbConnector(AbstractDatabaseConnector):

    def __init__(self, connection_string, collection):
        """ Class for using MongoDb as a backing for BusyBody

        @param connection_string: Address of a mongodb instance
        @param collection: Name of the collection to insert records into
        @return: None
        """
        try:
            from pymongo import MongoClient
        except ImportError:
            print 'BusyBody requires pymongo to be installed to use the MongoDb Connector'
            logger.error(Colors.FAIL + 'BusyBody requires pymongo to be installed to use the MongoDb Connector' + Colors.ENDC)
            raise

        self.client = MongoClient(connection_string)
        self.db = self.client[collection]

    def insert_user_record(self, email, record):
        """ Insert a Person API result into the database

        @param email: Email of the user to insert
        @param record: User record returned by FullContact
        @return: None
        """
        record['email'] = email
        self.db.insert_one(record)

    def log_failure(self, email, failure_response):
        """ Log a failure response in the database

        @param email: Email of the user that was searched
        @param failure_response: Failure response returned by FullContact
        @return: None
        """
        failure_response['email'] = email
        self.db.insert_one(failure_response)
