#!/usr/bin/env python

import json, os, yaml
from ThruTextCustomField import ThruTextCustomField
from AutoDetectSeperator import *

class CustomFieldInterp(object):

	"""
	Synonyms are not case sensitive. This is a slight departure from ThruText in which custom fields are case sensitive. So, if you were hoping to have two custom fields that are identical except for their capitalization, this class won't be work for you. 
	"""

	critical_field_codes = ['first_name', 'last_name', 'phone']

	def __init__(self, debug=False, login_manager=None):
		self.debug = debug 
		self.login_manager = login_manager
		self.codes_filename = 'custom_field_codes.json'
		self.code_to_id = None
		self.synonyms_filename = 'custom_field_synonyms.yaml'
		self.synonym_to_code = None

	def setup(self, redo_custom_fields=True, verbose=True):
		failures = 0
		check_for_codes_func = "get_code_to_id" if redo_custom_fields else "new_code_to_id"
		test_list = ["read_synonyms_file", check_for_codes_func, "compare_ids_to_synonyms", "reconcile_ids_codes_synonyms"]
		for test in test_list:
			if not getattr(self, test)(verbose=verbose):
				print("Failed " + str(test))
				failures += 1
		return failures == 0

	def read_synonyms_file(self, filename=None, verbose=True):
		"""
		Reads in a config file to determine what column headers to map to custom fields.
		input:
		filename (optional) - the name of the file to read. defaults to self.synonyms_filename
		The config file is a standard yaml file in the format:
		<custom_field_code>:
			- synonym1
			- synonym2
		<next_custom_field_code>:
			-synonym1
			-synonym2
		None of this is case sensitive.
		All custom field codes are their own synonym. eg, a column header of zip code will be mapped to zip code.
		take note of the names of the 3 critical fields - first_name, last_name, and phone
		It would be cool to notice duplicate keys, but yaml doesn't seem to be able to do that
		"""
		if filename is None:
			filename = self.synonyms_filename
		current_field_code = None
		self.synonym_to_code = {} 

		try:
			with open(os.path.join('config', filename), 'r') as ymlfile:
				cfg = yaml.load(ymlfile)
				if isinstance(cfg, str):
					print("Errror: Something went wrong reading yaml file.")
					return False
				for custom_field_code in cfg.keys():
					og_custom_field_code = custom_field_code
					custom_field_code = custom_field_code.lower()
					if custom_field_code in self.synonym_to_code:
						current_code = self.synonym_to_code[custom_field_code]
						if current_code != custom_field_code:
							print("Error: custom field code " + custom_field_code + " should be its own synonym, but it's also a synonym for code " + current_code)
							return False
					else:
						self.synonym_to_code[custom_field_code] = custom_field_code.lower()
					if cfg[og_custom_field_code] is None or len(cfg[og_custom_field_code]) == 0:
						if verbose:
							print("Warning: no synonyms listed for custom field " + str(current_field_code))
						continue
					for synonym in cfg[og_custom_field_code]:
						synonym = synonym.lower()
						if synonym in self.synonym_to_code:
							current_code = self.synonym_to_code[synonym]
							if current_code != custom_field_code:
								print("Error: " + synonym + " is listed as a synonym for " + custom_field_code + " but it's also a synonym for " + current_code)
								return False
						else:
							self.synonym_to_code[synonym] = custom_field_code
		except FileNotFoundError:
			print("Warning: no synonyms file " + str(filename) + " found in config folder!")
			return False
		return True 

	def get_code_to_id(self, verbose=True):
		result = True
		if not self.read_code_to_id(verbose=False):
			result = result and self.new_code_to_id()
			result = result and self.save_code_to_id()
		return result

	def new_code_to_id(self, verbose=True):
		rcf = ThruTextCustomField(login_manager=self.login_manager)
		custom_field_list = rcf.list_all()
		self.code_to_id = {}
		for cfl in custom_field_list:
			self.code_to_id[cfl.code.lower()] = cfl.id
		for critical_field in self.critical_field_codes:
			# add these to the id dict b/c they're real fields, but they don't have a normal id
			self.code_to_id[critical_field.lower()] = 0
		return self.save_code_to_id()

	def save_code_to_id(self, filename=None):
		if filename is None:
			filename = self.codes_filename
		try:
			with open(os.path.join('config', filename), 'w') as cf_file:
				cf_file.write(json.dumps(self.code_to_id))
		except FileNotFoundError:
			print("Error: couldn't write to " + os.path.join('config', filename) + " probably because the config folder is missing.")
			return False
		return True

	def read_code_to_id(self, filename=None, verbose=True):
		if filename is None:
			filename = self.codes_filename
		try:
			with open(os.path.join('config',filename), 'r') as ifile:
				try:
					self.code_to_id = json.loads(ifile.read())
					return True
				except json.JSONDecodeError:
					print("Error: can't read json from file " + str(filename) + " to create custom field code to id dictionary.")
		except FileNotFoundError:
			if verbose:
				print("Warning: can't find file " + str(filename))
		return False

	def compare_ids_to_synonyms(self, verbose=True):
		"""
			Things you might want to know:
			1. a custom field code appears in the synonyms file but not ThruText
			2. theres a custom filed in ThruText w/ no synonyms
		"""

		codes_with_synonyms = set(self.synonym_to_code.values())
		missing_synonyms = 0
		for code in self.code_to_id.keys():
			if code not in codes_with_synonyms:
				missing_synonyms += 1
				if verbose:
					print("Warning: code " + str(code) + " doesn't have any synonyms. It might be missing from your synonym file. It can only be included in groups by using its exact name as a column header.")
		if missing_synonyms > 0 and verbose:
			print("Missing synonyms for " + str(missing_synonyms) + " codes.")

		missing_ids = 0
		for code in codes_with_synonyms:
			if code not in self.code_to_id:
				missing_ids += 1
				if verbose:
					print("\n\nError: code " + str(code) + " has synonyms listed for it in the synonym file, but it doesn't exist in ThruText. The synonym file may be misformatted, you might be using custom field titles instead of codes, or the custom_field_codes.json file might be out of date. You can run new_code_to_id function, or delete your custom_field_codes.json file and start over. (This is NOT talking about your synonyms file. Don't delete that. The custom_field_codes file is automatically generated.)\n\n")
		if missing_ids > 0:
			print("Have synonyms for " + str(missing_ids) + " codes that aren't in ThruText.")

		return missing_ids == 0

	def reconcile_ids_codes_synonyms(self, verbose=True):
		"""
		Custom field codes are always their own synonyms. Any listed in the config file will be added to the synonym list automatically. But if a custom field code isn't in the config file, this function adds it to the list and checks to see if it's ambigious.
		"""
		ambigious = 0
		for adding_code in self.code_to_id.keys():
			current_code = self.synonym_to_code.get(adding_code)
			if current_code is not None and current_code != adding_code:
				print("Error: custom field code " + adding_code + " should be its own synonym, but it's also a synonym for custom field " + current_code)
				ambigious += 1
			else:
				self.synonym_to_code[adding_code] = adding_code
		return ambigious == 0

	def columns_to_mappings(self, first_row):

		#check that we've at least attempted to build synonyms and ids
		if self.synonym_to_code is None:
			print("Error: no synonyms created yet! Can't match columns to custom fields without them. Have you run setup()?")
			return None, None
		if self.code_to_id is None:
			print("Error: no ids created yet! Can't match columns to custom fields without them. Have you run setup()?")
			return None, None

		#initialize everything
		identified_codes = {}
		custom_fields_mapping = []
		critical_fields_mapping = {}
		if self.debug:
			print("Column Name -> ThruText Custom Field")

		# going column header by column header and matching them up w/ custom fields
		for index in range(len(first_row)):
			col_header = str(first_row[index]).lower()
			code = self.synonym_to_code.get(col_header)
			if code is None:
				# this is not a big deal. lots of csvs will have unused columsn
				if self.debug:
					print("Warning: couldn't find custom field code for column header " + str(col_header))
				continue
			elif code in identified_codes:
				#this is a big deal. ambigious column names are the #1 way things get messed up
				print("Error: already matched custom field " + str(code) + " with column " + str(identified_codes[code]) + " and it also matches " + str(col_header))
				return None, None
			else:
				# ok, found a good column_header -> code. proceeding on...
				if self.debug:
					print(str(col_header) + " -> " + str(code))
				identified_codes[code] = col_header

			# now that we have a good code, need to add it to a mapping.
			if code in self.critical_field_codes:
				# mapping for critical fields is really easy. code : index
				critical_fields_mapping[code] = index
			else:
				try:
					# mapping for custom fields is more complex b/c they have IDs
					custom_fields_mapping.append(
						{
							'custom_field_id':self.code_to_id[code], 
							'column':index
						}
					)
				except KeyError:
					print("ERROR: missing id for custom field code " + str(code) + ". This should have been caught during the compare_ids_to_synonyms() function. Did you run setup()?")
					return None, None
		# we've mapped all we're going to. let's make sure we got the critical fields...
		for critical in self.critical_field_codes:
			if critical not in identified_codes:
				print("ERROR: missing mapping for critical field " + str(critical) + ". Won't work in ThruText without first_name, last_name, and phone.")
				return None, None
		return custom_fields_mapping, critical_fields_mapping

import unittest
class TestCustomFieldInterp(unittest.TestCase):

	def test_setup(self, redo_custom_fields=True):
		def particpation_trophy(**kwargs):
			return True
		def real_life(**kwargs):
			return False
		cfi = CustomFieldInterp()
		cfi.read_synonyms_file = particpation_trophy
		cfi.get_code_to_id  = particpation_trophy
		cfi.new_code_to_id = real_life
		cfi.compare_ids_to_synonyms = particpation_trophy
		cfi.reconcile_ids_codes_synonyms = particpation_trophy
		assert cfi.setup()
	
	def test_read_synonyms_file_ambigious(self, filename=None):
		cfi = CustomFieldInterp()
		assert not cfi.read_synonyms_file(filename=os.path.join('testing', 'ambigious_cfi.yaml'))

	def test_read_synonyms_file_no_synonyms(self, filename=None):
		cfi = CustomFieldInterp()
		assert cfi.read_synonyms_file(filename=os.path.join('testing', 'no_synonyms.yaml'))

	def test_read_synonyms_file_no_file(self, filename=None):
		cfi = CustomFieldInterp()
		assert not cfi.read_synonyms_file(filename=os.path.join('testing', 'sir_not_appearing_in_this_folder.yaml'))

	def test_read_synonyms_file_no_misformatted(self, filename=None):
		cfi = CustomFieldInterp()
		assert not cfi.read_synonyms_file(filename=os.path.join('testing', 'not_a_real.yaml'))

	def test_new_code_to_id_actually_makes_file(self):
		pass

	def test_new_code_to_id_file_matches_ThruText(self):
		pass
	
	def test_save_code_to_id(self):
		og_dict = {'test' : True, 'dict' : True, 'Realistic' : False}
		cfi = CustomFieldInterp()
		cfi.code_to_id = og_dict
		assert cfi.save_code_to_id(filename=os.path.join('testing', 'code_to_id.json'))
		with open(os.path.join('config', 'testing', 'code_to_id.json'), 'r') as ifile:
			assert og_dict == json.loads(ifile.read())

	def test_read_code_to_id(self):
		cfi = CustomFieldInterp()
		assert cfi.read_code_to_id(filename=os.path.join('testing', 'code_to_id_valid_test.json'))

	def test_compare_ids_to_synonyms(self):
		cfi = CustomFieldInterp()
		print("No warnings.")
		cfi.code_to_id = {'code1' : 1, 'code2': 2, 'code3': 3}
		cfi.synonym_to_code = {'uno' : 'code1', 'eins' : 'code1', 'un' : 'code1', 'dos' : 'code2', 'drei' : 'code3'}
		assert cfi.compare_ids_to_synonyms()
		print("warning: 1 code with no synonyms.")
		cfi.code_to_id = {'code1' : 1, 'code2': 2, 'code3': 3}
		cfi.synonym_to_code = {'uno' : 'code1', 'eins' : 'code1', 'un' : 'code1', 'dos' : 'code2'}
		assert cfi.compare_ids_to_synonyms()
		print("Error: one synonym to a code that doesn't exist.")
		cfi.code_to_id = {'code1' : 1, 'code2': 2, 'code3': 3}
		cfi.synonym_to_code = {'uno' : 'code1', 'eins' : 'code1', 'un' : 'code1', 'dos' : 'code2', 'quatro' : 'code4'}
		assert not cfi.compare_ids_to_synonyms()

	def test_reconcile_ids_codes_synonyms(self):
		"""
		Custom field codes are always their own synonyms. Any listed in the config file will be added to the synonym list automatically. But if a custom field code isn't in the config file, this function adds it to the list and checks to see if it's ambigious.
		"""
		cfi = CustomFieldInterp()
		cfi.synonym_to_code = {'one' : 'code1', 'two' : 'code2'}
		cfi.code_to_id = {'code1': 1, 'code2': 2, 'code3' : 3, 'code4': 4}
		assert cfi.reconcile_ids_codes_synonyms()
		for c in ['code1', 'code2', 'code3', 'code4']:
			assert c in cfi.synonym_to_code
		cfi.synonym_to_code = {'one' : 'code1', 'two' : 'code2', 'code3' : 'code1'}
		cfi.code_to_id = {'code1': 1, 'code2': 2, 'code3' : 3, 'code4': 4}
		assert not cfi.reconcile_ids_codes_synonyms()

	def test_columns_to_mappings_works(self):
		cfi = CustomFieldInterp()
		cfi.synonym_to_code = {
			'one'   : 'code1', 
			'code1' : 'code1',
			'two'   : 'code2', 
			'code2' : 'code2',
			'first_name':'first_name', 
			'first':'first_name', 
			'last_name':'last_name',
			'last':'last_name',
			'phone' : 'phone',
			'phone_number' : 'phone',
		}
		cfi.code_to_id = {'code1': 1, 'code2': 2, 'code3' : 3, 'code4': 4}
		custom, critical= cfi.columns_to_mappings(['first', 'one', 'last', 'code2', 'fillibuster', 'democracy', 'phonez', 'phone'])
		cols_so_far = set()
		for c in custom:
			if c['column'] == 0:
				assert False # this is the first name
			elif c['column'] == 1:
				c['custom_field_id'] = 'code1'
			elif c['column'] == 2:
				assert False # this is the last name
			elif c['column'] == 3:
				c['custom_field_id'] = 'code2'
			elif c['column'] == 4:
				assert False # this is nothing
			elif c['column'] == 5:
				assert False # this is nothing
			elif c['column'] == 6:
				assert False # this is nothing
			elif c['column'] == 7:
				assert False # this is the phone number
			elif c['column'] > 7:
				assert False # too many columns yo
			cols_so_far.add(c['column'])
		assert len(cols_so_far) == len(custom)
		assert len(cols_so_far) == 2
		assert critical == {'first_name':0, 'last_name':2, 'phone':7}


	def test_columns_to_mappings_detect_empty(self):
		cfi = CustomFieldInterp()
		assert not cfi.columns_to_mappings()

	def test_columns_to_mappings_detect_empty(self):
		cfi = CustomFieldInterp()
		assert not cfi.columns_to_mappings()

	def test_columns_to_mappings_detect_empty(self):
		cfi = CustomFieldInterp()
		cfi.code_to_id = {'code1': 1, 'code2': 2, 'code3' : 3, 'code4': 4}
		custom, critical = cfi.columns_to_mappings(first_row=['first', 'last', 'phone', 'code1'])
		assert custom is None
		assert critical is None

	def test_columns_to_mappings_dupes(self):
		cfi = CustomFieldInterp()
		cfi.synonym_to_code = {
			'one' : 'code1', 
			'code1' : 'code1',
			'two' : 'code2', 
			'code2' : 'code2',
			'first_name':'first_name', 
			'first':'first_name', 
			'last_name':'last_name',
			'last':'last_name',
			'phone' : 'phone',
			'phone_number' : 'phone',
		}
		cfi.code_to_id = {
			'code1': 1, 
			'code2': 2, 
			'code3': 3, 
			'code4': 4,
		}
		custom, critical= cfi.columns_to_mappings(['first', 'one', 'last', 'code2', 'fillibuster', 'first_name', 'democracy', 'phonez', 'phone'])
		assert custom is None
		assert critical is None

if __name__ == '__main__':
	unittest.main()
