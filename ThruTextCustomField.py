#!/usr/bin/env python

from ThruTextObject import ThruTextObject
from LoginManager import LoginManager
import json

class ThruTextCustomField(ThruTextObject):
	"""
	not implemented - updating, deleting
	"""

	url_name = 'custom_fields'
	ageAttribute = None

	def initialize_values(self, in_dict=None, login_manager=None):
		self.id = None
		self.type = None

		#attributes
		self.code = None
		self.accountId = None
		self.title = None
		self.has_data = None


	def from_dict(self, in_dict):
		self.id = in_dict['id']
		self.type = in_dict['type']

		#attributes
		self.code = in_dict['attributes']['code']
		self.account_id = in_dict['attributes']['account_id']
		self.title = in_dict['attributes']['title']
		self.has_data = in_dict['attributes'].get('has_data')

	def as_dict(self):
		return {
			'id':self.id,
			'type':self.type,
			'attributes': {
				'code' : self.code,
				'account_id' : self.account_id,
				'title' : self.title,
				'has_data' : self.has_data,
			}
		}

	def make_new(self, *, title=None, code=None):
		"""
		title: what the custom field is. eg, Polling Location
		code: the string that gets substitued in the text message. eg, poll_loc
		"""
		if title is None or code is None:
			print("Error: can't make custom field without a title and a code.")
			return False

		payload = {'data':{'attributes':{'title':title, 'code':code}}}
		response, worked = self.safe_request('post', url=self.base_url, headers={}, data=payload)
		if not worked:
			print("Error: failed to make new custom field.")
			return False
		try:
			self.from_dict(json.loads(response.content)['data'])
		except json.JSONDecodeError:
			print("Warning: got something weird back from attempt to make new custom field. This custom field may not be an accurate representation of what's in ThruText")
		return True

	def get_rid_of(self):
		pass


