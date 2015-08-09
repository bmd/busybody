import logging
import tortilla

from fullcontact_interface import FullContactInterface


logger = logging.getLogger(__name__)


class FullContact(FullContactInterface):

    def __init__(self, fc_key, debug=False, style='dictionary'):
        """ Create a FullContact object.

        @param fc_key: API Key for the FullContact API
        @param debug: Debug mode for Tortilla
        @param style: One of 'list' or 'dictionary'. Determines what response type
            should be returned from FullContact.
        @return: None
        """
        self.fc_key = fc_key
        self.style = style

        self.api = tortilla.wrap(
            'https://api.fullcontact.com/v2',
            debug=debug,
            delay=1,
            extension='json'
        )

        logger.debug('Set up FullContact API to return {} using API key {}'.format(style, fc_key))

    def get_person(self, email):
        """ Submits a request to the FullContact person API and return the result.

        @param email: The email of the user to search for
        @return: tortilla.response
        """
        logger.info('Submitting API Request for {}'.format(email))

        response = self.api.person.get(silent=True, params={
            'email': email,
            'apiKey': self.fc_key,
            'style': self.style
        })

        logger.info('API returned a response with status {}'.format(response.status))
        logger.debug(response)

        return response
