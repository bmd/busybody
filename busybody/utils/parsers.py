import re
import unicodecsv as csv


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
