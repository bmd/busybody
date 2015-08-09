
class FullContactInterface:
    """
    Abstract class to implement for accessing the FullContact API
    """

    # @param status_map: Mapping for HTTP codes in the context of the FullContact API
    status_map = {
        200: 'OK',
        202: 'ACCEPTED',
        400: 'BAD REQUEST',
        403: 'FORBIDDEN',
        404: 'NOT FOUND',
        405: 'METHOD NOT ALLOWED',
        410: 'GONE (ENDPOINT DEPRECATED)',
        422: 'INVALID REQUEST',
        500: 'SERVER ERROR'
    }

    def __init__(self):
        raise NotImplementedError

    def get_person(self, email):
        raise NotImplementedError
