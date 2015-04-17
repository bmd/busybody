import json
import sys
import yaml

from busybody.colors import Colors
import unicodecsv as csv
from peewee import *
from playhouse.csv_loader import dump_csv

from busybody.models import *
from busybody.busybody import BusyBody, SeekableDict


def parse_config_settings(config_file):
    print Colors.BOLD + 'Reading configuration settings ...' + Colors.ENDC,
    try:
        with open(config_file, 'r') as inf:
            cfg = yaml.load(inf)
        print Colors.OKGREEN + 'SUCCESS'
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

    # look up users
    for email in emails:
        bb.look_up_user(email['email'])



    # clean up
    bb.dump_failed_queue('failures.csv')
    #bb.execute_queued_retries()
    bb.dump_retry_queue('retries.csv')

    sys.exit()

    # export successes
    bb.export_matched_users('user_profiles.csv')

    sys.exit()

    with open('bart.json', 'r') as inf:
        users = [SeekableDict(user) for user in json.loads(inf.read())]

    emails = ['bart@fullcontact.com', 'salil.kalia@gmail.com']
    for i, usr in enumerate(users):
        insert_user_data(db, emails[i], usr)
    FacebookProfile = UserProfile.select(UserProfile).where(UserProfile.network_name == 'Facebook').alias('FacebookProfile')
    TwitterProfile = UserProfile.select(UserProfile).where(UserProfile.network_name == 'Twitter').alias('TwitterProfile')
    Website = UserProfile.select(UserProfile).where(UserProfile.network_name == 'Web').alias('Website')

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


