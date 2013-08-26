from datetime import datetime, timedelta
from helpers import format_date
from public_records_portal import app
import os
import json
from db_helpers import get_attribute, get_objs


def generate_prr_emails(request_id, notification_type, user_id = None):
	app_url = app.config['APPLICATION_URL'] 
	# Define the e-mail template:
	template = "generic_email.html" 
	if notification_type == "Request made":
		template = "new_request_email.html"
	# Get information on who to send the e-mail to and with what subject line based on the notification type:
	email_info = get_email_info(notification_type=notification_type)
	email_subject = "Public Records Request %s: %s" %(request_id, email_info["Subject"])
	recipient_types = email_info["Recipients"]
	page = "%srequest/%s" %(app_url,request_id) # The request URL
	include_unsubscribe_link = True 
	for recipient_type in recipient_types: 
		if "Staff" in recipient_type:
			page = "%scity/request/%s" %(app_url,request_id)
			include_unsubscribe_link = False # Gets excluded for city staff
		if recipient_type in ["Staff owner","Requester","Subscriber"]:
			if user_id:
				recipient = get_attribute(attribute = "email", obj_id = user_id, obj_type = "User")
				send_prr_email(page = page, recipients = [recipient], subject = email_subject, template = template, include_unsubscribe_link = include_unsubscribe_link)
			else:
				print "Can't send an e-mail out if no user exists."
		elif recipient_type == "Subscribers":
			subscribers = get_attribute(attribute = "subscribers", obj_id = request_id, obj_type = "Request")
			for subscriber in subscribers:
				recipient = get_attribute(attribute = "email", obj_id = subscriber.user_id, obj_type = "User")
				send_prr_email(page = page, recipients = [recipient], subject = email_subject, template = template, include_unsubscribe_link = include_unsubscribe_link) # Each subscriber needs to get a separate e-mail.
		elif recipient_type == "Staff participants":
			recipients = []
			participants = get_attribute(attribute = "owners", obj_id = request_id, obj_type = "Request")
			for participant in participants:
				recipient = get_attribute(attribute = "email", obj_id = participant.user_id, obj_type = "User")
				recipients.append(recipient)
			send_prr_email(page = page, recipients = recipients, subject = email_subject, template = template, include_unsubscribe_link = include_unsubscribe_link, cc_everyone = True)
		else:
			print recipient_type
			print "Not a valid recipient type"

def send_prr_email(page, recipients, subject, template, include_unsubscribe_link = True, cc_everyone = False):
	if recipients:
		try:
			if send_emails:
				send_email(body = render_template(template, page = page), recipients = recipients, subject = subject, include_unsubscribe_link = include_unsubscribe_link, cc_everyone = cc_everyone)
			else:
				print "%s to %s with subject %s" % (render_template(template, page = page), recipients, subject)
		except:
			print "E-mail was not sent."

def send_email(body, recipients, subject, include_unsubscribe_link = True, cc_everyone = False):
	mail = sendgrid.Sendgrid(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'], secure = True)
	sender = app.config['DEFAULT_MAIL_SENDER']
	plaintext = ""
	html = body
	message = sendgrid.Message(sender, subject, plaintext, html)
	if not include_unsubscribe_link:
		message.add_filter_setting("subscriptiontrack", "enable", 0)
	if cc_everyone:
		for recipient in recipients:
			message.add_cc(recipient)
	else:
		for recipient in recipients:
			message.add_to(recipient)
	message.add_bcc(sender)
	mail.web.send(message)

def due_date(date_obj, extended = None, format = True):
	days_to_fulfill = 10
	if extended == True:
		days_to_fulfill = days_to_fulfill + 14
	if not date_obj:
		return None
	if type(date_obj) is not datetime:
		date_obj = datetime.strptime(date_obj, "%Y-%m-%dT%H:%M:%S.%f")
	due_date = date_obj + timedelta(days = days_to_fulfill)
	if format:
		return format_date(due_date.date())
	return due_date.date()

def is_due_soon(date_obj, extended = None):
	current_date = datetime.now().date()
	due = due_date(date_obj = date_obj, extended = extended, format = False)
	num_days = 2
	if (current_date + timedelta(days = num_days)) == due:
		return True, due
	return False, due

def is_overdue(date_obj, extended = None):
	current_date = datetime.now().date()
	due = due_date(date_obj = date_obj, extended = extended, format = False)
	if (current_date >= due):
		return True, due
	return False, due

def get_email_info(notification_type):
	email_json = open(os.path.join(app.root_path, 'static/json/emails.json'))
	json_data = json.load(email_json)
	return json_data["Notification types"][notification_type]


def notify_due():
	requests = get_objs("Request")
	email_json = open(os.path.join(app.root_path, 'static/json/emails.json'))
	json_data = json.load(email_json)
	for req in requests:
		if "Closed" not in req.status:
			# Check if it is due in 2 days
			due_soon, date_due = is_due_soon(req.date_created, req.extended) 
			if due_soon:
				change_request_status(req.id, "Due soon")
				email_subject = "%sPublic Records Request %s: %s" %(test, req.id, json_data["Request due"])
			else:
				# Otherwise, check if it is overdue
				is_overdue, date_due = is_overdue(req.date_created, req.extended)
				if is_overdue:
					change_request_status(req.id, "Overdue")
					email_subject = "%sPublic Records Request %s: %s" %(test, req.id, json_data["Request overdue"])
				else:
					continue
			owner_uid = get_attribute(attribute = "user_id", obj_id = req.current_owner, obj_type = "Owner")	
			owner_email = get_attribute(attribute = "email", obj_id = owner_uid, obj_type = "User")
			recipients = [owner_email]
			backup_email = get_dept_backup(owner_email)
			if backup_email:
				recipients.append(backup_email)
			app_url = app.config['APPLICATION_URL']
			page = "%scity/request/%s" %(app_url,req.id)
			body = "You can view the request and take any necessary action at the following webpage: <a href='%s'>%s</a>.</br></br> This is an automated message. You are receiving it because you are listed as the Public Records Request Liaison, Backup or Supervisor for your department." %(page, page)
				# Need to figure out a way to pass in generic email template outside application context. For now, hardcoding the body.
			send_email(body = body, recipients = recipients, subject = email_subject, include_unsubscribe_link = False)