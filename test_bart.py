import json
import yaml

import unicodecsv as csv
from peewee import *
from playhouse.csv_loader import dump_csv

from models import *
from busybody import BusyBody


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


def parse_config_settings(config_file):
    with open(config_file, 'r') as inf:
        cfg = yaml.load(inf)

    return cfg


def digest_user_profiles(profiles_csv):
    """ Return dict objects of lookup values for each user"""
    with open(profiles_csv, 'r') as inf:
        reader = csv.DictReader(inf)

        profs = []
        for row in reader:
            if 'email' in row and row['email'] != '':
                profs.append({'type': 'email', 'name': row['email']})
            elif 'twitter' in row and row['twitter'] != '':
                profs.append({'type': 'twitter', 'name': row['twitter'].replace('@', '')})
            elif 'phone' in row and row['phone'] != '':
                profs.append({'type': 'phone', 'name': row['phone']})

    return profs


def insert_user_data(d, email, user):
    try:
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

        base_age_range = str(user.seek('demographics', 'ageRange'))
        if base_age_range:
            age_min, age_max = base_age_range.split('-')
        else:
            age_min, age_max = None, None

        UserDemography.create(
            user=user_obj,
            gender=user.seek('demographics', 'gender'),
            age=user.seek('demographics', 'age'),
            age_range_min=age_min,
            age_range_max=age_max
        )

        for org in user['organizations']:
            UserOrganization.create(
                user=user_obj,
                organization_name=org.get('name', ''),
                title=org.get('title', ''),
                start_date=org.get('startDate', None),
                end_date=org.get('endDate', None),
                is_current=org.get('current', 0),
                is_primary=org.get('isPrimary', 0)
            )

        for topic in user.seek('digitalFootprint', 'topics', default=list()):
            UserTopic.create(
                user=user_obj,
                provider=topic.get('provider', ''),
                topic=topic.get('value', None)
            )

        for score in user.seek('digitalFootprint', 'scores', default=list()):
            UserModelScore.create(
                user=user_obj,
                provider=score.get('provider', ''),
                type=score.get('general', ''),
                score_value=score.get('value', None)
            )

        for web in user.seek('contactInfo', 'websites', default=list()):
            UserProfile.create(
                user=user_obj,
                profile_type='website',
                network_id='website',
                network_name='website',
                profile_url=web.get('url', None)
            )

        for profile in user.seek('socialProfiles', default=list()):
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

    except IntegrityError as e:
        print 'Error inserting user record :: "%s"' % e


if __name__ == '__main__':
    cfg = parse_config_settings('config.yaml')
    profiles = digest_user_profiles('bloggers.csv')
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

    with open('account-export.csv', 'w') as fh:
        dump_csv(query, fh)
