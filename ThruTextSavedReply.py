#!/usr/bin/env python

import json
from ThruTextObject import ThruTextObject
from LoginManager import LoginManager

class ThruTextSavedReply(ThruTextObject):
	"""
	"""

	age_attribute = 'updated_at'

	@property
	def url_name(self):
		if self.campaign_id is None:
			return 'saved_replies'
		else:
			return '/campaigns/'+str(self.campaign_id)+'/saved_replies'

	def delete(self):
		response, worked = self.safe_request('delete', url=self.base_url+'/'+self.id, headers={})
		return worked

	def make_new(self, title, body, campaign_id=None):
		"""
		title - the name of the saved reply (eg, Wrong Number)
		body - the text of the saved reply (Sorry about that! Can we get your info?)
		campaign_id (optional) - if you fill this in, the saved reply will be associated w/ a specific campaign. If you leave it blank, it will become a global saved reply, available on ALL campaigns.
		"""

		if title is None or body is None:
			print("Error: can't make a saved reply without a title and a body.")
			print("title: " + str(title))
			print("body: " + str(body))
			return False

		payload = {
			"data": {
				"attributes": {
					"title": title,
					"body": body,
					"is_opt_out":False
				}
			}
		}

		if campaign_id is None:
			payload['data']['relationships'] = {
				'account':{
					'data':{
						'type':'accounts',
						'id':account_id,
					}
				},
				'campaign':{
					'data':None
				}
			}
			payload['data']['type'] = 'saved-replies'
		else:
			payload['data']['attributes']["campaign_id"] = ''
		self.campaign_id = campaign_id
		response, worked = self.safe_request('post', url=self.base_url, headers={}, data=payload)
		if not worked:
			print("Error: failed to create new saved reply.")
			return False

		try:
			self.from_dict(json.loads(response.content)['data'])
		except json.JSONDecodeError:
			print("Warning: got something weird back from attempt to make new saved reply. This saved reply may not be an accurate representation of what's in ThruText")
		return True

	def initialize_values(self, in_dict=None, login_manager=None):
		self.id = None
		self.type = None
		self.campagin_id = None
		self.account_id = None
		self.body = None
		self.campaign_id = None
		self.order = None
		self.tag_id = None
		self.title = None
		self.updated_at = None
		self.user_id = None

	def as_dict(self):
		return {
			"attributes": {
				"account_id":self.account_id,
				"body":self.body,
				"campaign_id":self.campaign_id,
				"order":self.order,
				"tag_id":self.tag_id,
				"title":self.title,
				"updated_at":self.updated_at,
				"user_id":self.user_id,
			},
			"id":self.id,
			"type":self.type,
		}

	def from_dict(self, in_dict):
		self.id = in_dict['id']
		self.type = in_dict['type']
		self.account_id = in_dict['attributes']['account_id']
		self.body = in_dict['attributes']['body']
		self.campaign_id = in_dict['attributes']['campaign_id']
		self.order = in_dict['attributes']['order']
		self.tag_id = in_dict['attributes'].get('tag_id')
		self.title = in_dict['attributes']['title']
		self.updated_at = in_dict['attributes']['updated_at']
		self.user_id = in_dict['attributes'].get('user_id')

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


