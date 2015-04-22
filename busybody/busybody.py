import tortilla
from playhouse.csv_loader import dump_csv
from playhouse.shortcuts import model_to_dict

from models import *
from colors import Colors


class SeekableDict(dict):
    """
    See if an arbitrarily deep key exists without commiting to the
    existance of any of its parent keys.

    It's not quite like a defaultdict, but it's not quite not a
    defaultdict either.
    """

    @staticmethod
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
        410: 'GONE (ENDPOINT DEPRECATED)',
        422: 'INVALID REQUEST',
        500: 'SERVER ERROR'
    }

    def __init__(self, fc_key, debug_setting=False, style='dictionary'):
        self.fullcontact = fc_key
        self.api = tortilla.wrap('https://api.fullcontact.com/v2', debug=debug_setting, delay=1, extension='json')
        self.style = style
        self.debugging = debug_setting

    def _log_failure(self, result, email):
        FailureLog.create(
            email=email,
            initial_status=result.status,
            message=result.message,
            request_id=result.requestId,
            retry_complete=(result.status not in [202, 403, 500, 400, 422])
        )
        return True

    def _update_failure_log(self, current_row_obj, new_result):
        # update the failure row to flag if our result has succeeded
        fq = (FailureLog
            .update(
                most_recent_retry_status=new_result.status,
                retry_count=FailureLog.retry_count + 1,
                retry_complete=(new_result.status not in [202, 403, 500, 400, 422]),
                most_recent_retry_dt=datetime.datetime.now()
            )
            .where(
                FailureLog.request_id == current_row_obj['request_id']
            )
        )
        fq.execute()

        # get the updated row
        return FailureLog.select().where(FailureLog.request_id == current_row_obj['request_id'])

    # TODO
    def retry_failures(self):
        """ Get a list of emails that still need to be retried and query the FullContact API """
        users_to_retry = self._get_remaining_retries()

        # just return if we have nothing to retry!
        if len(users_to_retry) == 0:
            return False

        # lookup users who need to be retried
        user_lookups = []
        for user in users_to_retry:
            lookup = self.look_up_user(user['email'])
            user_lookups.append(model_to_dict(lookup))

        return user_lookups

    def _get_remaining_retries(self):
        """
        Return all rows from the failure_log table that still need to be retried
        """
        query = (FailureLog
            .select()
            .where(
                (
                    # specific codes that indicate we need to retry
                    #   - 202: explicit retry call
                    #   - 403: rate limit or auth rejection
                    #   - 500: server error, not our fault
                    (FailureLog.initial_status == 202) |
                    (FailureLog.initial_status == 403) |
                    (FailureLog.initial_status == 500)
                )
                # a retry can complete without succeeding (i.e. if  we go from 202 -> 404)
                & (FailureLog.retry_complete == 0)
            )
        )
        return [model_to_dict(result) for result in query]

    def look_up_user(self, user_email, is_retry=False):
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

        elif response.status == 403:
            print Colors.WARNING + '  403 RATE LIMITED: ' + Colors.ENDC + 'either sending too many requests per second or exceeded quota'

        else:
            print Colors.FAIL + '  ' + str(response.status) + ' ' + self.status_map[response.status] + ': ' + Colors.ENDC + 'failed to return a result for ' + user_email

        if is_retry:
            self._update_failure_log(cur_id, response)
        elif response.status != 200:
            self._log_failure(response, user_email)

        return response

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

    def dump_failure_table(self, outf_path):
        with open(outf_path, 'w') as outf:
            dump_csv(FailureLog.select(), outf)

    def export_user_data(self, outf_path):
        FacebookProfile = (UserProfile
            .select(UserProfile)
            .where(UserProfile.network_name == 'Facebook')
            .alias('FacebookProfile')
        )

        TwitterProfile = (UserProfile
            .select(UserProfile)
            .where(UserProfile.network_name == 'Twitter')
            .alias('TwitterProfile')
        )

        Website = (UserProfile
            .select(UserProfile)
            .where(UserProfile.network_name == 'Web')
            .alias('Website')
        )

        query = (User
            .select(
                User.user_id.alias('user_id'),
                User.first_name.alias('first_name'),
                User.last_name.alias('last_name'),
                User.email.alias('email'),
                UserAddress.location_general.alias('location'),
                UserDemography.age.alias('age'),
                UserDemography.age_range_min.alias('age_range_min'),
                UserDemography.age_range_max.alias('age_range_max'),
                UserModelScore.score_value.alias('klout_score'),
                FacebookProfile.c.profile_id.alias('facebook_id'),
                FacebookProfile.c.user_name.alias('facebook_username'),
                FacebookProfile.c.profile_url.alias('facebook_profile'),
                TwitterProfile.c.profile_id.alias('twitter_id'),
                TwitterProfile.c.user_name.alias('twitter_screen_name'),
                TwitterProfile.c.followers.alias('twitter_followers'),
                TwitterProfile.c.following.alias('twitter_following'),
                Website.c.profile_url.alias('website'),
                User.create_dt.alias('scraped_on')
            )
            .join(UserAddress, JOIN.LEFT_OUTER).switch(User)
            .join(UserModelScore, JOIN.LEFT_OUTER).switch(User)
            .join(UserDemography, JOIN.LEFT_OUTER).switch(User)
            .join(UserTopic, JOIN.LEFT_OUTER).switch(User)
            .join(FacebookProfile, JOIN.LEFT_OUTER, on=(User.user_id==FacebookProfile.c.user_id)).switch(User)
            .join(TwitterProfile, JOIN.LEFT_OUTER, on=(User.user_id==TwitterProfile.c.user_id)).switch(User)
            .join(Website, JOIN.LEFT_OUTER, on=(User.user_id==Website.c.user_id))
            .group_by(User)
        )

        with open(outf_path, 'w') as outf:
            dump_csv(query, outf)
