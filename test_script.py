import logging
import argparse
import json

from busybody import *

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='logs/testing.log',
    filemode='a'
)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

logger = logging.getLogger(__name__)
logger.addHandler(console)


if __name__ == '__main__':
    # run the script
    logger.info("-------------------------------------")
    logger.info("| BUSYBODY")
    logger.info("-------------------------------------")

    # set up argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()

    # configuration options
    cfg = YamlConfigParser.read_config('config.yaml')
    fname = args.input

    # read the file and strip out invalid emails
    logger.info('Reading user data to scrape from file {}'.format(fname))
    emails = EmailParser.read_emails(fname)
    logger.debug(Colors.OKGREEN + "  Got {0} valid emails to process".format(len(emails)) + Colors.ENDC)

    # construct BusyBody object
    logger.debug('Constructing BusyBody')
    db = SqliteConnector('busybody.sqlite')
    api = FullContact(cfg['fc_api_key'])
    bb = BusyBodyFactory.construct(db, api)

    # bb.process_person('micahlwilson@gmail.com')

    # read an example email
    with open('bart.json', 'r') as inf:
        bart_sample = [SeekableDict(j) for j in json.load(inf)]

    # insert test record
    logger.info('Inserting test user records')
    db.insert_user_record('salil.kalia@gmail.com', bart_sample[1])
    db.insert_user_record('bart@fullcontact.com', bart_sample[0])
    db.insert_user_record('b.maionedowning@gmail.com', bart_sample[2])
    db.insert_user_record('micahlwilson@gmail.com', bart_sample[3])
