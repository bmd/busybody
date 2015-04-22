import json
import sys
import yaml

from busybody.colors import Colors
import unicodecsv as csv
from peewee import *
from playhouse.csv_loader import dump_csv
from playhouse.shortcuts import model_to_dict

from busybody.models import *
from busybody.busybody import BusyBody, SeekableDict


def parse_config_settings(config_file):
    print Colors.BOLD + 'Reading configuration settings ...' + Colors.ENDC,
    try:
        with open(config_file, 'r') as inf:
            cfg = yaml.load(inf)
        print Colors.OKGREEN + 'SUCCESS' + Colors.ENDC
        return cfg
    except IOError, e:
        print Colors.FAIL + 'FAIL' + Colors.ENDC
        print Colors.FAIL + '  ' + str(e) + Colors.ENDC
        sys.exit(1)


def get_user_emails(profiles_csv):
    print Colors.BOLD + 'Reading emails for lookup ...' + Colors.ENDC,

    try:
        with open(profiles_csv, 'r') as inf:
            reader = csv.DictReader(inf)
            profs = [{'email': row['email']} for row in reader]
        print Colors.OKGREEN + 'SUCCESS' + Colors.ENDC
        print '  Got {} addresses to look up'.format(len(profs))
        return profs

    except (IOError, KeyError) as e:
        print Colors.FAIL + 'FAILED' + Colors.ENDC
        print '  ' + Colors.FAIL + str(e) + Colors.ENDC
        sys.exit(1)


if __name__ == '__main__':
    # get app configuration
    cfg = parse_config_settings('config.yaml')

    # read in profiles to search
    emails = get_user_emails('emails.txt')

    # initialize busybody instance
    bb = BusyBody(db, cfg['fc_api_key'])

    """
    # look up users
    for email in emails:
        bb.look_up_user(email['email'])
    """

    # clean up
    bb.dump_failure_table('failures.csv')
    # bb.execute_queued_retries()

    """
    bb.dump_failure_table('failures.csv')
    #r = bb.retry_failures()
    sys.exit()

    with open('bart.json', 'r') as inf:
        users = [SeekableDict(user) for user in json.loads(inf.read())]

    for i, usr in enumerate(users):
        insert_user_data(db, emails[i], usr)
    """