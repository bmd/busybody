from peewee import *
from models import *
import yaml

import tortilla

def parse_config_settings(config_file):
	with open(config_file, 'r') as inf:
		cfg = yaml.load(inf)

	return cfg

class BusyBody(object):
	"""A BusyBody Instance"""
	def __init__(self, db, fc_key):
		super(BusyBody, self).__init__()
		self.conn = db
		self.api_key = fc_key

if __name__ == '__main__':

	query_parameters = {
		'email': 'b.maionedowning@gmail.com', 
		'apiKey': '...', 
		'style': 'dictionary'
	}

	fullcontact = tortilla.wrap('https://api.fullcontact.com/v2', debug=True, extension='json')
	result = fullcontact.person.get(params=query_parameters)

	print 'Testing Execution'
	print db
