#!/usr/bin/env python

import json, time, requests
from datetime import datetime
import pytz
from LoginManager import LoginManager
import os
from abc import ABC, abstractmethod

class ThruTextObject(ABC):
	"""
	A bunch of generically useful stuff that thru_text objects should be able to do
	ThruText Object check list:
	1. age attribute
	2. url_name
	3. initialize_values function for __init__
	4. in_dict, from_dict
	5. make_new <- creates a new one of these, and becomes a copy of it
	6. get_rid_of <- either archiving or deleting this

	also consider if the object has weird behavior for become or list_all
	"""

	#what attribute you use for how old you are.
	#set to None if that's not something that applies to you
	age_attribute = 'end_date'

	#the thru_text object type that appears after the last / in the url. Used in base_url. groups, campaigns, etc. Set to None if you want to throw an error w/ the default base_url
	url_name = None

	# all thru_text objects have an id and a type. This is the type, its meant to make sure you don't have a campaign object representing a group or something like that
	thru_text_type = None

	@abstractmethod
	def initialize_values(self):
		"""
		Called in __init__ between configuring the login and using in_dict. 
		You'll have a login manager if you want to do any api calls.
		"""
		pass

	def __init__(self, *, in_dict=None, login_manager=None):
		"""
		This class is abstract, so don't make one of them but this is how the constructor should look.
		input:
		in_dict (optional) : dictionary from which to build this object
		login_manager (optional) : if you've already logged in, you can resuse that manager. if not, we'll make one for you

		"""
		self.id = None
		self.type = None
		self.default_timezone = None
		self.configure_login(login_manager)
		self.initialize_values()
		#initialize variables
		if in_dict is not None:
			self.from_dict(in_dict)

	def configure_login(self, login_manager=None):
		"""
		This is where we handle logging in and making a session. From here on out, we assume that's all settled.
		"""
		if login_manager is None:
			self.login_manager = LoginManager()
		else:
			self.login_manager = login_manager
		self.session = self.login_manager.create_session()
		
	#thru_text objects are structured:
	# {
	# 	id
	# 	type
	# 	attributes {} (things that can change)
	# 	relationships {} (linked thru_text object)
	# 	links {} (actual urls of other things)
	# }

	@property
	def base_url(self):
		if self.url_name is None:
			print("Error: don't have a url name. Should " + str(self.__class__) + " have a custom base url function?")
			return None
		if self.login_manager.staging:
			url_start = 'https://api.relaytxt-staging.io/v1/accounts/'
		else:
			url_start = 'https://api.relaytxt.io/v1/accounts/'
		return url_start+str(self.login_manager.account_number)+'/'+str(self.url_name)

	@property
	def display_url(self):
		"""
		generates the URL that a user would go to to see this object
		input:
		output:
		the url you can type into a browser
		"""
		if self.url_name is None:
			print("Error: don't have a url name. Should " + str(self.__class__) + " have a custom display url function?")
			return None
		if self.login_manager.staging:
			staging_url = '.relaytxt-staging.io/admin/'
		else:
			staging_url = '.relaytxt.io/admin/'
		return 'https://' + str(self.login_manager.account_name) + staging_url + str(self.url_name) + '/' + str(self.id) 

	@abstractmethod
	def from_dict(self, in_dict):
		"""
		eat a dictionary, fill in your attributes
		most often used to turn the output of a request into an object
		"""
		pass

	@abstractmethod
	def as_dict(self):
		"""
		return this as a dictionary
		most often used to make this part of a payload of a request
		"""
		pass

	@abstractmethod
	def make_new(self):
		"""
		makes a new one of these in the website, and then makes this object the new one that was created
		""" 
		pass

	def timestamp(self):
		"""
		returns the value of the age attribute as None or a datetime
		"""
		if self.age_attribute is None:
			return None
		try:
			timestamp_str = getattr(self, self.age_attribute)
		except AttributeError:
			return None
		if timestamp_str is None:
			return None
		return self.str_to_datetime(timestamp_str)

	def str_to_datetime(self, unicode_string):
		"""
		turns ThruText's timestamps format into a datetime
		"""
		#example: u'2018-06-16T01:00:00.000000Z'
		return datetime.strptime(unicode_string, '%Y-%m-%dT%H:%M:%S.%fZ')

	def datetime_to_str_no_tz(self, dt):
		return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

	def datetime_to_str(self, dt):
		"""
		Turns a datetime into a string in the accepted thru_text format
		"""
		if dt.tzinfo is None:
			if self.default_timezone is not None:
				aware_time = self.default_timezone.localize(dt)
			elif os.getenv('THRU_TEXT_DEFAULT_TIMEZONE') is not None and len(os.getenv('THRU_TEXT_DEFAULT_TIMEZONE')):
				aware_time = pytz.timezone(os.getenv('THRU_TEXT_DEFAULT_TIMEZONE')).localize(dt)
			else:
				aware_time = pytz.timezone('Etc/Zulu').localize(dt)
		else:
			aware_time = dt
		result = aware_time.astimezone(pytz.timezone('Etc/Zulu')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
		return result 
		
	def safe_request(self, method, *, url=None, headers=None, session=None, data=None, includes=None, filters=None):
		"""
		A method that makes the request. Automatically retries in cases of failed connections, and displays debug info. We're not trying to reinvent the wheel here, just incldue all the standard debugging stuff you'd do anyway in one place. You ought to be able to use safe_request to make any sort of request you could normally make. If you want to use the methods of the request module directly in your code, that also works, but when extending this code safe_request should be used for uniformity.
		input:
		method - post, get, delete, etc.
		url - the url that you're sending the request to
		headers - dictionary of any additional headers. is added to the ones in the session as normal
		session - the session to use, if you want to specify a different one than this object normally uses
		data - the payload of the request AS A DICTIONARY. This method does the json-ing to it
		includes - a single include or list of includes as a string. This method does all the needed formatting.
		output:
		my_request - the standard request object generated by what you asked for. This can be None if for some if you're not online or something like that.
		working - whether or not the request worked (returned a status_code in the 200 range)
		"""

		# get the session we're going to use
		if session is None:
			session = self.session

		if url is None:
			print("Error: no url for request!")
			return False
		if headers is None:
			headers = {}

		# stuff all the parameters into a dict, w/ some formatting as you go
		request_parameters = {'url':url, 'headers':headers}
		if data is not None:
			request_parameters['data'] = json.dumps(data)
		if includes is not None:
			if request_parameters.get('params') is None:
				request_parameters['params'] = {}
			if isinstance(includes, list):
				request_parameters['params']['include'] = ','.join(includes)
			else:
				request_parameters['params']['include'] = str(includes)
		if filters is not None:
			if request_parameters.get('params') is None:
				request_parameters['params'] = {}
			filter_str = ''
			for key, value in filters.items():
				request_parameters['params']['filter['+str(key)+']'] = str(value)

		#try to actually do the request
		max_tries = 3
		tries = 0
		connected = False
		response = None
		while not connected and tries < max_tries:
			try:
				response = getattr(session, method)(**request_parameters)
				connected = True
			except requests.exceptions.ConnectionError:
				tries += 1
			except AttributeError:
				print("ERROR: no attribute of session named " + str(method))
				break

		#did it work?
		try:
			if response.status_code < 200 or response.status_code >= 300:
				print("status_code: " + str(response.status_code))
				print("text:        " + str(response.text))
				print("method:      " + str(method))
				print("url:         " + str(url))
				print("headers:     " + str(headers))
				if includes is not None:
					print("includes:    " + str(includes))
				if data is not None:
					print("data:     " + str(data))
				return response, False
		except AttributeError:
			print("ERROR: something is weird with the request after safe_request.")
			return response, False
		return response, True

	def become(self, become_id=None, *, includes=None):
		"""
		turns this thru_text object into a copy of the thru_text object w/ the given ID
		"""
		if become_id is None:
			become_id = self.id
		url = self.base_url+'/'+str(become_id)
		future_me_request, worked = self.safe_request('get', url=url, headers={}, includes=includes)
		if not worked:
			return False
		try:
			self.from_dict(json.loads(future_me_request.content)['data'])
		except KeyError:
			return False
		return self.type == self.thru_text_type

	@abstractmethod
	def get_rid_of(self, other_id=None):
		"""
		do the appropriate thing to get rid of this object. Either archiving or deleting.
		input:
		other_id: (optional) if you want to get rid of another object, you specify its id here. If not specified, will get rid of this object.
		returns:
		boolean. whether or not the object was gotten rid of
		"""
		pass

	def archive(self, archive_id=None):
		"""
		Archives this
		This end point has changed 
		"""
		if archive_id is None:
			archive_id = self.id
		url = self.base_url+'/'+str(archive_id)+'/archive'
		payload = {}
		archive, worked = self.safe_request('post', url=url, headers={}, data=payload)
		return worked

	def list_all(self, filters=None, includes=None):
		"""
		Returns a list of all of this object represented as the appropriate type of ThruText object
		You will frequently want to filter by active only. Example: TODO
		"""
		object_list_request, worked = self.safe_request('get', url=self.base_url, headers={}, includes=includes, filters=filters)
		if not worked:
			return None
		object_list = json.loads(object_list_request.content)['data']
		result = []
		for ol in object_list:
			try:
				result.append(self.__class__(in_dict=ol, login_manager=self.login_manager))
			except KeyError:
				pass
		return result

class ConcreteThruTextObject(ThruTextObject):
	"""
	An object that is exactly like a ThruTextObject, but less abstract. Used for testing.
	"""
	age_attribute = None
	url_name = ''
	thru_text_type = None

	def initialize_values(self):
		pass

	def from_dict(self, in_dict):
		pass

	def as_dict(self):
		pass

	def make_new(self):
		pass

	def get_rid_of(self, other_id=None):
		pass

import unittest

class TestGenericThruTextObject(unittest.TestCase):
	"""
	Tests for functions that are not likely to be overriden by inheriting classes, like configure_login or any of the datetime to string functions.
	"""

	def prove_session_works(self, session, base_url):
		response = session.get(url=base_url+'groups', headers={})
		return (response.status_code >= 200 and response.status_code < 300)
		
	def test_configure_login_from_none(self):
		"""
		prove this object will make a working login manager
		"""
		testing = ConcreteThruTextObject()
		assert testing.login_manager is not None
		assert self.prove_session_works(testing.session, testing.base_url)
		testing.session.close()

	def test_configure_login_from_existing_lm(self):
		"""
		prove this object will take an existing login manager and use it
		prove the existing login manager doesn't log in again
		"""
		lm = LoginManager()
		lm.default_login()
		num_attempts = lm.num_attempts
		testing = ConcreteThruTextObject(login_manager=lm)
		assert testing.login_manager is not None
		assert testing.login_manager.token == lm.token
		assert testing.login_manager.num_attempts == num_attempts
		assert testing.login_manager.prove_token_works()
		assert self.prove_session_works(testing.session, testing.base_url)
		testing.session.close()

	#TODO:
	# safe request

	def datetime_list(self):
		dt1 = datetime(year=1941, month=12, day=7, hour=8, minute=10)
		dt2 = datetime(year=2001, month=9, day=11, hour=8, minute=46, microsecond=194)
		dt3 = datetime(year=2016, month=11, day=9, hour=7, minute=30, second=7)
		return[dt1, dt2, dt3]

	def assert_same(self, thing1, thing2, test_name=None):
		if thing1 != thing2 or (thing1 is None and thing1 is not thing2):
			print('\n\n')
			if test_name is not None:
				print(str(test_name))
			print(str(thing1) + " != " + str(thing2))
			print('\n\n')
		assert thing1 == thing2
		
	def test_str_to_datetime(self):
		lm = LoginManager(fake=True)
		cro = ConcreteThruTextObject(login_manager=lm)
		dtl = [datetime(year=2018, month=6, day=16), datetime(year=2019, month=3, day=11, hour=9), datetime(year=1900, month=11, day=1, hour=0, minute=1, second=59) ]
		answers = ['2018-06-16T00:00:00.000000Z', '2019-03-11T09:00:00.000000Z', '1900-11-01T00:01:59.000000Z']
		for index in range(len(dtl)):
			self.assert_same(cro.str_to_datetime(answers[index]), dtl[index], test_name="test_str_to_datetime_" + str(index+1))

	def test_datetime_to_str_no_tz(self):
		lm = LoginManager(fake=True)
		cro = ConcreteThruTextObject(login_manager=lm)
		dtl = self.datetime_list()
		answers = ['1941-12-07T08:10:00.000000Z','2001-09-11T08:46:00.000194Z','2016-11-09T07:30:07.000000Z']
		for index in range(len(dtl)):
			self.assert_same(cro.datetime_to_str_no_tz(dtl[index]), answers[index], test_name="test_datetime_to_str_no_tz")

	def generic_test_datetime_to_str(self, env_default=None, local_default=None, dtl=None,  answers=None, test_name=None):
		if test_name is None:
			test_name = 'unnamed_test'
		saved_default_tz = os.getenv('THRU_TEXT_DEFAULT_TIMEZONE')
		os.environ['THRU_TEXT_DEFAULT_TIMEZONE'] = '' if env_default is None else env_default
		try:
			if dtl is None:
				dtl = self.datetime_list()
			lm = LoginManager(fake=True)
			cro = ConcreteThruTextObject(login_manager=lm)
			if local_default is not None:
				cro.default_timezone = pytz.timezone(local_default)
			for index in range(len(dtl)):
				self.assert_same(cro.datetime_to_str(dtl[index]), answers[index], test_name=test_name + '_' + str(index+1))
		finally:
			if saved_default_tz is not None:
				os.environ['THRU_TEXT_DEFAULT_TIMEZONE'] = saved_default_tz

	def test_datetime_to_str_no_default_tz(self):
		answers = ['1941-12-07T08:10:00.000000Z', '2001-09-11T08:46:00.000194Z', '2016-11-09T07:30:07.000000Z']
		self.generic_test_datetime_to_str(answers=answers, test_name="test_datetime_to_str_no_default_tz")

	def test_datetime_to_str_local_default_tz(self):
		answers = ['1941-12-07T14:10:00.000000Z', '2001-09-11T13:46:00.000194Z', '2016-11-09T13:30:07.000000Z']
		self.generic_test_datetime_to_str(local_default='US/Central', answers=answers, test_name="test_datetime_to_str_local_default_tz")

	def test_datetime_to_str_env_default_tz(self):
		answers = [ '1941-12-07T18:10:00.000000Z', '2001-09-11T18:46:00.000194Z', '2016-11-09T17:30:07.000000Z', ]
		#Etc/GMT+10 actually means GMT-10, because why not
		self.generic_test_datetime_to_str(env_default='Etc/GMT+10', answers=answers, test_name="test_datetime_to_str_env_default_tz")

	def test_datetime_to_str_local_beats_env(self):
		answers = [ '1941-12-07T14:10:00.000000Z', '2001-09-11T13:46:00.000194Z', '2016-11-09T13:30:07.000000Z',]
		#Etc/GMT+10 actually means GMT-10, because why not
		self.generic_test_datetime_to_str(local_default='US/Central', env_default='Etc/GMT+10', answers=answers, test_name="test_datetime_to_str_local_beats_env")

	def test_datetime_to_str_aware_times(self):
		dt1 = datetime(year=1941, month=12, day=7, hour=8, minute=10)
		#Etc/GMT+10 actually means GMT-10, because why not
		dt1 = pytz.timezone('Etc/GMT+10').localize(dt1)
		dt2 = datetime(year=2001, month=9, day=11, hour=8, minute=46, microsecond=194)
		dt2 = pytz.timezone('US/Eastern').localize(dt2)
		dt3 = datetime(year=2016, month=11, day=9, hour=7, minute=30, second=7)
		dt3 = pytz.timezone('Etc/Zulu').localize(dt3)
		answers = [ '1941-12-07T18:10:00.000000Z', '2001-09-11T12:46:00.000194Z', '2016-11-09T07:30:07.000000Z', ]
		self.generic_test_datetime_to_str(local_default='Asia/Shanghai', env_default='Europe/Moscow', answers=answers, dtl=[dt1, dt2, dt3], test_name="test_datetime_to_str_aware_times")

if __name__ == "__main__":
	unittest.main()

