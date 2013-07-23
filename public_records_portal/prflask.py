from flask import render_template, request, flash, redirect, url_for
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from public_records_portal import app, filters, prr, models
from filters import *
from prr import *
import json
import os
import inspect

# Initialize login
login_manager = LoginManager()
login_manager.init_app(app)

# Routing
routing = 
{
	'your_requests':'/your_requests'
	'index': '/',
	'explain_all_actions': '/actions',
	'new_request': '/new',
	'show_response': '/response/<int:request_id>',
	'show_request_for_x': '/<string:audience>/request/<int:request_id>',
	'show_request': '/request/<int:request_id>',
	'any_page': '/<page>',
	'requests': '/requests',
	'update_password': '/update_password',
	'logout': '/logout',
	'login': '/login',
	'add_a_resource': '/add_a_<string:resource>',
	'public_add_a_resource': '/public_add_a_<string:resource>',
	'update_a_resource': '/update_a_<string:resource>',
	'close': '/close'
}
# app.add_url_rule('/your_requests', your_requests)
# app.add_url_rule('/', 'index', index)
# app.add_url_rule('/actions', explain_all_actions)
# app.add_url_rule('/new', new_request)
# app.add_url_rule('/response/<int:request_id>', show_response)
# app.add_url_rule('/<string:audience>/request/<int:request_id>', show_request_for_x)
# app.add_url_rule('/request/<int:request_id>', show_request)
# app.add_url_rule('/<page>', any_page)
# app.add_url_rule('/requests', requests)
# app.add_url_rule('/update_password', update_password)
# app.add_url_rule('/logout', logout)

# # These are invoked from form submissions
# app.add_url_rule('/login', login)
# app.add_url_rule('/add_a_<string:resource>', add_a_resource)
# app.add_url_rule('/public_add_a_<string:resource>', public_add_a_resource)
# app.add_url_rule('/update_a_<string:resource>', update_a_resource)
# app.add_url_rule('/close', close)

#Functions
# Shows all public records requests that have been made by current owner. This doesn't work currently.
@login_required
def your_requests():
	app.add_url_rule(routing['your_requests'], your_requests)
	all_record_requests = []
	owner_resource = get_resource_filter("owner", [dict(name='user_id', op='eq', val=current_user.id)])
	if owner_resource:
		for owner in owner_resource['objects']:
			req_resource = get_resource_filter("request", [dict(name='current_owner', op='eq', val=owner['id'])])
			if req_resource['objects']:
				req = req_resource['objects'][0]
				all_record_requests.append(req)
	return render_template('all_requests.html', all_record_requests = all_record_requests, user_id = current_user.id, title = "Requests assigned to you")

# Let's start with the index page! For now we'll let the users submit a new request.
def index():
	if current_user.is_anonymous() == False:
		return redirect(your_requests())
	else:
		return redirect(url_for('new_request'))
index.methods = ['GET', 'POST']

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

def explain_all_actions():
	action_json = open(os.path.join(app.root_path, 'actions.json'))
	json_data = json.load(action_json)
	actions = []
	for data in json_data:
		actions.append("%s: %s" %(data, json_data[data]))
	return render_template('actions.html', actions = actions)

# They can always submit a new request by navigating here, but the index might change.
def new_request():
	if request.method == 'POST':
		request_text = request.form['request_text']
		if request_text == "":
			return render_template('error.html', message = "You cannot submit an empty request.")
		email = request.form['request_email']
		alias = None
		phone = None
		if 'request_alias' in request.form:
			alias = request.form['request_alias']
		if 'request_phone' in request.form:
			phone = request.form['request_phone']
		request_id, is_new = make_request(text = request_text, email = email, assigned_to_email = app.config['DEFAULT_OWNER_EMAIL'], assigned_to_reason = app.config['DEFAULT_OWNER_REASON'], user_id = get_user_id(), alias = alias, phone = phone)
		if is_new:
			return show_request(request_id, banner_msg = "Thanks! Your request has been uploaded.", template = "requested.html")
		return render_template('error.html', message = "Your request is the same as /request/%s" % request_id)
	else:
		return render_template('new_request.html', user_id = get_user_id())
new_request.methods = ['GET', 'POST']

# Returns a view of the case based on the audience. Currently views exist for city staff or general public.
def show_request_for_x(audience, request_id):
	if "city" in audience and current_user.is_anonymous():
		return render_template('alpha.html')
	return show_request(request_id = request_id, template = "manage_request_%s.html" %(audience))
show_request_for_x.methods = ['GET', 'POST']

def show_response(request_id):
	req = get_resource("request", request_id)
	if not req:
		return render_template('error.html', message = "A request with ID %s does not exist." % request_id)
	return render_template("response.html", req = req, user_id = get_user_id())

def show_request(request_id, template = None, record_uploaded = None, for_email_notification = False, banner_msg = None):
	req = get_resource("request", request_id)
	if not req:
		return render_template('error.html', message = "A request with ID %s does not exist." % request_id)
	if template:
		if "city" in template and not current_user_id:
			return render_template('alpha.html')
	else:
		template = "manage_request_public.html"
	if req['status'] and "Closed" in req['status']:
		template = "closed.html"
	return render_template(template, req = req, for_email_notification = for_email_notification, record_uploaded = record_uploaded, banner_msg = banner_msg, user_id = get_user_id())

@login_required
def add_a_resource(resource):
	if request.method == 'POST':
		resource_id = add_resource(resource = resource, request_body = request, current_user_id = current_user.id)
		if float(resource_id):
			return redirect(url_for('show_request_for_x', audience='city', request_id = request.form['request_id']))
		elif resource_id == False:
			return render_template('error.html')
		else:
			return render_template('help_with_uploads.html', message = resource_id)
	return render_template('error.html', message = "You can only update requests from a request page!")
add_a_resource.methods = ['GET', 'POST']

def public_add_a_resource(resource):
	if request.method == 'POST' and "note" in resource:
		resource_id = add_resource(resource = resource, request_body = request, current_user_id = None)
		if float(resource_id):
			return redirect(url_for('show_request_for_x', audience='public', request_id = request.form['request_id']))
	return render_template('error.html')
public_add_a_resource.methods = ['GET', 'POST']

def update_a_resource(resource):
	if request.method == 'POST':
		update_resource(resource, request)
		if current_user.is_anonymous() == False:
			return redirect(url_for('show_request_for_x', audience='city', request_id = request.form['request_id']))
		else:
			return redirect(url_for('show_request', request_id = request.form['request_id']))
	return render_template('error.html', message = "You can only update requests from a request page!")
update_a_resource.methods = ['GET', 'POST']

# Closing is specific to a case, so this only gets called from a case (that only city staff have a view of)
@login_required
def close(request_id = None):
	if request.method == 'POST':
		template = 'closed.html'
		request_id = request.form['request_id']
		close_request(request_id = request_id, reason = request.form['close_reason'], current_user_id = current_user.id)
		return show_request(request_id, template= template)
	return render_template('error.html', message = "You can only close from a requests page!")
close.methods=['GET', 'POST']

# Shows all public records requests that have been made.
def requests():
	all_record_requests = get_resources(resource = "request")
	if all_record_requests:
		return render_template('all_requests.html', all_record_requests = all_record_requests['objects'], user_id = get_user_id(), title = "All Requests")
	else:
		return index()


@login_manager.unauthorized_handler
def unauthorized():
	return render_template('alpha.html')

# test template:  I clearly don't know what should go here, but need to keep a testbed here.
@app.route('/test')
def show_test():
	return render_template('test.html')

def any_page(page):
	try:
		return render_template('%s.html' %(page), user_id = current_user_id)
	except:
		return render_template('error.html', message = "%s totally doesn't exist." %(page), user_id = get_user_id())

@login_manager.user_loader
def load_user(userid):
	user = models.User.query.get(userid)
	return user

def login(email=None, password=None):
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		if email_validation(email):
			user = create_or_return_user(email=email)
			if user.password == password:
				user_for_login = models.User.query.get(user.id)
				login_user(user_for_login)
				return index()
	return render_template('error.html', message = "Oops, your e-mail/ password combo didn't work.") 
login.methods = ['GET', 'POST']

def get_user_id():
	if current_user.is_anonymous() == False:
		return current_user.id
	return None

@login_required
def update_password(password=None):
	current_user_id = current_user.id
	if request.method == 'POST':
		try:
			password = request.form['password']
			user = models.User.query.get(current_user_id)
			user.password = password
			db.session.add(user)
			db.session.commit()
			return index()
		except:
			return render_template('error.html', message = "Something went wrong updating your password.")
	else:
		return render_template('update_password.html', user_id = current_user_id)
update_password.methods = ['GET', 'POST']

def logout():
	logout_user()
	return index()



# Routing
app.add_url_rule('/your_requests', your_requests)
app.add_url_rule('/', 'index', index)
app.add_url_rule('/actions', explain_all_actions)
app.add_url_rule('/new', new_request)
app.add_url_rule('/response/<int:request_id>', show_response)
app.add_url_rule('/<string:audience>/request/<int:request_id>', show_request_for_x)
app.add_url_rule('/request/<int:request_id>', show_request)
app.add_url_rule('/<page>', any_page)
app.add_url_rule('/requests', requests)
app.add_url_rule('/update_password', update_password)
app.add_url_rule('/logout', logout)

# These are invoked from form submissions
app.add_url_rule('/login', login)
app.add_url_rule('/add_a_<string:resource>', add_a_resource)
app.add_url_rule('/public_add_a_<string:resource>', public_add_a_resource)
app.add_url_rule('/update_a_<string:resource>', update_a_resource)
app.add_url_rule('/close', close)