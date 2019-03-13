# Thrutext-API

login manager - log into ThruText. Either configure env variables to do it, or log in at the terminal, or by function.

CustomFieldInterp - write a yaml file that maps your custom field codes to a list of synonyms. Put it in the config file and name it custom_field_codes.json. Now as long as your column headers are synonyms of a custom field, they'll be mapped in automatically.

ThruTextGroup - make a group out of csv file, or a dataframe. integrated w/ custom field interp so you don't have to worry about mapping things. Look at the juptyer notebooks for examples of how you can debug this easily to make sure you always know what fields you'll have.

ThruTextCampaign - make campaings based on yaml files, or update them on the fly.

All ThruText objects come with 
list_all() - shows all of that type of object. accepts includes as a parameter
safe_request - a wrapper around the request dict that shows debugging info. you don't have to use it, but these files do
become(id) - makes this object a copy of the object w/ this id. you'll frequently list all of something, then filter them based on some criteria, and then become the relevant one.
get_rid_of
as_dict/from_dict - turns them into a dict, or creates one based on a dict

