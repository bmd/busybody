import tortilla
import unicodecsv as csv
import json
from peewee import *
from playhouse.csv_loader import dump_csv
from models import *
from colors import Colors


class SeekableDict(dict):
    """
    See if an arbitrarily deep key exists without commiting to the
    existance of any of its parent keys.

    It's not quite like a defaultdict, but it's not quite not a
    defaultdict either.
    """

    def seek(d, *keys, **kwargs):
        default = kwargs.get('default', None)
        cur_key = d
        try:
            for k in keys:
                cur_key = cur_key[k]
            return cur_key
        except KeyError:
            return default


class BusyBody(object):
    """A BusyBody Instance"""

    status_map = {
        200: 'OK',
        202: 'ACCEPTED',
        400: 'BAD REQUEST',
        403: 'FORBIDDEN',
        404: 'NOT FOUND',
        405: 'METHOD NOT ALLOWED',
        410: 'GONE - ENDPOINT DEPRECATED',
        422: 'INVALID',
        500: 'SERVER ERROR'
    }

    def __init__(self, db, fc_key, debug_setting=False, style='dictionary'):
        self.conn = db
        self.fullcontact = fc_key
        self.api = tortilla.wrap('https://api.fullcontact.com/v2', debug=debug_setting, delay=1, extension='json')
        self.retries = []
        self.failures = []
        self.style = style
        self.debugging = debug_setting

    def requeue(self, user, response):
        self.retry_queue.append({'user': user, 'returned_status': response['status']})

    def dump_queued_retries(self, path):
        with open(path, 'w') as outf:
            writer = csv.writer(outf)
            writer.writerow(['email', 'requeue_reason'])
            writer.writerows([[user['email'], user['returned_status']] for user in self.retries])

    def dump_failed_queue(self, path):
        with open(path, 'w') as outf:
            writer = csv.writer(outf)
            writer.writerow(['email', 'fail_reason'])
            writer.writerows([[user['email'], user['returned_status']] for user in self.failures])

    def execute_queued_retries(self):
        pass

    def insert_user_rows(self, email, user):
        user_obj = User.create(
            email=email,
            first_name=user.seek('contactInfo', 'givenName'),
            last_name=user.seek('contactInfo', 'familyName'),
            match_likelihood=user.seek('likelihood')
        )

        UserAddress.create(
            user=user_obj,
            location_general=user.seek('demographics', 'locationGeneral'),
            city_name=user.seek('demographics', 'locationDeduced', 'city', 'name'),
            city_is_deduced=user.seek('demographics', 'locationDeduced', 'city', 'deduced'),
            county_name=user.seek('demographics', 'locationDeduced', 'county', 'name'),
            county_is_deduced=user.seek('demographics', 'locationDeduced', 'county', 'deduced'),
            state_name=user.seek('demographics', 'locationDeduced', 'state', 'name'),
            state_code=user.seek('demographics', 'locationDeduced', 'state', 'code'),
            state_is_deduced=user.seek('demographics', 'locationDeduced', 'state', 'deduced'),
            country_name=user.seek('demographics', 'locationDeduced', 'country', 'name'),
            country_code=user.seek('demographics', 'locationDeduced', 'country', 'code'),
            country_is_deduced=user.seek('demographics', 'locationDeduced', 'country', 'deduced'),
            continent_name=user.seek('demographics', 'locationDeduced', 'continent', 'name'),
            continent_is_deduced=user.seek('demographics', 'locationDeduced', 'continent', 'deduced'),
            address_likelihood=user.seek('demographics', 'locationDeduced', 'likelihood')
        )

        base_age_range = user.seek('demographics', 'ageRange')
        if base_age_range:
            print base_age_range
            age_min, age_max = base_age_range.split('-')[0], base_age_range.split('-')[1]
        else:
            age_min, age_max = None, None

        UserDemography.create(
            user=user_obj,
            gender=user.seek('demographics', 'gender'),
            age=user.seek('demographics', 'age'),
            age_range_min=age_min,
            age_range_max=age_max
        )

        organizations = user.seek('organizations', default=list())
        for org in organizations:
            UserOrganization.create(
                user=user_obj,
                organization_name=org.get('name', ''),
                title=org.get('title', ''),
                start_date=org.get('startDate', None),
                end_date=org.get('endDate', None),
                is_current=org.get('current', 0),
                is_primary=org.get('isPrimary', 0)
            )

        topics = user.seek('digitalFootprint', 'topics', 'klout', default=list())

        for topic in topics:
            UserTopic.create(
                user=user_obj,
                provider=topic.get('provider', ''),
                topic=topic.get('value', None)
            )

        scores = user.seek('digitalFootprint', 'scores', 'klout', default=list())
        for score in scores:
            UserModelScore.create(
                user=user_obj,
                provider=score.get('provider', ''),
                type=score.get('general', ''),
                score_value=score.get('value', None)
            )

        websites = user.seek('contactInfo', 'websites', default=list())
        for web in websites:
            UserProfile.create(
                user=user_obj,
                profile_type='website',
                network_id='website',
                network_name='website',
                profile_url=web.get('url', None)
            )

        profiles_raw = user.seek('socialProfiles', default=list())
        profiles = []
        for network, profile in profiles_raw.items():
            profiles.extend([p for p in profile])
        for profile in profiles:
            profile = SeekableDict(profile)
            UserProfile.create(
                user=user_obj,
                profile_type='social',
                network_id=profile.seek('typeId'),
                network_name=profile.seek('typeName'),
                profile_id=profile.seek('id'),
                profile_url=profile.seek('url'),
                user_name=profile.seek('username'),
                user_bio=profile.seek('bio'),
                followers=profile.seek('followers'),
                following=profile.seek('following'),
                user_feed=profile.seek('rss')
            )

    def look_up_user(self, user_email):
        """ Query the FullContact API for a single user """

        response = self.api.person.get(silent=True, params={
            'email': user_email,
            'apiKey': self.fullcontact,
            'style': self.style
        })

        if response.status == 200:
            print Colors.OKGREEN + '  200 OK: ' + Colors.ENDC + 'lookup successful for ' + user_email
            print '    Inserting results into database ...',
            try:
                self.insert_user_rows(user_email, SeekableDict(response))
                print Colors.OKGREEN + 'SUCCESS' + Colors.ENDC
            except IntegrityError as e:
                print Colors.FAIL + 'FAILED'
                print '      Error inserting user record: "{}"'.format(e) + Colors.ENDC

        elif response.status == 202:
            print Colors.WARNING + '  202 ACCEPTED: ' + Colors.ENDC + 'will need to retry lookup for ' + user_email
            self.retries.append(user_email)

        elif response['status'] == 403:
            print Colors.WARNING + '  403 RATE LIMITED: ' + Colors.ENDC + 'either sending too many requests per second or exceeded quota'
            self.retries.append(user_email)

        else:
            print Colors.FAIL + '  ' + str(response['status']) + ' FAILURE: ' + Colors.ENDC + 'failed to return a result for ' + user_email
            self.failures.append(user_email)

        return True

    def export_matched_users(self, query, outf_path):
        with open(outf_path, 'w') as outf:
            dump_csv(query, outf)
