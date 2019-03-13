#!/usr/bin/env python

import csv

def detect(filename, custom_list=None):
	if custom_list is None:
		custom_list = ',\t'
	with open(filename, 'rb') as to_sniff:
		try:
			dialect = csv.Sniffer().sniff(to_sniff.readline().decode('utf-8', 'replace'), delimiters=custom_list)
		except csv.Error:
			print("Warning: Can't detect seperator. Defaulting to tabs.")
			return '\t'
	return dialect.delimiter
