from datetime import datetime, timedelta
import os
from public_records_portal import app
import json
from jinja2 import Markup
from db_helpers import *
import notifications

def date_granular(timestamp):
	if not timestamp:
		return None
	if type(timestamp) is not datetime:
		timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
	delta = datetime.now() - timestamp
	days, hours, minutes, seconds = delta.days, delta.seconds//3600, delta.seconds//60, delta.seconds
	if days > 1:
		return "%s days ago" % days
	elif hours > 1:
		return "%s hours ago" % hours
	elif minutes > 1:
		return "%s minutes ago" % minutes
	elif seconds > 1:
		return "%s seconds ago" % seconds
	else:
		return "Just now."

def date(obj):
	if not obj:
		return None
	try:
		return format_date(obj.date())
	except: # Not a datetime object
		try:
			return format_date(datetime.strptime(obj, "%Y-%m-%dT%H:%M:%S.%f").date())
		except:
			return format_date(obj) # Just return the thing, maybe it's already a date

def timestamp(obj):
	return obj.strftime('%H:%M:%S')


def tutorial(section):
	# Get filepath for actions.json
	tutorial_filepath = os.path.join(app.root_path, 'static/json/tutorial.json')
	tutorial_json = open(tutorial_filepath)
	json_data = json.load(tutorial_json)
	explanation = json_data[section]
	return explanation

def explain_action(action, explanation_type = None):
	# Get filepath for actions.json
	actions_filepath = os.path.join(app.root_path, 'static/json/actions.json')
	action_json = open(actions_filepath)
	json_data = json.load(action_json)
	explanation = json_data[action]
	if explanation_type:
		return explanation[explanation_type]
	else:
		explanation_str = ""
		if 'What' in explanation:
			explanation_str = explanation_str + explanation['What']
		if 'Who' in explanation:
			explanation_str = explanation_str + " " + explanation['Who']
		if 'Action' in explanation:
			explanation_str = explanation_str + " " + explanation['Action']
		return explanation_str

# We don't use this anymore since we validate against the city directory, but this could be one way of doing it.
def email_validation(email):
	if email:
		name, domain = email.split("@")
		if domain in ['oakland.net', 'oaklandnet.com', 'codeforamerica.org', 'oaklandcityattorney.org']:
			return True
	return False

def format_date(obj):
	return obj.strftime('%b %d, %Y')

def new_lines(value):
	new_value = value.replace('\n','<br>\n')
	if value != new_value:
		return Markup(new_value)
	return value

def display_staff_participant(owner, request):
	if owner.id == request.current_owner:
		return None
	staff = get_obj("User",owner.user_id)
	if not staff:
		return None
	if staff.alias:
		return staff.alias
	else:
		return staff.email

def get_status(request, audience = "public"):
	if not request.status:
		return None
	status = request.status.lower()
	if audience == "public":
		if "closed" in status:
			return "closed"
		return "open"
	if "closed" in status:
		return "closed"
	else:
		due_soon, due_date = notifications.is_due_soon(request.date_created, request.extended) 
		if due_soon:
			return "due soon"
		else:
			overdue, due_date = notifications.is_overdue(request.date_created, request.extended)
			if overdue:
				return "overdue"
		return "open"
	return None

def get_status_icon(status):
	if status and status == "closed":
		return "icon-archive icon-light"
	return ""

