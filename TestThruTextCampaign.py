#!/usr/bin/env python

import json, os, unittest
from TestThruTextObject import TestThruTextObject
from ThruTextGroup import ThruTextGroup
from ThruTextRegion import ThruTextRegion
from ThruTextCampaign import ThruTextCampaign
from LoginManager import LoginManager

class TestThruTextGroup(TestThruTextObject):

	@classmethod
	def construct_one(cls, **kwargs):
		"""
		"""
		return ThruTextCampaign(**kwargs)

	@classmethod
	def get_test_object_payload(cls):
		ttg = ThruTextGroup()
		gl = ttg.list_all()
		cls.test_group_id = gl[0].id
		ttregion = ThruTextRegion(login_manager = ttg.login_manager)
		rd = ttregion.list_all()
		for r in rd:
			ttregion.become_region(r)
			break
		ttregion.index = 0
		cls.region_test = ttregion
		payload= {
			'data' : {
				'attributes' : {
					'name' : 'example test campaign',
					'description' : 'proving the campaign class works',
					'country_id' : 'US',
					'start_date' : '2020-03-13T05:00:00-05:00',
					'end_date' : '2020-03-14T05:00:00-05:00',
					'time_zone' : 'US/Central',
					'open_time' : '05:00',
					'close_time' : '19:00',
					'regions' : [cls.region_test.as_dict()],
					'segments' : [
						{
							'segment_type' : 'add',
							'segment_source_type' : 'group',
							'order' : 0,
							'source_group_id' : cls.test_group_id,
							"filter_surveys":[],
							"reply_status":"any",
						}
					],
					'script' : 'hello initial message greetings',
					'settings' : {
						"self_assignment": False,
					},
				}
			}
		}
		print(payload)
		return payload

	def test_make_new(self):
		"""
		TODO: this is pretty weak
		"""
		# use make new to make a specific group
		# prove it's in the website
		# prove its properties match this one's
		# prove we did the beocme @ the end
		#new_group_response, worked = self.safe_request('post', url=self.base_url, data=payload, headers={})
		lm = LoginManager()
		one = self.construct_one(login_manager=lm)
		ttg = ThruTextGroup(login_manager=lm)
		gl = ttg.list_all()
		ttg.become(gl[0].id)
		ttg.become(ttg.list_all()[0].id)
		one.make_new(name='testing make new campaign', script='v important', description='test to prove the campaign maker works.', start_date='2020-01-01T11:00', end_date='2020-02-01T21:00', time_zone='US/Central', open_time='08:00', close_time='21:00', regions = 512, group_id=ttg.id)
		two = ThruTextCampaign(login_manager=lm)
		assert two.become(one.id)
		self.assert_same(two.name, 'testing make new campaign', 'test_make_new_name')
		self.assert_same(two.description, 'test to prove the campaign maker works.', 'test_make_new_desc')
		self.assert_same(two.script, 'v important', 'test_make_new_script')
		self.assert_same(two.time_zone, 'US/Central', 'test_make_new_time_zone')
		self.assert_same(two.open_time, '08:00', 'test_make_new_open_time')
		self.assert_same(two.close_time, '21:00', 'test_make_new_close_time')
		assert two.get_rid_of()
		assert two.become(one.id)
		assert two.status == 'archived' 

	def verify_example_object(self, example):
		testing_list = [
			(example.type, 'campaign', 'type'),
			(example.name, 'example test campaign', 'object name'),
			(example.country_id, 'US', 'country id'),
			(example.id, self.test_id, 'id'),
			(example.status, 'draft','status'),
			(example.start_date, '2020-11-08T21:00:00.0000Z', 'start_date'),
			(example.end_date, '2020-12-25T12:00:00.0000Z', 'end_date'),
			(example.time_zone, 'US/Central', 'time_zone'),
			(example.open_time, '05:00', 'open_time'),
			(example.close_time, '19:00', 'close_time'),
			##(example.regions, cls.region_test.as_dict(), 'reigon'
			(example.script, 'hello initial message greetings', 'script'),
		]
		for tup in testing_dict.items():
			self.assert_same(tup[0], tup[1], 'verify_example_object_' + str(tup[2]))

	def test_get_rid_of(self):
		"""
		TODO: this is kind of tested by make_new
		"""
		# I guess make one and kill it
		pass

	def test_from_file(self):
		pass

	def example_dict(self):
		"""
		example dicts used for as_dict or from_dict tests
		"""
		return {
			'id' : 14,
			'type' : 'campaign',
			'relationships': {
			},
			'links': None,
			'attributes': {
				'name':'not the greatest campaign.',
				'status':'active',
				'open_time':'00:06',
				'close_time':'23:59',
				'start_date':'2000-05-01T18:00:00.00000Z',
				'end_date':'2000-05-01T19:00:00.00000Z',
				'description': 'this is just a tribute',
				'opt_outs_count': 0,
				'initial_sent_count': 1,
				'replies_count': 12,
				'conversations_count': 4,
				'unassigned_count':9001,
				'senders_count':7,
				'script':"couldn't remember",
				'country_id':'canada',
				'time_zone':'Etc/Zulu',
				'apportionment_failed_reason':'time management',
			}
		}

	def test_from_dict_correctness(self):
		try:
			login_manager = LoginManager(fake=True)
			example = self.construct_one(login_manager=login_manager)
			example.from_dict(self.example_dict())
			testing_list = [
				(example.id, 14 , 'id'),
				(example.type, 'campaign', 'type'),
				(example.name, 'not the greatest campaign.', 'name'),
				(example.status, 'active','status'),
				(example.open_time, '00:06','open_time'),
				(example.close_time, '23:59','close_time'),
				(example.start_date, '2000-05-01T18:00:00.00000Z','start_date'),
				(example.end_date, '2000-05-01T19:00:00.00000Z', 'end_date'),
				(example.description,  'this is just a tribute', 'desc'),
				(example.opt_outs_count,  0, 'opt_outs'),
				(example.initial_sent_count,  1, 'initial_sent_count'),
				(example.replies_count,  12, 'replies'),
				(example.conversations_count,  4, 'conversations'),
				(example.unassigned_count, 9001, 'unassinged'),
				(example.senders_count, 7, 'senders count'),
				(example.script, "couldn't remember", 'script'),
				(example.country_id, 'canada', 'country_id'),
				(example.time_zone, 'Etc/Zulu', 'time_zone'),
				(example.failure, 'time management', 'apportionment_failed'),
			]
			for tup in testing_list:
				self.assert_same(tup[0], tup[1], 'test_from_dict_correctness_' + str(tup[2]))
		finally:
			example.session.close()

	def test_as_dict_correctness(self):
		pass

del(TestThruTextObject)
if __name__ == '__main__':
	unittest.main()

