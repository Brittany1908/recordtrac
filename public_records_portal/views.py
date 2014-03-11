"""Contains all functions that render templates/html for the app.
"""

from flask import render_template, request, redirect, url_for, jsonify
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from public_records_portal import app
from filters import *
from prr import add_resource, update_resource, make_request, close_request, get_request_table_data
from db_helpers import *
import departments
import os, json
from urlparse import urlparse, urljoin
from notifications import send_prr_email
from spam import is_spam, is_working_akismet_key
from requests import get
from time import time
from flask.ext.cache import Cache
from recaptcha.client import captcha
from timeout import timeout

# Initialize login
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize cache
cache = Cache()
cache.init_app(app, config={'CACHE_TYPE': 'simple'})

# Set flags:

check_for_spam = True
if app.config['ENVIRONMENT'] == 'PRODUCTION':
	check_for_spam = True

# Submitting a new request
def new_request(passed_recaptcha = False, data = None):
	if data or request.method == 'POST':
		if not data and not passed_recaptcha:
			data = request.form.copy()
		email = data['request_email']
		request_text = data['request_text']
		if request_text == "":
			return render_template('error.html', message = "You cannot submit an empty request.")
		if email == "" and 'ignore_email' not in data and not passed_recaptcha:
			return render_template('missing_email.html', form = data, user_id = get_user_id())
		if check_for_spam and is_spam(request_text) and not passed_recaptcha:
			return render_template('recaptcha.html', form = data, message = "Hmm, your request looks like spam. To submit your request, type the numbers or letters you see in the field below.", public_key = app.config['RECAPTCHA_PUBLIC_KEY'])
		alias = None
		phone = None
		if 'request_alias' in data:
			alias = data['request_alias']
		if 'request_phone' in data:
			phone = data['request_phone']
		request_id, is_new = make_request(text = request_text, email = email, user_id = get_user_id(), alias = alias, phone = phone, passed_recaptcha = passed_recaptcha, department = data['request_department'])
		if is_new:
			return redirect(url_for('show_request_for_x', request_id = request_id, audience = 'new'))
		if not request_id:
			return render_template('error.html', message = "Your request looks a lot like spam.")
		app.logger.info("\n\nDuplicate request entered: %s" % request_text)
		return render_template('error.html', message = "Your request is the same as /request/%s" % request_id)
	else:
		doc_types = os.path.exists(os.path.join(app.root_path, 'static/json/doctypes.json'))
		return render_template('new_request.html', doc_types = doc_types, user_id = get_user_id())

def index():
	if current_user.is_anonymous() == False:
		return redirect(url_for('requests'))
	else:
		return landing()

def landing():
	viz_data_freq, viz_data_time = get_viz_data()
	return render_template('landing.html', viz_data_freq = json.dumps(viz_data_freq), viz_data_time = json.dumps(viz_data_time), user_id = get_user_id())

def viz():
	viz_data_freq, viz_data_time = get_viz_data()
	return render_template('viz.html', viz_data_freq = json.dumps(viz_data_freq), viz_data_time = json.dumps(viz_data_time))

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

def explain_all_actions():
	action_json = open(os.path.join(app.root_path, 'static/json/actions.json'))
	json_data = json.load(action_json)
	actions = []
	for data in json_data:
		actions.append("%s: %s" %(data, json_data[data]["What"]))
	return render_template('actions.html', actions = actions)

# Returns a view of the case based on the audience. Currently views exist for city staff or general public.
def show_request_for_x(audience, request_id):
	if "city" in audience and current_user.is_anonymous():
		return render_template('alpha.html')
	return show_request(request_id = request_id, template = "manage_request_%s.html" %(audience))
show_request_for_x.methods = ['GET', 'POST']

def show_response(request_id):
	req = get_obj("Request", request_id)
	if not req:
		return render_template('error.html', message = "A request with ID %s does not exist." % request_id)
	return render_template("response.html", req = req, user_id = get_user_id())

def track(request_id = None):
	if request.method == 'POST':
		if not request_id:
			request_id = request.form['request_id']
		return redirect(url_for('show_request', request_id = request_id))
	else:
		return render_template("track.html")

def unfollow(request_id, email):
	success = False
	user_id = create_or_return_user(email.lower())
	subscriber = get_subscriber(request_id = request_id, user_id = user_id)
	if subscriber:
		success = update_obj(attribute = "should_notify", val = False, obj = subscriber)
	if success:
		return show_request(request_id = request_id, template = "manage_request_unfollow.html")
	else:
		return render_template('error.html', message = "Unfollowing this request was unsuccessful. You probably weren't following it to begin with.")

def show_request(request_id, template = None):
	current_user_id = get_user_id()
	req = get_obj("Request", request_id)
	if not req:
		return render_template('error.html', message = "A request with ID %s does not exist." % request_id)
	if template:
		if "city" in template and not current_user_id:
			return render_template('alpha.html')
	else:
		template = "manage_request_public.html"
	if req.status and "Closed" in req.status and template != "manage_request_feedback.html":
		template = "closed.html"
	return render_template(template, req = req, user_id = get_user_id())

def docs():
	return redirect('http://codeforamerica.github.io/public-records/docs/1.0.0')

@login_required
def edit_case(request_id):
	req = get_obj("Request", request_id)
	return render_template("edit_case.html", req = req, user_id = get_user_id())

@login_required
def add_a_resource(resource):
	if request.method == 'POST':
		resource_id = add_resource(resource = resource, request_body = request, current_user_id = current_user.id)
		if type(resource_id) == int or str(resource_id).isdigit():
			app.logger.info("\n\nSuccessfully added resource: %s with id: %s" % (resource, resource_id))
			return redirect(url_for('show_request_for_x', audience='city', request_id = request.form['request_id']))
		elif resource_id == False:
			app.logger.info("\n\nThere was an issue with adding resource: %s" % resource)
			return render_template('error.html')
		else:
			app.logger.info("\n\nThere was an issue with the upload: %s" % resource_id)
			return render_template('help_with_uploads.html', message = resource_id)
	return render_template('error.html', message = "You can only update requests from a request page!")

def public_add_a_resource(resource):
	if request.method == 'POST':
		if 'note' in resource or 'subscriber' in resource: 
			resource_id = add_resource(resource = resource, request_body = request, current_user_id = None)
			if type(resource_id) == int:
				request_id = request.form['request_id']
				audience = 'public'
				if 'subscriber' in resource:
					audience = 'follower'
				return redirect(url_for('show_request_for_x', audience=audience, request_id = request_id))
	return render_template('error.html')

def update_a_resource(resource):
	if request.method == 'POST':
		update_resource(resource, request)
		if current_user.is_anonymous() == False:
			return redirect(url_for('show_request_for_x', audience='city', request_id = request.form['request_id']))
		else:
			return redirect(url_for('show_request', request_id = request.form['request_id']))
	return render_template('error.html', message = "You can only update requests from a request page!")

# Closing is specific to a case, so this only gets called from a case (that only city staff have a view of)
@login_required
def close(request_id = None):
	if request.method == 'POST':
		template = 'closed.html'
		request_id = request.form['request_id']
		close_request(request_id = request_id, reason = request.form['close_reason'], user_id = current_user.id)
		return show_request(request_id, template= template)
	return render_template('error.html', message = "You can only close from a requests page!")

# Shows all public records requests that have been made.
@timeout(seconds=25)
def requests():
	try:
		departments_json = open(os.path.join(app.root_path, 'static/json/list_of_departments.json'))
		list_of_departments = json.load(departments_json)
		departments = sorted(list_of_departments, key=unicode.lower)
		my_requests = False
		requester_name = ""
		dept_selected = "All departments"
		open_requests = True
		if request.method == 'GET':
			filters = request.args.copy()
			if not filters:
				if not current_user.is_anonymous():
					my_requests = True
					filters['owner'] = current_user.id
				filters['status'] = 'open'
			else:
				if 'department' in filters and filters['department'].lower() == 'all':
					del filters['department']
				if not ('status' in filters and filters['status'].lower() == 'open'):
					open_requests = False
				if 'department' in filters:
					dept_selected = filters['department']
				if 'owner' in filters and not current_user.is_anonymous():
					my_requests = True
				if 'requester' in filters and current_user.is_anonymous():
					del filters['requester']
		record_requests = get_request_table_data(get_requests_by_filters(filters))
		user_id = get_user_id()
		if record_requests:
			template = 'all_requests.html'
			if user_id: 
				template = 'all_requests_city.html'
		else:
			template = "all_requests_noresults.html"
		total_requests_count = get_count("Request")
		return render_template(template, record_requests = record_requests, user_id = user_id, title = "All Requests", open_requests = open_requests, departments = departments, dept_selected = dept_selected, my_requests = my_requests, total_requests_count = total_requests_count, requester_name = requester_name)
	except Exception, message:
		if "Too long" in message:
			message = "Loading requests is taking a while. Try exploring with more restricted search options."
			app.logger.info("\n\nLoading requests timed out.")
		return render_template('error.html', message = message, user_id = get_user_id())


@login_manager.unauthorized_handler
def unauthorized():
	return render_template('alpha.html')

@login_manager.user_loader
def load_user(userid):
	user = get_obj("User", userid)
	return user


# test template:  I clearly don't know what should go here, but need to keep a testbed here.
@app.route('/test')
def show_test():
	return render_template('test.html')

def any_page(page):
	try:
		return render_template('%s.html' %(page), user_id = get_user_id())
	except:
		return render_template('error.html', message = "%s totally doesn't exist." %(page), user_id = get_user_id())

def tutorial():
	user_id = get_user_id()
	app.logger.info("\n\nTutorial accessed by user: %s." % user_id)
	return render_template('tutorial.html', user_id = user_id)

def login(email=None, password=None):
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		user_to_login = authenticate_login(email, password)
		if user_to_login:
			login_user(user_to_login)
			redirect_url = get_redirect_target()
			if 'login' in redirect_url or 'logout' in redirect_url:
				return redirect(url_for('index'))
			else:
				if "city" not in redirect_url:
					redirect_url = redirect_url.replace("/request/", "/city/request/")
				return redirect(redirect_url)
		else:
			app.logger.info("\n\nLogin failed (due to incorrect e-mail/password combo) for email: %s." % email)
			return render_template('error.html', message = "Your e-mail/ password combo didn't work. You can always <a href='/reset_password'>reset your password</a>.")
	app.logger.info("\n\nLogin failed for email: %s." % email)
	return render_template('error.html', message="Something went wrong.")

def reset_password(email=None):
	if request.method == 'POST':
		email = request.form['email']
		password = set_random_password(email)
		if password:
			send_prr_email(page = app.config['APPLICATION_URL'], recipients = [email], subject = "Your temporary password", template = "password_email.html", include_unsubscribe_link = False, password = password)
			app.logger.info("\n\nPassword reset sent for email: %s." % email)
			message = "Thanks! You should receive an e-mail shortly with instructions on how to login and update your password."
		else:
			app.logger.info("\n\nPassword reset attempted and denied for email: %s." % email)
			message = "Looks like you're not a user already. Currently, this system requires logins only for city employees. "
	return render_template('reset_password.html', message = message)


@login_required
def update_password(password=None):
	if request.method == 'POST':
		if set_password(current_user, request.form['password']):
			return index()
		app.logger.info("\n\nFailure updating password for user " % current_user.id)
		return render_template('error.html', message = "Something went wrong updating your password.")
	else:
		app.logger.info("\n\nSuccessfully updated password for user " % current_user.id)
		return render_template('update_password.html', user_id = current_user.id)

def staff_card(user_id):
	return render_template('staff_card.html', uid = user_id)

def logout():
	logout_user()
	return index()

def get_user_id():
	if current_user.is_anonymous() == False:
		return current_user.id
	return None

# Used as AJAX POST endpoint to check if new request text contains certain keyword
# See new_requests.(html/js)
def is_public_record():
	request_text = request.form['request_text']
	not_records_filepath = os.path.join(app.root_path, 'static/json/notcityrecords.json')
	not_records_json = open(not_records_filepath)
	json_data = json.load(not_records_json)
	request_text = request_text.lower()
	app.logger.info("Someone input %s" %(request_text))
	if "birth" in request_text or "death" in request_text or "marriage" in request_text:
		return json_data["Certificate"]
	if "divorce" in request_text:
		return json_data["Divorce"]
	return ''

def get_redirect_target():
	""" Taken from http://flask.pocoo.org/snippets/62/ """
	for target in request.values.get('next'), request.referrer:
		if not target:
			continue
		if is_safe_url(target):
			return target

def is_safe_url(target):
	""" Taken from http://flask.pocoo.org/snippets/62/ """
	ref_url = urlparse(request.host_url)
	test_url = urlparse(urljoin(request.host_url, target))
	return test_url.scheme in ('http', 'https') and \
		ref_url.netloc == test_url.netloc


def recaptcha():
	if request.method == 'POST':
		response = captcha.submit(
			request.form['recaptcha_challenge_field'],
			request.form['recaptcha_response_field'],
			app.config['RECAPTCHA_PRIVATE_KEY'],
			request.remote_addr
			)
		if not response.is_valid:
			message = "Invalid. Please try again."
			return render_template('recaptcha.html', message = message, public_key = app.config['RECAPTCHA_PUBLIC_KEY'], form = request.form)
		else:
			return new_request(passed_recaptcha = True, data = request.form)
	else:
		app.logger.info("\n\nAttempted access to recaptcha not via POST")
		return render_template('error.html', message = "You don't need to be here.")

def well_known_status():
    '''
    '''
    response = {
        'status': 'ok',
        'updated': int(time()),
        'dependencies': ['Akismet', 'Scribd', 'Sendgrid', 'Postgres'],
        'resources': {}
        }
    
    #
    # Try to connect to the database and get the first user.
    #
    try:
        if not get_obj('User', 1):
            raise Exception('Failed to get the first user')
        
    except Exception, e:
        response['status'] = 'Database fail: %s' % e
        return jsonify(response)
    
    #
    # Try to connect to Akismet and see if the key is valid.
    #
    try:
        if not is_working_akismet_key():
            raise Exception('Akismet reported a non-working key')
        
    except Exception, e:
        response['status'] = 'Akismet fail: %s' % e
        return jsonify(response)
    
    #
    # Try to ask Sendgrid how many emails we have sent in the past month.
    #
    try:
        url = 'https://sendgrid.com/api/stats.get.json?api_user=%(MAIL_USERNAME)s&api_key=%(MAIL_PASSWORD)s&days=30' % app.config
        got = get(url)
        
        if got.status_code != 200:
            raise Exception('HTTP status %s from Sendgrid /api/stats.get' % got.status_code)
        
        mails = sum([m['delivered'] + m['repeat_bounces'] for m in got.json()])
        response['resources']['Sendgrid'] = 100 * float(mails) / int(app.config.get('SENDGRID_MONTHLY_LIMIT') or 40000)
        
    except Exception, e:
        response['status'] = 'Sendgrid fail: %s' % e
        return jsonify(response)
    
    return jsonify(response)
