#!/usr/bin/env python

import json, pytz, yaml
from os.path import expanduser
from datetime import datetime

from LoginManager import LoginManager
from ThruTextObject import ThruTextObject
from ThruTextGroup import ThruTextGroup
from ThruTextSavedReply import ThruTextSavedReply
from ThruTextSurvey import ThruTextSurvey
from ThruTextRegion import ThruTextRegion

class ThruTextCampaign(ThruTextObject):

	url_name = 'campaigns'
	thru_text_type = 'campaign'

	acceptable_time_zones = ['US/Alaska', 'US/Aleutian', 'US/Arizona', 'US/Central', 'US/East-Indiana', 'US/Eastern', 'US/Hawaii', 'US/Indiana-Starke', 'US/Michigan', 'US/Mountain', 'US/Pacific', 'US/Pacific-New', 'US/Samoa']

	def initialize_values(self):
		self.backup_dir = expanduser('~') + '/Downloads'

		#top level
		self.id = None
		self.type = None

		#relationships
		self.followups = {}
		self.segments = {}
		self.campaign_tags = {}
		self.surveys = {}
		self.saved_replies = {}
		self.custom_fields = {}
		self.regions = {}

		#links
		self.links = None

		#attributes
		self.name = None
		self.opt_outs_count = None
		self.status = None
		self.open_time = None
		self.close_time = None
		self.conversations_count = None
		self.description = None
		self.end_date = None
		self.script = None
		self.country_id = None
		self.initial_sent = None
		self.time_zone = None
		self.unassigned_count= None
		self.open_time = None
		self.replies_count = None
		self.failure = None
		self.senders_count = None
		self.start_date = None

		self.region_dict = None

	def from_dict(self, in_dict):
		#top level
		self.id = in_dict['id']
		self.type = in_dict['type'] 

		#relationships
		self.followups = in_dict['relationships'].get('followups')
		self.segments = in_dict['relationships'].get('segments')
		self.campaign_tags = in_dict['relationships'].get('campaign_tags')
		self.surveys = in_dict['relationships'].get('surveys')
		self.saved_replies = in_dict['relationships'].get('saved_replies')
		self.custom_fields = in_dict['relationships'].get('custom_fields')
		self.regions = in_dict['relationships'].get('regions')

		#links
		self.links = in_dict['links']

		#attributes
		self.name = in_dict['attributes']['name']
		self.status = in_dict['attributes']['status']

		self.open_time = in_dict['attributes']['open_time']
		self.close_time = in_dict['attributes']['close_time']
		self.start_date = in_dict['attributes']['start_date']
		self.end_date = in_dict['attributes']['end_date']

		self.description = in_dict['attributes']['description']
		self.opt_outs_count = in_dict['attributes']['opt_outs_count']
		self.initial_sent_count = in_dict['attributes']['initial_sent_count']
		self.replies_count = in_dict['attributes']['replies_count']
		self.conversations_count = in_dict['attributes']['conversations_count']
		self.unassigned_count = in_dict['attributes']['unassigned_count']
		self.senders_count = in_dict['attributes']['senders_count']
		self.script = in_dict['attributes']['script']
		self.country_id = in_dict['attributes']['country_id']
		self.time_zone = in_dict['attributes']['time_zone']
		self.failure = in_dict['attributes']['apportionment_failed_reason']

	def as_dict(self):
		return {
			'id' : self.id,
			'type' : self.type,
			'relationships': {
				'followups' : self.followups,
				'segments' : self.segments,
				'campaign_tags' : self.campaign_tags,
				'surveys' : self.surveys,
				'saved_replies' : self.saved_replies,
				'custom_fields' : self.custom_fields,
				'regions' : self.regions,
			},
			'links': self.links,
			'attributes': {
				'name':self.name,
				'status':self.status,
				'open_time':self.open_time,
				'close_time':self.close_time,
				'start_date':self.start_date,
				'end_date':self.end_date,

				'description':self.description,
				'opt_outs_count':self.opt_outs_count,
				'initial_sent_count':self.initial_sent_count,
				'replies_count':self.replies_count,
				'conversations_count':self.conversations_count,
				'unassigned_count':self.unassigned_count,
				'senders_count':self.senders_count,
				'script':self.script,
				'country_id':self.country_id,
				'time_zone':self.time_zone,
				'apportionment_failed_reason':self.failure,
			}
		}

	def get_links(self):
		return self.links

	def get_relationships(self):
		return {
			'followups':self.followups,
			'segments':self.segments,
			'campaign_tags':self.campaign_tags,
			'surveys':self.surveys,
			'saved_replies':self.save_replies,
			'custom_fields':self.custom_fields,
			'regions':self.regions,
		}

	@property
	def exports_url(self):
		return self.base_url+'/'+self.id+'/exports'

	def get_exports(self):
		"""
		Returns a list of exports associated w/ this campaign
		doesn't create an export if none exist
		"""
		results = []
		export_response, working = self.safe_request('get', url=self.exports_url, headers = {})
		if not working:
			print("Error: Couldn't get surveys for " + self.name)
			return None
		exports_list_dict = json.loads(export_response.content)
		for eld in exports_list_dict['data']:
			try:
				results.append(ThruTextExport(eld))
			except KeyError:
				pass
		return results
#
	def start_export(self, export_type=None):
		"""
		Starts a new export of the specified type.
		If you don't specify a new one, defaults to surveys.
		As far as I know, exports are forever so... don't go crazy w/ this.
		"""
#
		if export_type is None:
			export_type = 'surveys'
		payload = {'data':{'attributes':{'export_type':export_type}}}
		export_response, working = self.safe_request('post', url=self.exports_url, headers={}, data=payload)
		if not working:
			print("Error: couldn't start export for " + str(self.name))
			return None

		try:
			return ThruTextExport(json.loads(export_response.content)['data'])
		except KeyError:
			return None
#
	def newest_export(self, export_type=None):
		"""
		Gets your surveys and returns the newest FINISHED one.
		If you specify an export type, 
		Only considers the exports of the specified type
		"""
		export_list = self.get_exports()
		if not isinstance(export_list, list):
			return None
		export_list.sort(key=lambda x: x.timestamp())
		try:
			return export_list[0]
		except IndexError:
			return None

		newest = None
		for el in export_list:
			if export_type is not None and el.export_type != export_type:
				continue
			elif el.timestamp() is None:
				continue
			elif newest is None:
				newest = el
			elif el.timestamp() > newest.timestamp():
				newest = el
		return newest

	def save_export(self, export_type=None, filename=None):
		"""
		Downloads the newest export
		if you don't specify the type, defaults to surveys
		"""
		exporting = export_type if export_type is not None else 'surveys'
		newest = self.newest_export(export_type=exporting)
		if newest is None:
			return False
		if filename is None:
			filename = self.name + '_' + exporting + '.csv'
		newest.download(filename=filename, backup_dir=self.backup_dir)
#
	def launch(self):
		mr, working = self.safe_request('post', url=self.url_base()+'/'+self.id+'/apportion', headers={}, data={})
		return working

	def get_rid_of(self, other_id=None):
		return self.archive(other_id)

	def valid_date(self, t, tz):
		"""
		t - datetime or string %Y-%m-%dT%H:%M%
		tz - string representing the time_zone of the campaign
		ALWAYS takes datetime as time_zone tz 
		"""
		if isinstance(t, (str, bytes)):
			try:
				dt = datetime.strptime(t, '%Y-%m-%dT%H:%M')
			except (ValueError, TypeError) as e:
				print("Error: couldn't use date " + str(t) + ", must be in format YYYY-MM-DDTHH:MM")
				return None
		elif isinstance(t, datetime):
			dt = t
		else:
			print("Error: Don't know how to deal w/ date of this type")
			return None
		dt = pytz.timezone(tz).localize(dt)
		return dt.isoformat()
		#return dt.strftime('%Y-%m-%dT%H:%M:00.00-00:00')

	def valid_24_hour_time(self, t):
		if isinstance(t, (str, bytes)):
			try:
				dt = datetime.strptime(t, '%H:%M')
			except (ValueError, TypeError) as e:
				print("Error: couldn't use 24 hour time " + str(t) + ", must be in format HH:MM")
				return None
		elif isinstance(t, datetime):
			dt = t
		else:
			print("Error: Don't know how to deal w/ 24 hour time of this type")
			return None
		return dt.strftime('%H:%M')

	def from_file(self, filename, group_id=None, segments=None, debug=False):
		with open(filename, 'r') as ymlfile:
			cfg = yaml.load(ymlfile)
			parameter_dict = {}
			for key in ['name', 'description', 'script', 'start_date', 'end_date', 'time_zone', 'open_time', 'close_time', 'regions']:
				parameter_dict[key] = cfg[key]
			for optional_key in ['group_id', 'segments', 'country_id', 'self_assign']:
				parameter_dict[optional_key] = cfg.get(optional_key)
			try:
				sa = parameter_dict['self_assign'].lower()
				if sa in ['true', 'y', 't', 'yes']:
					parameter_dict['self_assign'] = True
				elif sa in ['false', 'n', 'f', 'no']:
					parameter_dict['self_assign'] = False
				else:
					print("Error: don't understand self_assign value of " + str(sa))
					return False
			except KeyError:
				pass
			except AttributeError:
				print("Error: don't understand self_assign value of " + str(parameter_dict[optional_key]))
				return False
			parameter_dict['debug'] = debug 
			parameter_dict['group_id'] = group_id
			worked = self.make_new(**parameter_dict)
			if not worked:
				return False
			reply_list = []
			for sr in cfg['saved replies']:
				reply_list.append((sr['title'], sr['body']))
			survey_list = []
			for v in cfg['surveys']:
				survey_list.append((v['question'], v['type'], v.get('choices')))
			if debug:
				print("Successfully debugged campaign config file.")
				return True
			rsv = ThruTextSavedReply(login_manager=self.login_manager)
			for sr in reply_list:
				worked = rsv.make_new(title=sr[0], body=sr[1], campaign_id=self.id)
				if not worked:
					print("Error: failed to make saved reply " + str(sr))
					return False
			rv = ThruTextSurvey(login_manager=self.login_manager)
			for v in survey_list:
				worked = rv.make_new(question=v[0], survey_type=v[1], survey_choices=v[2], campaign_id=self.id)
				if not worked:
					print("Error: failed to make survey " + str(v))
					return False
			return True

	def make_new(self, name, description, start_date, end_date, time_zone, open_time, close_time, regions, script, self_assign=False, group_id=None, segments=None, country_id=None, debug=False):
		"""
		name - str - what to call the campaign
		description - str - <255 char description of what the campaign does. Is visible to senders.
		start_date - str (%Y-%m-%d) or datetime - when you want the senders to be able to start sending initial messages. Note: time_zone and time of day are ignored.
		end_date - str (%Y-%m-%d) or datetime - when you want the senders to stop being able to send NEW initial messages. Note: time_zone and time of day are ignored.
		time_zone - the time_zone the campaign is in. This is the time_zone all the values will display as. 
		open_time - the earliest time senders can send any type of message. In a 24 hour format, no TZ
		close_time - the lastest time senders can send any type of message. In a 24 hour format, no TZ
		regions - list of up to 3 reigons or area codes to send the messages from. Should be iterable, or a single item
		script - initial message for the campaign
		self_assign (optional) - specifies if the campaign will allow self-assignment. Defaults to false
		group_id (optional) - if you specify this, the campaign will be created w/ this group as it's base segment. You need to use exactly one of group_id or segements.
		segments (optional) - if you specify this, the campaign will be created w/ these segements. You need to use exactly one of group_id or segements.
		***I would strongly encourage you not to use the segements parameter, or to use it extremely sparingly.***
		If you need to make 50 campaigns w/ one group each and remove one other group from all of them, that's fine. If you're removing multiple groups from multiple other campaigns, or filtering several times, etc, it's very easy to mess up something minor and make broken campaigns.
		country_id (optional) - defaults to US, but you can specify something else here
	
		"""
		max_len = 255
		if len(name) > max_len:
			print("Warning: truncating name b/c it's too long.")
			name = name[:255]

		if len(description) > max_len:
			print("Warning: truncating description b/c it's too long.")
			description = description[:255]

		if len(script) > 320:
			print("Warning: initial message probably exceeds 2 segements.")

		if not time_zone in self.acceptable_time_zones:
			print("Error: time_zone is " + str(time_zone) + ". It needs to be one of the following strings: " + str(self.acceptable_time_zones))
			return False

		processed_start_date = self.valid_date(start_date, time_zone)
		if processed_start_date is None:
			print("Error: couldn't use start_date " + str(start_date))
			return False

		processed_end_date = self.valid_date(end_date, time_zone)
		if processed_end_date is None:
			print("Error: couldn't use end_date " + str(end_date))
			return False

		processed_open_time = self.valid_24_hour_time(open_time)
		if processed_open_time is None:
			print("Error: couldn't use open_time " + str(open_time))
			return False

		processed_close_time = self.valid_24_hour_time(close_time)
		if processed_close_time is None:
			print("Error: couldn't use close_time " + str(close_time))
			return False

		if isinstance(regions, str):
			regions = [regions]
		try:
			region_iter = iter(regions)
		except TypeError:
			regions = [regions]

		if self.region_dict is None:
			rr = ThruTextRegion(login_manager=self.login_manager)
			self.region_dict = rr.list_all()

		processed_regions = []
		index = 0
		for r in regions:
			try:
				nrr = ThruTextRegion(login_manager=self.login_manager)
				nrr.become_region(r, region_dict=self.region_dict)
				nrr.index = index
			except KeyError:
				print("Error: don't know region w/ name " + str(r))
				return False
			processed_regions.append(nrr.as_dict())
			index += 1
			if index > 4:
				break

		if len(processed_regions) < 1 or len(processed_regions) > 3:
			print("Error: need to specify between 1 and 3 regions / area codes. Found " + str(len(processed_regions)))
			return False

		if group_id is not None and segments is not None:
			print("Error: you can either use group_id or segments, but not both.")
			return False
		if group_id is None and segements is None:
			print("Error; you have to either use group_id or segments. Otherwise there's nothing to base the campaign on.")
			return False

		if group_id is not None:
			rg = ThruTextGroup(login_manager=self.login_manager)
			if not rg.become(group_id):
				print("Error: got group id " + str(group_id) + " but that's not a real group. Double check here: " + rg.display_url())
			segments = [
				{
					'segment_type' : 'add',
					'segment_source_type' : 'group',
					'order' : 0,
					'source_group_id' : group_id,
					"filter_surveys":[],
					"reply_status":"any",
				}
			]

		if debug:
			return True

		payload = {
			'data' : {
				'attributes' : {
					'name' : name,
					'description' : description,
					'country_id' : 'US',
					'start_date' : processed_start_date,
					'end_date' : processed_end_date,
					'time_zone' : time_zone,
					'open_time' : processed_open_time,
					'close_time' : processed_close_time,
					'regions' : processed_regions,
					'segments' : segments,
					'script' : script,
					'settings' : {
						"self_assignment":self_assign,
					},
				}
			}
		}

		new_campaign_response, worked = self.safe_request('post', url=self.base_url, data=payload, headers={})
		if not worked:
			print("Error: failed to make new campaign.")
			return False
		try:
			self.from_dict(json.loads(new_campaign_response.content)['data'])
		except json.JSONDecodeError:
			print("Warning: got something weird back from attempt to make new campaign. This campaign may not be an accurate representation of what's in ThruText")
		return True

