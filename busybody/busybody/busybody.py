import logging

from playhouse.csv_loader import dump_csv

from ..database.models import *
from ..utils.colors import Colors

logger = logging.getLogger(__name__)


class BusyBodyFactory:
    @staticmethod
    def construct(db_connection, fullcontact_api):
        return BusyBody(db_connection, fullcontact_api)


class BusyBody:
    def __init__(self, database, fc_api):
        self.api = fc_api
        self.db = database

    def process_person(self, email):
        response = self.api.get_person(email)

        if response.status == 200:
            try:
                logger.info()
                self.db.insert_user_record(email, response)
            except IntegrityError, e:
                logger.warn(Colors.FAIL + 'Error inserting user record: {}'.format(e) + Colors.ENDC)
        else:
            if response.status == 202:
                logger.warn(Colors.WARNING + '  202 ACCEPTED: ' + Colors.ENDC + 'will need to retry lookup for ' + email)
            elif response.status == 403:
                logger.warn(Colors.WARNING + '  403 RATE LIMITED: ' + Colors.ENDC + 'either sending too many requests per second or exceeded quota')
            else:
                logger.error(Colors.FAIL + '  ' + str(response.status) + ' ' + self.api.status_map[response.status] + ': ' + Colors.ENDC + 'failed to return a result for ' + email)

            self.db.log_failure(email, response)

        return response

    def retry_person(self, retry_state):
        email = retry_state['email']
        response = self.api.get_person(email)

        if response.status == 200:
            self.db.insert_user_record(email, response)
        else:
            if response.status == 202:
                logger.warn(Colors.WARNING + '  202 ACCEPTED: ' + Colors.ENDC + 'will need to retry lookup for ' + email)
            elif response.status == 403:
                logger.warn(Colors.WARNING + '  403 RATE LIMITED: ' + Colors.ENDC + 'either sending too many requests per second or exceeded quota')
            else:
                logger.error(Colors.FAIL + '  ' + str(response.status) + ' ' + self.api.status_map[response.status] + ': ' + Colors.ENDC + 'failed to return a result for ' + email)

        self.db.update_retry_row(retry_state, response)

        return response

    def dump_failures(self, outf_path, include_completed=False):
        self.db.dump_failure_table(outf_path, include_completed=include_completed)

    def get_failures(self):
        failures = self.db.fetch_retry_queue()
        return failures

    def dump_user_data(self, outf_path):
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
