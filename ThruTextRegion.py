#!/usr/bin/env python

import json, os
from ThruTextObject import ThruTextObject

class ThruTextRegion(ThruTextObject):

	age_attribute = None
	url_name = None

	def become_region(self, region, region_dict=None):
		if region_dict is None:
			region_dict = self.list_all() 
		self.name = region
		try:
			self.id = region_dict[str(region).lower()]
		except (KeyError, TypeError) as e:
			print("Error: can't find region for name " + str(region))
			return False
		return True

	def new_region_list(self, filename=None):
		if self.login_manager.staging:
			response, worked = self.safe_request('get', url='https://api.relaytxt-staging.io/v1/countries', headers={}, includes='regions')
		else:
			response, worked = self.safe_request('get', url='https://api.relaytxt.io/v1/countries', headers={}, includes='regions')
		if not worked:
			print("Error: failed to get the countries.")
			return False
		included_list = [{'id':n['id'], 'type':n['type'], 'name':n['attributes']['name']} for n in json.loads(response.content)['included']]
		if filename is None:
			filename = os.path.join('config', self.default_filename)
		with open(filename, 'w') as ofile:
			ofile.write(json.dumps(included_list))
		return self.format_region_dict(included_list)

	def format_region_dict(self, included_list):
		region_dict = {}
		for il in included_list:
			region_dict[il['name'].lower()] = il['id']
			code = self.get_code(il['name'])
			if code is not None:
				region_dict[code] = il['id']
		return region_dict

	def get_code(self, name):
		area_code = name[name.rfind('(')+1:name.rfind(')')]
		try:
			_ = int(area_code)
			return area_code
		except (TypeError, ValueError) as e:
			pass
		return None

	def list_all(self, filename=None, redo=False):
		if filename is None:
			filename = os.path.join('config', self.default_filename)
		if not redo:
			try:
				with open(filename, 'r') as ifile:
					included_list = json.loads(ifile.read())
				return self.format_region_dict(included_list)
			except FileNotFoundError:
				pass
		return self.new_region_list(filename)

	def initialize_values(self):
		self.index = None
		self.name = None
		self.id = None
		self.type = None
		self.default_filename ='thru_text_region_list.cfg'

	def from_dict(self, in_dict):
		self.id = in_dict['id']
		self.type = in_dict['type']
		self.name = in_dict['name']
		self.index = in_dict.get('index')

	def as_dict(self):
		out_dict = {}
		for attr in ['id', 'type', 'name', 'index']:
			if getattr(self, attr) is not None:
				out_dict[attr] = getattr(self, attr)
		return out_dict

	def get_rid_of(self, other_id=None):
		print("Error: you can't get rid of a region.")
		return False

	def make_new(self):
		print("Error: you can't make new regions.")
		return False

	
