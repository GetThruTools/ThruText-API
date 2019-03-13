#!/usr/bin/env python

import getpass
import requests
import json
import os
import sys
import random

class LoginManager(object):
	"""
	Class used to log into ThruText and hold on to that token, along w/ some associated information.

	Ideally you'll only have one of these and pass it around to whoever needs it. 

	Standards:
	* There should be no cost in API to duplicate log ins unless you specify redo=True
	* Need to have redo option so you can change accounts
	* All log ins go through real_authenticate. real_authenticate sets self.token = the result.
	* if you set redo to true, and try to log in and fail, that sets the token to None
	
	"""

	def __init__(self, *, thru_text_account_name=None, staging=None, fake=False):
		"""
		A login manager remembers a token, whether or not you're in the staging environment or production, and what your account number is. All of those things are intrinsically tied to your login. Things that aren't intrinsic to your login should be handled elsewhere.
		input:
		thru_text_account_name (optional-ish) : name of the thru_text account to log into (ie, in elsonforemperor.thrutexttxt.io, elsonforemperor is the account name. If not specified, the value defaults to the environment variable THRU_TEXT_ACCOUNT_ID. This value needs to be specified in some way.
		"""
		self.token = None if not fake else 'fake'
		self.account_number = None
		self.default_login_method = 'env_login'
		if thru_text_account_name is not None:
			self.account_name = thru_text_account_name
		else:
			try:
				self.account_name = os.environ['THRU_TEXT_ACCOUNT_NAME']
			except KeyError:
				print ("ERROR: missing thru_text account name. Must either specify thru_text_account_name parameter or set environment variable THRU_TEXT_ACCOUNT_ID. Your thru_text account name is in your thru_text URLs (https://<ThruTextID>.relaytxt.io)")
				raise
		self.num_attempts = 0
		if staging is not None:
			self.staging = staging
		else:
			try:
				staging = os.environ['THRU_TEXT_STAGING']
			except KeyError:
				staging = False
			if staging:
				#this will be true if staging has ANY value.
				self.staging = True
			else:
				self.staging = False

	def real_authenticate(self, un, pw, fatal_failure=True, verbose=True):
		"""
		Performs the authentication.

		input: 
		username, password
		fatal_failure, boolean, whether you want a failed log in attempt to exit or return None

		returns: value of token if successful or None if not
		Also sets self.token = result of authentication
		"""

		# reset everything
		self.token = None
		self.account_number = None 
		if self.staging:
			auth_url = 'https://api.relaytxt-staging.io/v1/sessions'
		else:
			auth_url = 'https://api.relaytxt.io/v1/sessions'

		# do the request
		with requests.Session() as s:
			s.headers.update({
				'Accept':'application/vnd.api+json',
				'Content-Type' : 'application/vnd.api+json',
			})
			payload = {"data": {"attributes": {"email": un, "password": pw}}}
			login_response = s.post(url=auth_url, data=json.dumps(payload), headers={})
		self.num_attempts += 1

		# how'd it go?
		if login_response.status_code < 200 or login_response.status_code >= 300:
			if verbose:
				print("Error: Authorization attempt failed.")
				print("status code: " + str(login_response.status_code))
				print("headers: " + str(login_response.headers))
				print("content: " + str(login_response.content))
			if fatal_failure:
				sys.exit('Failed to authenticate')
			return None
		elif verbose:
			print("Successfully authorized!")

		# if we're here, it must have worked. get the relevant info
		response_dict = json.loads(login_response.content)
		try:
			for incl in response_dict['included']:
				if incl['type'] == 'account':
					self.account_number = incl['id']
		except KeyError:
			pass
		if self.account_number is None:
			if verbose:
				print("Error: Authorized, but couldn't find account number.")
			if fatal_failure:
				sys.exit("Authorized, but couldn't find account number.")
		try:
			self.token = response_dict['data']['attributes']['token']
		except KeyError:
			pass
		return self.token

	def terminal_login(self, fatal_failure=False, redo=False, max_tries=3, verbose=True):
		"""
		For use with command line or jupyter notebooks. No cost to duplicate attempts.
		input: 
		fatal_failure - boolean, do you want to exit on failure?
		redo - override previous log in
		output: 
		returns None or the token
		"""
		if self.token is not None and not redo:
			return self.token

		result = None
		tries = 0
		while result is None and tries < max_tries:
			un = getpass.getpass("Please enter your username:")
			pw = getpass.getpass("Please enter your password:")
			result = self.real_authenticate(un=un, pw=pw, fatal_failure=fatal_failure, verbose=verbose)
			tries += 1
		return result

	def env_login(self, fatal_failure=False, redo=False, verbose=True):
		"""
		Logs in via environment variables
		input:
		fatal_failure - boolean, do you want to exit on failure?
		redo - override previous log in
		output: 
		returns None or the token
		"""
		if self.token is not None and not redo:
			return self.token

		un, pw = None, None
		try:
			un = os.environ['THRU_TEXT_API_UN']
		except KeyError:
			print('ERROR: Missing environment variable THRU_TEXT_API_UN. Expected THRU_TEXT_API_UN and THRU_TEXT_API_PW')
		try:
			pw = os.environ['THRU_TEXT_API_PW']
		except KeyError:
			print('ERROR: Missing environment variable THRU_TEXT_API_PW. Expected THRU_TEXT_API_UN and THRU_TEXT_API_PW')
		if un is None or pw is None:
			#this is set to None to maintain symmetry w/ a failed log in attempt via real_authenticate
			#I could be persuaded that this is wrong, but I don't want someone to think they've switched accounts when they've actually failed the 2nd log in
			self.token = None
			return None
		else:
			return self.real_authenticate(un=un, pw=pw, fatal_failure=fatal_failure, verbose=verbose)

	def default_login(self, fatal_failure=False, redo=False):
		try:
			getattr(self, self.default_login_method)(fatal_failure=fatal_failure, redo=redo)
		except AttributeError:
			print("ERROR: missing method for default login " + str(self.default_login_method) + ".")
			raise

	def create_session(self, login_method=None, fatal_failure=False, redo=False):
		"""
		Creates a session based on this login manager
		"""
		if self.token is None or redo:
			if login_method is None:
				self.default_login(fatal_failure=fatal_failure, redo=redo)
			else:
				try:
					getattr(self, login_method)(self, fatal_failure=fatal_failure, redo=redo)
				except AttributeError:
					print("ERROR: missing method for login " + str(login_method) + ".")
					raise
		session = requests.Session()
		session.headers.update({
			'Accept':'application/vnd.api+json',
			'Content-Type' : 'application/vnd.api+json',
			'Authorization' : 'Token token="' + str(self.token) + '"',
		})
		return session
		
	def prove_token_works(self):
		"""
		Only used in testing
		"""
		try:
			s = self.create_session()
			if self.staging:
				test_url = 'https://api.relaytxt-staging.io/v1/accounts/'+str(self.account_number)+'/campaigns'
			else:
				test_url = 'https://api.relaytxt.io/v1/accounts/'+str(self.account_number)+'/campaigns'
			proof_response = s.get(url=test_url, headers={})
		finally:
			s.close()
		return proof_response.status_code >= 200 and proof_response.status_code < 300


import unittest

class TestLoginMethod(unittest.TestCase):
	"""
	Suite of tests a log in method has to pass. If you add a new log in method, create a class that inherits from this one to test it.
	"""

	def create_successful_login(self, lm, fatal_failure, redo):
		"""
		Successfully logs in, or prompts the user to successfully log in.
		"""
		pass

	def create_failed_login(self, lm, fatal_failure, redo):
		"""
		Unsuccessfully logs in, or prompts the user to fail to log in.
		"""
		pass

	def test_basic_login(self):
		"""
		Basic test - can you log in successfully?
		"""
		lm = LoginManager()
		assert lm.token is None
		self.create_successful_login(lm, fatal_failure=False, redo=True)
		assert lm.token is not None
		assert lm.prove_token_works()

	def test_basic_fail_login(self):
		"""
		If you fail to log in, have you really failed?
		Can you fail without it being a fatal failure?
		"""
		lm = LoginManager()
		assert lm.token is None
		try:
			self.create_failed_login(lm, fatal_failure=False, redo=True)
		except SystemExit:
			assert False
		assert lm.token is None

	def test_fatal_failure(self):
		"""
		Tests that the fatal_failure option is handled correctly
		"""
		caught_exception = False
		lm = LoginManager()
		assert lm.token is None
		try:
			self.create_failed_login(lm, fatal_failure=True, redo=True)
		except SystemExit:
			caught_exception = True
		assert caught_exception

	def test_not_redo_successes(self):
		"""
		If the same token manager is asked to log in multiple times while redo is false, it should do nothing.
		"""
		lm = LoginManager()
		assert lm.token is None
		self.create_successful_login(lm, fatal_failure=False, redo=False)
		previous_attempts = lm.num_attempts
		for test_number in range(2):
			self.create_successful_login(lm, fatal_failure=False, redo=False)
			assert lm.token is not None
			assert lm.prove_token_works()
			assert lm.num_attempts == previous_attempts

	def test_redo_successes(self):
		"""
		If you set redo=True, the token manager should try to log in each time.
		"""
		lm = LoginManager()
		assert lm.token is None
		previous_attempts = lm.num_attempts
		for test_number in range(2):
			self.create_successful_login(lm, fatal_failure=False, redo=True)
			assert lm.token is not None
			assert lm.prove_token_works()
			assert lm.num_attempts > previous_attempts
			previous_attempts = lm.num_attempts

	def test_redo_failures(self):
		"""
		If you set redo=True and fail to log in, that should wipe out the previous token.
		"""
		lm = LoginManager()
		assert lm.token is None
		previous_attempts = lm.num_attempts
		for works in [True, False, False]:
			if works:
				self.create_successful_login(lm, fatal_failure=False, redo=True)
				assert lm.token is not None
				assert lm.prove_token_works()
			else:
				self.create_failed_login(lm, fatal_failure=False, redo=True)
				assert lm.token is None
			assert lm.num_attempts > previous_attempts
			previous_attempts = lm.num_attempts

	def test_redo_random(self):
		"""
		A set of 5 random log ins
		"""
		lm = LoginManager()
		assert lm.token is None
		previous_attempts = lm.num_attempts
		for test_number in range(5):
			works = bool(random.getrandbits(1))
			if works:
				self.create_successful_login(lm, fatal_failure=False, redo=True)
				assert lm.token is not None
				assert lm.prove_token_works()
			else:
				self.create_failed_login(lm, fatal_failure=False, redo=True)
				assert lm.token is None
			assert lm.num_attempts > previous_attempts
			previous_attempts = lm.num_attempts

