import logging
import re
import sys
import unicodecsv as csv
import yaml

from colors import Colors

logger = logging.getLogger(__name__)


class YamlConfigParser:

    @staticmethod
    def read_config(fname):
        """ Read a configuration file and return a dict of settings.

        @param fname: Path to config file
        @return: dict
        """
        logger.info('Reading configuration settings from {}'.format(fname))
        try:
            with open(fname, 'r') as inf:
                cfg = yaml.load(inf)
            logger.debug(Colors.OKGREEN + '  Successfully read config file' + Colors.ENDC)
            return cfg
        except IOError, e:
            logger.error(Colors.FAIL + '  Could not read config file' + Colors.ENDC)
            logger.error(Colors.FAIL + '  ' + str(e) + Colors.ENDC)
            sys.exit(1)


class EmailParser:

    @staticmethod
    def is_valid(email):
        """ Ensure that an email is valid, according to a simple regex

        @param email: email to validate
        @return: bool
        """
        return re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email)

    @classmethod
    def read_emails(cls, fname):
        """ Read and validate a file containing emails to match against the FullContact API

        @param fname: file containing a column named 'email'
        @return: list
        """
        with open(fname, 'rU') as inf:
            return [r['email'] for r in csv.DictReader(inf) if EmailParser.is_valid(r['email'])]
