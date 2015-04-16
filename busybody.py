import tortilla

from peewee import *
from models import *


class BusyBody(object):
    """A BusyBody Instance"""

    def __init__(self, db, fc_key, debug_setting=False, style='dictionary'):
        self.conn = db
        self.fullcontact = fc_key
        self.api = tortilla.wrap('https://api.fullcontact.com/v2', debug=debug_setting, extension='json')
        self.retry_queue = []
        self.style = style

    def dump_queued_retries(self):
        pass

    def execute_queued_retries(self):
        pass

    def match_user_data(self, user_obj):
        """ Query the FullContact API for a single user """
        response = self.fullcontact.person.get(params={
            user_obj['key']: user_obj['key'],
            'apiKey': self.fullcontact,
            'style': self.style
        })

        if response['status'] == 200:
            # success
            pass
        elif response['status'] == 202:
            # add to retry queue
            pass
        elif response['status'] == 403:
            # not authorized - need to bail
            pass
        elif response['status'] == 404:
            # not found - add to failed lookups
            pass
        else:  # shouldn't have unhandled cases?
            pass

    def insert_user_data_object(self, email, user_obj):
        pass


if __name__ == '__main__':
    print 'Testing Execution'
    print db
