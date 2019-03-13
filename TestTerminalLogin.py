#!/usr/bin/env python

import unittest
import os
from LoginManager import TestLoginMethod

class TestTerminalLogin(TestLoginMethod):
	"""
	Suite of tests to prove the environment log in method works
	"""

	def create_successful_login(self, tm, fatal_failure, redo):
		"""
		"""
		print("Please log in successfully")
		tm.terminal_login(fatal_failure=fatal_failure, redo=redo, max_tries=1, verbose=False)

	def create_failed_login(self, tm, fatal_failure, redo):
		print("Please FAIL to log in")
		tm.terminal_login(fatal_failure=fatal_failure, redo=redo, max_tries=1, verbose=False)

del(TestLoginMethod)

if __name__ == '__main__':
	unittest.main()

