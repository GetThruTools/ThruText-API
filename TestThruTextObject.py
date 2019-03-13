#!/usr/bin/env python

from ThruTextObject import ThruTextObject
from LoginManager import LoginManager
from abc import ABC, abstractmethod
import unittest, json, requests, time
from datetime import datetime

class TestThruTextObject(unittest.TestCase, ABC):
	"""
	Basic suite of tests that cover the functions of ThruTextObject that are meant to be overridden. 
	Each thru_text object should extend this class with its own tests.
	"""

	test_id = None

	def assert_same(self, thing1, thing2, test_name=None):
		if thing1 != thing2 or (thing1 is None and thing1 is not thing2):
			print('\n\n')
			if test_name is not None:
				print(str(test_name))
			print(str(thing1) + " != " + str(thing2))
			print('\n\n')
		assert thing1 == thing2

	@classmethod
	def setUpClass(cls):
		super(TestThruTextObject, cls).setUpClass()
		lm = LoginManager()
		cls.test_id = cls.make_test_in_thru_text(login_manager=lm)

	@classmethod
	def tearDownClass(cls):
		super(TestThruTextObject, cls).tearDownClass()
		testing = cls.construct_one()
		testing.get_rid_of(cls.test_id)
		testing.session.close()

	@classmethod
	@abstractmethod
	def construct_one(cls, **kwargs):
		"""
		wrapper for this object's constructor
		"""
		pass

	@abstractmethod 
	def verify_example_object(self):
		"""
		prove that this object is identical to the one made in make_test_in_thru_text
		"""
		pass

	@classmethod
	def get_test_object_payload(cls):
		"""
		Returns the data to post to make the example object
		"""
		return {}

	@classmethod
	def make_test_in_thru_text(cls, login_manager):
		"""
		make a thru_text object to use in testing
		returns the id of the made object
		remember to use self.login_manager
		don't use make_new or any other methods
		"""
		payload = cls.get_test_object_payload()
		try:
			tto = cls.construct_one(login_manager=login_manager)
			response = tto.session.post(url=tto.base_url, headers={}, data=json.dumps(payload))
			assert (response.status_code >= 200 and response.status_code < 300)
			mdict = json.loads(response.content)['data']
			assert mdict['type'] == tto.thru_text_type
			return mdict['id']
		finally:
			tto.session.close()


	@abstractmethod
	def example_dict(self):
		"""
		example dicts used for as_dict or from_dict tests
		"""
		return {}

	@abstractmethod
	def test_from_dict_correctness(self):
		pass

	@abstractmethod
	def test_as_dict_correctness(self):
		pass


	def test_become(self):
		"""
		it's possible this test can fail b/c status changes from uploading to active
		"""
		pass

	def test_list_all(self):
		one = self.construct_one()
		response = one.session.get(url=one.base_url, headers={})
		manual_list = json.loads(response.content)['data']
		func_list = one.list_all()
		assert len(manual_list) == len(func_list)
		manual_list = sorted(manual_list, key=lambda obj: obj['id'])
		func_list = sorted(func_list, key=lambda obj: obj.id)
		for index in range(len(manual_list)):
			self.assert_same(manual_list[index]['id'], func_list[index].id, 'test_list_all_'+str(index))

	@abstractmethod
	def test_make_new(self):
		"""
		make a test object and verify it
		"""
		pass

	@abstractmethod
	def test_get_rid_of(self):
		"""
		"""
		pass

	def test_base_url(self):
		lm = LoginManager(fake=True)
		lm.account_number = '0000000001'
		lm.staging = False
		testing = self.construct_one(login_manager=lm)
		test_url = testing.base_url
		assert test_url is not None
		self.assert_same(test_url, 'https://api.relaytxt.io/v1/accounts/0000000001/'+str(testing.url_name), 'test_base_url')

	def test_display_url(self):
		lm = LoginManager(fake=True)
		lm.account_name = 'testing_account'
		lm.account_number = '0000000001'
		lm.staging = False
		testing = self.construct_one(login_manager=lm)
		testing.id = '0000000002'
		test_url = testing.display_url
		assert test_url is not None
		self.assert_same(test_url, 'https://testing_account.relaytxt.io/admin/'+str(testing.url_name)+'/0000000002', 'test_display_url')

	def test_dict_round_trips(self):
		"""
		Tests conversion of values from in_dict into an object, and then out again.
		the out dict can have more values b/c of the Nones
		(This is set up so that you can add more example dicts and it scales)
		"""
		lm = LoginManager(fake=True)
		for start_dict in [self.example_dict(), None]:
			if start_dict is None:
				continue
			testing = self.construct_one(login_manager=lm, in_dict=start_dict)
			end_dict = testing.as_dict()
			start_keys  = set(start_dict.keys())
			end_keys = set(end_dict.keys())
			assert len(start_keys) <= len(end_keys)
			for key in end_keys:
				start_value = start_dict.get(key)
				if isinstance(start_value, dict):
					for subkey, subvalue in start_value.items():
						self.assert_same(subvalue, end_dict[key][subkey], 'test_dict_round_trip, key: ' + str(key) + ": " + str(subkey))
				elif start_value is not None:
					self.assert_same(start_value, end_dict[key], 'test_dict_round_trip, key: ' + str(key))
				else:
					assert end_dict[key] is None

	def test_dict_random_round_trip(self):
		lm = LoginManager()
		testing = self.construct_one(login_manager = lm)
		object_list = testing.list_all()
		first_dict = object_list[0].as_dict()
		second_object = self.construct_one(login_manager=lm, in_dict=first_dict)
		second_dict = second_object.as_dict()
		self.assert_same(first_dict, second_dict, 'test_dict_random_round_trip')

	def test_timestamp(self):
		lm = LoginManager(fake=True)
		testing = self.construct_one(login_manager=lm)
		if testing.age_attribute is None:
			assert True
			return
		try:
			_ = getattr(testing, testing.age_attribute)
		except AttributeError:
			assert False
		dt = datetime.now()
		setattr(testing, testing.age_attribute, dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
		self.assert_same(dt, testing.timestamp(), 'test_timestamp_1')
		setattr(testing, testing.age_attribute, '2018-11-06T08:00:00.0000Z')
		self.assert_same(testing.timestamp(), datetime(year=2018, month=11, day=6, hour=8), 'test_timestamp_2')

