#!/usr/bin/env python

import json, os

from ThruTextObject import ThruTextObject
from CustomFieldInterp import CustomFieldInterp
from AutoDetectSeperator import *
import pandas

class ThruTextGroup(ThruTextObject):
	"""
	Object that represents a group on the ThruText website.
	"""

	url_name = 'groups'
	age_attribute = None 
	thru_text_type = 'group'

	def initialize_values(self):
		self.type = None
		self.id = None
		self.figured_custom = None
		self.figured_critical = None

		#attributes
		self.status = None
		self.account_id = None
		self.country_id = None
		self.upload_failed_reason = None
		self.name = None

		#contacts
		self.contacts_invalid = None
		self.contacts_opted_out = None
		self.contacts_unvalidated = None
		self.contacts_valid = None

		#links
		self.links = None

		#relationships
		self.campaigns = None
		self.imports = None
		self.custom_fields = None

	def figure_out_mapping(self, columns, verbose=False):
		cfi = CustomFieldInterp(login_manager=self.login_manager)
		cfi.setup(verbose=verbose)
		self.figured_custom, self.figured_critical = cfi.columns_to_mappings(columns)
		if self.figured_custom is None and self.figured_critical is None:
			print("Error: couldn't figure out mapping for " + str(columns))
			return False
		return True
		
	def from_dataframe(self, group_name, df, line_by_line_func=None, country_id='US'):
		if self.figured_custom is None or self.figured_critical is None:
			self.figure_out_mapping(df.columns.values)
		csv_data = []
		csv_data.append(df.columns.values.tolist())
		for index, row in df.iterrows():
			raw_row = [v if not pandas.isnull(v) else '' for v in row.values]
			if line_by_line_func is not None:
				raw_row = line_by_line_func(raw_row)
				if raw_row is None:
					continue
			csv_data.append(raw_row)
		return self.make_new(name=group_name, custom_field_mapping=self.figured_custom, critical_field_mapping=self.figured_critical, csv_data=csv_data, country_id=country_id)

	def from_file(self, group_name, filename, line_by_line_func=None, country_id='US'):
		sep = detect(filename)
		df = pandas.read_csv(filename, sep=sep, encoding='utf-8', dtype=object)
		return self.from_dataframe(group_name=group_name, df=df, line_by_line_func=line_by_line_func, country_id=country_id)

	def make_new(self, name, custom_field_mapping, critical_field_mapping, csv_data, country_id='US'):
		"""
		Creates a new group in the website.
		name : what to call the group. <255 characters
		custom_field_mapping : which columns correspond to what custom fields. The custom fields are identified by their ID number. List of dicts, each dict has 2 keys: custom_field_id and column. both values are ints. The column is the matching 0 indexed column in the csv data
		[
			{
				'custom_field_id': id number of the custom field, 
				'column': the index of the column. starts at 0. ie, this 3rd column
			},
			{
				'custom_field_id': 2454914995, 
				'column': 3,
			},
		]
		critical_field_mapping : This is like the custom field mappings, but the 3 critical fields are always the same and are identified by their names rather than an id number. Dict with 3 keys, first_name, last_name, and phone. all 3 values are ints that are the matching 0 indexed column of the csv_data
		{
			"first_name" : 0,
			"last_name" : 1,
			"phone" : 2,
		}

		csv_data : 2-D list that is the csv. 
		[
			['first', 'last', 'phone', 'zip'],
			['John', 'Elson', '555-555-1234', '99000']
		]
		IMPORTANT: the 1st row is always the column headers. They get ignored. If you leave them out, you'll lose one row of data per csv.

		country_id : (optional) country_id for the group. Defaults to US
		"""

		payload = {
			'data' : {
				'attributes': {
					'name' : name,
					'country_id' : country_id,
					'time_zone' : "",
					'group_custom_fields': custom_field_mapping,
					'import': {
						'csv_data': csv_data,
						'mapping':critical_field_mapping,
					}
				}
			}
		}

		new_group_response, worked = self.safe_request('post', url=self.base_url, data=payload, headers={})
		if not worked:
			return False
		try:
			self.from_dict(json.loads(new_group_response.content)['data'])
		except json.JSONDecodeError:
			print("Warning: got something weird back from attempt to make new group. This group may not be an accurate representation of what's in ThruText")
		return True

	def get_rid_of(self, other_id=None):
		gid = other_id if other_id is not None else self.id
		payload = {'data':{'id': gid, 'attributes':{'status':'archived'}}}
		response, worked = self.safe_request('patch', url=self.base_url+'/'+str(gid), headers={}, data=payload)
		return worked

	def get_contacts(self):
		return {
			'unvalidated': self.contacts_unvalidated,
			'valid': self.contacts_valid,
			'opted_out': self.contacts_opted_out,
			'invalid':self.contacts_invalid,
		}

	def get_relationships(self):
		return {
			'campaigns':self.campaigns,
			'import':self.imports,
			'custom_fields':self.custom_fields,
		}

	def as_dict(self):
		return {
			'id' : self.id,
			'type' : self.type,
			'attributes' : {
				'status' : self.status,
				'account_id' : self.account_id,
				'country_id' : self.country_id,
				'upload_failed_reason': self.upload_failed_reason,
				'contact_counts' : self.get_contacts(),
				'name' : self.name,
			},
			'relationships' : self.get_relationships(),
			'links' : self.links,
		}

	def from_dict(self, in_dict):
		self.id = in_dict['id']
		self.type = in_dict['type']
		self.status =    in_dict['attributes']['status']
		self.account_id = in_dict['attributes']['account_id']
		self.country_id = in_dict['attributes']['country_id']
		self.upload_failed_reason =   in_dict['attributes']['upload_failed_reason']
		self.contacts_unvalidated = in_dict['attributes']['contact_counts']['unvalidated']
		self.contacts_valid = in_dict['attributes']['contact_counts']['valid']
		self.contacts_opted_out = in_dict['attributes']['contact_counts']['opted_out']
		self.contacts_invalid = in_dict['attributes']['contact_counts']['invalid']
		self.name = in_dict['attributes']['name']
		try:
			self.campaigns = in_dict['relationships']['campaigns']['data']
		except (KeyError, TypeError) as e:
			self.campaigns = in_dict['relationships']['campaigns']
		try:
			self.imports = in_dict['relationships']['import']['data']
		except (KeyError, TypeError) as e:
			self.imports = in_dict['relationships']['import']
		try:
			self.custom_fields = in_dict['relationships']['custom_fields']['data']
		except (KeyError, TypeError) as e:
			self.custom_fields = in_dict['relationships']['custom_fields']
		self.links = in_dict['links']

