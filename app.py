from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import base64
import json
import smtplib

app = Flask(__name__)
app.config['SECRET_KEY'] = "Happy"
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return User.get(user_id)

class LoginForm(FlaskForm):
	username = StringField('Email Id', validators = [InputRequired(), Email()])
	password = PasswordField('Password', validators = [InputRequired()])
	remember = BooleanField('Remember me')

class DashForm(FlaskForm):
	dash_id = StringField('', validators = [InputRequired()])

class WForm(FlaskForm):
	w_id = StringField('', validators = [InputRequired()])

class MForm(FlaskForm):
	m_id = StringField('', validators = [InputRequired()])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
	form = LoginForm()
	global global_user, global_password
	global_user = form.username.data
	global_password = form.password.data

	if form.validate_on_submit():
		return redirect(url_for('workspaceId')) # redirect to First Page for Processes and Import Actions
	
	return render_template('login.html', form=form)

@app.route('/workspaceId', methods = ['GET', 'POST'])
def workspaceId():
	formw = WForm()
	name = global_user

	credentials = global_user + ":" + global_password

	user = 'Basic ' + str(base64.b64encode(credentials).encode('utf-8').decode('utf-8'))

	getHeaders = {
    		'Authorization': user,
    		'Content-Type' : 'application/json'
	}

	workspace_names = requests.get('https://api.anaplan.com/1/3/workspaces/', headers = getHeaders, data=json.dumps({'localeName': 'en_US'}))

	#showing on the html page
	f_workspace_names = workspace_names.text.encode("utf-8")
	li = eval(f_workspace_names)
	length_import =  len(li)
	print(li[1]['name'])
	if formw.validate_on_submit():
		return redirect(url_for('modelId'))

	return render_template('dashboard_w.html', form=formw, name=name, li=li, length_import=length_import)


@app.route('/modelId', methods = ['GET', 'POST'])
def modelId():
	formm = MForm()
	formw = WForm()
	name = global_user

	wid = formw.w_id.data

	credentials = global_user + ":" + global_password

	user = 'Basic ' + str(base64.b64encode(credentials).encode('utf-8').decode('utf-8'))

	getHeaders = {
    		'Authorization': user,
    		'Content-Type' : 'application/json'
	}

	model_names = requests.get('https://api.anaplan.com/1/3/workspaces/' + wid + '/models/', headers=getHeaders, data=json.dumps({'localeName': 'en_US'}))

	#showing on the html page
	f_model_names = model_names.text.encode('utf-8')
	li = eval(f_model_names)
	length_import =  len(li)

	if formm.validate_on_submit():
		return redirect(url_for('dashboard'))

	return render_template('dashboard_m.html', form=formm, name=name, li=li, length_import=length_import)


@app.route('/dashboard', methods = ['GET', 'POST'])
def dashboard():
	formd = DashForm()
	formw = WForm()
	formm = MForm()
	
	wid = formw.w_id.data
	mid = formm.m_id.data

	name = global_user

	credentials = global_user + ":" + global_password

	user = 'Basic ' + str(base64.b64encode(credentials).encode('utf-8').decode('utf-8'))

	getHeaders = {
    		'Authorization': user,
    		'Content-Type' : 'application/json'
	}	

	import_names = requests.get('https://api.anaplan.com/1/3/workspaces/' + wid + '/models/' + mid + '/imports/', headers=getHeaders, data=json.dumps({'localeName': 'en_US'}))

	
	f_import_names = import_names.text.encode('utf-8')
	print(f_import_names)
	li = eval(f_import_names)
	length_import = len(li) #length of Import Name
	
	if formd.validate_on_submit():
		return redirect(url_for('status'))

	return render_template('dashboard.html', form=formd, name=name, li=li, length_import=length_import)

@app.route('/status', methods = ['GET', 'POST'])
def status():
	formw = WForm()
	formm = MForm()
	formd = DashForm()

	wid = formw.w_id.data
	mid = formm.m_id.data

	nameid = formd.dash_id.data
	
	credentials = global_user + ":" + global_password

	user = 'Basic ' + str(base64.b64encode(credentials).encode('utf-8').decode('utf-8'))

	getHeaders = {
    		'Authorization': user,
    		'Content-Type' : 'application/json'
	}

	getProcesses = requests.post('https://api.anaplan.com/1/3/workspaces/' + wid + '/models/'+ mid +'/imports/' + nameid + '/tasks/', headers=getHeaders, data=json.dumps({'localeName': 'en_US'}))

	name_action = requests.get('https://api.anaplan.com/1/3/workspaces/' + wid + '/models/'+ mid +'/imports/' + nameid, headers=getHeaders, data=json.dumps({'localeName': 'en_US'}))

	f_action_name = name_action.text.encode('utf-8')

	ni = eval(f_action_name)

	send_name = ni["name"]

	if getProcesses.status_code == 200:
		status = "Status: Success"
		mail= smtplib.SMTP('smtp.gmail.com',587)
		mail.starttls()
		mail.login('testanaplanapi@gmail.com','Testing01')
		content = send_name+" The action was successful. The user who initiated is: "+global_user
		message = 'Subject: {}\n\n{}'.format(content, "PROCESS INITIATED")
		mail.sendmail('testanaplanapi@gmail.com',global_user,message)
		mail.close()
		return render_template('status.html', status=status, nameid=send_name)
	else:
		status = "Status: No Success"
		mail= smtplib.SMTP('smtp.gmail.com',587)
		mail.starttls()
		mail.login('testanaplanapi@gmail.com','Testing01')
		content = send_name+" The action was not successful. The user who initiated is: "+global_user
		message = 'Subject: {}\n\n{}'.format(content, "PROCESS INITIATED")
		mail.sendmail('testanaplanapi@gmail.com',global_user,message)
		mail.close()
		return render_template('status.html', status=status, nameid=send_name)


@app.route('/logout')
def logout():
	return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)