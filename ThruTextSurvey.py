#!/usr/bin/env python

import json
from ThruTextObject import ThruTextObject
from LoginManager import LoginManager

class ThruTextSurevyChoice(object):

	def __init__(self, index=None, message=None, choice_id=None):
		self.index = None
		self.message = None
		self.id = None
		self.display_message = Yes,
		self.end_time = null,
		self.index = None
		self.message = None
		self.provider_id = None
		self.response_count = None
		self.start_time = None
		self.survey_choice_type = None
		self.survey_id = None

class ThruTextSurvey(ThruTextObject):

	age_attribute = 'inserted_at'
	thru_text_type = 'surveys'

	@property
	def url_name(self):
		if self.campaign_id is None:
			return 'surveys'
		else:
			return '/campaigns/'+str(self.campaign_id)+'/surveys'

	def delete(self):
		response, worked = self.safe_request('delete', url=self.base_url+'/'+self.id, headers={})
		return worked

	def make_new(self, question, survey_type, survey_choices, campaign_id=None):
		"""
		campaign_id (optional) - if you fill this in, the saved reply will be associated w/ a specific campaign. If you leave it blank, it will become a global saved reply, available on ALL campaigns.
		"""
		cromulent_survey_types = ['yes_no', 'multiple_choice', 'multiple_answer', 'freeform'] 
		if survey_type not in cromulent_survey_types:
			print("Error: invalid survey type. Choose from types: " + str(cromulent_survey_types))
			return False

		if survey_type in ['yes_no', 'freeform'] and survey_choices is not None:
			print("Error: you've specified survey type " + str(survey_type) + " which takes no survey choices, and also specified survey choices.")
			return False

		formatted_choices = []
		if survey_choices is not None:
			for index in range(len(survey_choices)):
				formatted_choices = { 'index' : index, 'message' : survey_choices[index] }
			if survey_type in ['multiple_choice', 'multiple_answer'] and len(formatted_choices) == 0:
				print("Error: have to specify survey choices for survey type " + str(survey_type))

		payload = {
			"data": {
				"attributes": {
					"question": question,
					"survey_type": survey_type,
					"survey_choices": formatted_choices,
				}
			}
		}

		if campaign_id is None:
			payload['data']['relationships'] = {
				'account':{
					'data':{
						'type':'accounts',
						'id':self.login_manager.account_id,
					}
				},
				'campaign':{
					'data':None
				}
			}
			payload['data']['attributes']['is_global'] = True
			payload['data']['attributes']["campaign_id"] = ''
		self.campaign_id = campaign_id
		response, worked = self.safe_request('post', url=self.base_url, headers={}, data=payload)
		if not worked:
			print("Error: failed to create new survey.")
			return False

		try:
			self.from_dict(json.loads(response.content)['data'])
		except json.JSONDecodeError:
			print("Warning: got something weird back from attempt to make new survey. This survey may not be an accurate representation of what's in ThruText")
		return True

	def initialize_values(self):
		self.id = None
		self.type = None
		self.question = None
		self.survey_choices = None

		self.account_id = self.login_manager.account_number
		self.archived_at = None
		self.in_active_campaign = None
		self.inserted_at = None
		self.is_global = None
		self.order = None
		self.provider = None
		self.provider_data = None
		self.provider_id = None
		self.provider_type = None
		self.question = None
		self.response_count = None
		self.responsed_count = None
		self.survey_type = None

	def as_dict(self):
		return {
			'id' : self.id,
			'type' : self.type,
			'attributes':{
					"account_id":self.account_id,
					"archived_at":self.archived_at,
					"in_active_campaign":self.in_active_campaign,
					"inserted_at":self.inserted_at,
					"is_global":self.is_global,
					"order":self.order,
					"provider":self.provider,
					"provider_data":self.provider_data,
					"provider_id":self.provider_id,
					"provider_type":self.provider_type,
					"question":self.question,
					"response_count":self.response_count,
					"responsed_count": self.responsed_count,
					"survey_type":self.survey_type,
			},
		}

	def from_dict(self, in_dict):
		self.inserted_at = in_dict['attributes'].get('inserted_at')
		self.id = in_dict['id'] 
		self.type = in_dict['type']
		self.account_id = in_dict['attributes']['account_id']
		self.campaign_id = in_dict['attributes'].get('campaign_id')
		self.archived_at = in_dict['attributes']['archived_at']
		self.in_active_campaign = in_dict['attributes']["in_active_campaign"]
		self.is_global = in_dict['attributes']['is_global']
		self.order = in_dict['attributes']['order']
		self.provider = in_dict['attributes']['provider']
		self.provider_data = in_dict['attributes']['provider_data']
		self.provider_id = in_dict['attributes']['provider_id']
		self.provider_type = in_dict['attributes']['provider_type']
		self.question = in_dict['attributes']['question']
		self.response_count = in_dict['attributes']['response_count']
		self.responsed_count = in_dict['attributes']['responsed_count']
		self.survey_type = in_dict['attributes']['survey_type']

	def reorder(self, order):
		try:
			order = int(order)
			if order < 0:
				print("Error: order has to be a non-negative integer. Got " + str(order))
		except (ValueError, TypeError) as e:
			print("Error: order has to be an integer. got " + str(order))
		payload = {'data':{'attributes':{'order':order}}}
		request, worked = self.safe_request('put', url=self.base_url+'/'+self.id+'/reorder', headers={}, data=payload)
		return worked

	def get_rid_of(self):
		pass


