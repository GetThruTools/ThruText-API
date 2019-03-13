#!/usr/bin/env python

from ThruTextObject import ThruTextObject
import urllib2, os

class ThruTextExport(object):

	age_attribute = 'inserted'
	thru_text_type ='export'
	url_name='export'
	

	def initialize_values(self):
		self.export_of = export_of

		self.type = None
		self.id = None

		#attributes
		self.status = None
		self.end_date = None
		self.inserted = None # 2018-06-29T02:08:41.276564Z
		self.export_type = None
		self.campaign_id = None
		self.csv_url = None
		self.start_date = None


	def from_dict(self, inDict):

		self.type = inDict['type']
		self.id = inDict['id']

		#attributes
		self.status = inDict['attributes']['status']
		self.end_date = inDict['attributes']['end_date']
		self.start_date = inDict['attributes']['start_date']
		self.inserted = inDict['attributes']['inserted_at']
		self.export_type = inDict['attributes']['export_type']
		self.campaign_id = inDict['attributes']['campaign_id']
		self.csv_url = inDict['attributes']['csv_url']
	

	def as_dict(self):
		return {
			'type': self.type,
			'id' : self.id,
			'attributes': {
				'status':self.status,
				'end_date':self.end_date,
				'start_date':self.start_date,
				'inserted_at':self.inserted,
				'export_type':self.export_type,
				'campaign_id':self.campaign_id,
				'csv_url':self.csv_url,
			}
		}

	def download(self, filename, backup_dir):
		"""
		Downloads an export as filename to backupDir
		I don't have great error handling for this, to put it mildly
		"""
		attempt=0
		success = False
		while attempt < 3 and not success:
			try:
				getAWS = urllib2.urlopen(self.csvURL)
				html = getAWS.read()
				export_name = filename.replace('/','')
				export_name = exportName[:255]
				with open(os.path.join(backup_dir, export_name), 'wb') as f:
					f.write(html)
				success = True
			except:
				attempt += 1
		if success:
			print("Saved to " + str(os.path.join(backup_dir, export_name)))
		else:
			print("Failed to export " + str(filename))


