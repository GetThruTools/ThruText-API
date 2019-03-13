#!/usr/bin/env python

import unittest
import os
from LoginManager import LoginManager
from LoginManager import TestLoginMethod

class TestEnvLogin(TestLoginMethod):
	"""
	Suite of tests to prove the environment log in method works
	"""

	def setUp(self):
		"""
		Saves the environment log ins, because we may trash them during the test
		"""
		self.saved_environ_un = os.environ['THRU_TEXT_API_UN']
		self.saved_environ_pw = os.environ['THRU_TEXT_API_PW']

	def tearDown(self):
		"""
		Restores the environment variable log ins. Avoids setting them if they weren't there before.
		"""
		if self.saved_environ_un is not None:
			os.environ['THRU_TEXT_API_UN'] = str(self.saved_environ_un)
		if self.saved_environ_pw is not None:
			os.environ['THRU_TEXT_API_PW'] = str(self.saved_environ_pw)

	def create_successful_login(self, tm, fatal_failure, redo):
		"""
		"""
		os.environ['THRU_TEXT_API_UN'] = str(self.saved_environ_un)
		os.environ['THRU_TEXT_API_PW'] = str(self.saved_environ_pw)
		tm.env_login(fatal_failure=fatal_failure, redo=redo, verbose=False)

	def create_failed_login(self, tm, fatal_failure, redo):
		os.environ['THRU_TEXT_API_UN'] = 'username' if self.saved_environ_un != 'username' else 'username2'
		os.environ['THRU_TEXT_API_PW'] = 'password' if self.saved_environ_pw != 'password' else 'getasecurepassword'
		tm.env_login(fatal_failure=fatal_failure, redo=redo, verbose=False)

del(TestLoginMethod)

if __name__ == '__main__':
	unittest.main()

