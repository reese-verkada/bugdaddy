#!/usr/bin/env python3

from flask import Flask, jsonify, request, Blueprint, redirect, url_for, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import flask_saml
import sqlite3 as sql
from config import *
from jira import Jira
from salesforce import Salesforce
from raw_p_formula import Raw_P_Formula
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
import json

jira = Jira(JIRA_USERNAME, JIRA_PASSWORD, JIRA_URL)
sf = Salesforce(SALESFORCE_INSTANCE, SALESFORCE_REFRESH_TOKEN, SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_REPORT_ID)

def serialize(result, **kwargs):
	if isinstance(result,list):
		d = []
		for obj in result:
			if isinstance(obj, tuple):
				tmp = {}
				for m in obj:
					if isinstance(m, db.Model):
						tmp.update(m.to_dict(**kwargs))
				d.append(tmp)
			elif isinstance(obj, db.Model):
				d.append(obj.to_dict(**kwargs))
		return d
	elif isinstance(result,db.Model):
		return [result.to_dict(**kwargs)]
	elif isinstance(result,tuple):
		d = {}
		for obj in result:
			if isinstance(obj, db.Model):
				d.update(obj.to_dict(**kwargs))
		return [d]
	else:
		return []

def error(msg):
	return jsonify({"success":False,"message":msg}),400
def isNumeric(string):
	try:
		float(string)
		return True
	except ValueError:
		return False


def calculateDisplayP():
	#Get the list of display_p options from display_p_formula
	options = serialize(DisplayPFormula.query.order_by(DisplayPFormula.low.desc()).all())
	if not options:
		return
	#For every row in jira_issues
	for issue in serialize(JiraIssue.query.all(), only=('issue_id', 'raw_p')):
		if issue['raw_p'] == None:
			display_p = None
		else:
			#calculate the display_p based on the raw_p
			display_p = options[-1]['display_p']
			for option in options:
				if issue['raw_p'] >= option['low']:
					display_p = option['display_p']
					break
		try:
			JiraIssue.query.get(issue['issue_id']).display_p = display_p
			db.session.commit()
		except:
			db.session.rollback()

def calculateRawP():
	#Get the formula from the db
	formulaString = serialize(RawPFormula.query.first(), only=('formula',))
	#if the formula exists, make the formula object
	formula = None
	if formulaString:
		formula = Raw_P_Formula(formulaString[0]['formula'])
	else:
		return
	#create a variable as a shortcut for the set of variables required
	variablesRequired = formula.operands
	#get the weighted_variables table so we know the weights
	variableWeights = serialize(WeightedVariable.query.all())
	variableWeights = {weight['variable_name']:weight['variable_weight'] for weight in variableWeights}
	#get only issues that have at least one weighted variable value
	issues = JiraIssue.query.join(JiraIssue.variable_values).all()
	#for each issue
	for issue in issues:
		try:
			#get the list of variable values from weighted_variable_values
			variableValues = issue.variable_values
			variableValues = {variable.variable_name:variable.value for variable in variableValues}
			variablesAvailable = set(variableValues)
			variablesAvailable.add("cases_attached")
			#if the set of variables available is not the set of variables required, skip to the next row
			if not variablesAvailable.issuperset(variablesRequired):
				print("Not enough variables available for issue", issue.issue_id)
				issue.raw_p = None
				db.session.commit()
			#otherwise, evaluate the raw p using the formula object and update jira_issues
			else:
				package = dict()
				if 'cases_attached' in variablesRequired:
					variableWeights['cases_attached'] = 1.0
					variableValues['cases_attached'] = SFIssue.query.get(issue.issue_id).cases_attached
				package = {v:variableWeights[v]*variableValues[v] for v in variablesRequired}
				
				raw_p = formula.evaluate(package)
				issue.raw_p = raw_p
				db.session.commit()
		except Exception as e:
			db.session.rollback()
			print("skipping cause ",e,type(e))
			continue
	calculateDisplayP()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
cors = CORS(app, supports_credentials=True)
app.config.update({
	'SECRET_KEY': SAML_SECRET_KEY,
	'SAML_METADATA_URL': SAML_METADATA_URL,
	'SAML_DEFAULT_REDIRECT': '/api/redirect?to='+FRONTEND_URL,
	'PERMANENT_SESSION_LIFETIME': timedelta(minutes=SESSION_TIMEOUT),
	'SQLALCHEMY_DATABASE_URI': DATABASE_URI,
	'SQLALCHEMY_TRACK_MODIFICATIONS': False,
	'SQLALCHEMY_ENGINE_OPTIONS': {'pool_size' : 100, 'pool_recycle' : 280}
})
flask_saml.FlaskSAML(app)
db = SQLAlchemy(app)
from model import *
db.create_all()

@app.before_request
def before_request():
	session.permanent = True
	#list of pages that require no auth
	public = [
	url_for("login"),
	url_for("logout"),
	url_for("login_acs"),
	url_for("metadata"),
	url_for("redirect_to")
	]

	adminOnly = [
	url_for("jira_get",apiEndpoint=""),
	url_for("jira_comments",issue_key=""),
	url_for("jira_redirect",issue_key=""),
	url_for("concierge"),
	url_for("custom_attributes"),
	url_for("jira_projects"),
	url_for("weighted_variables"),
	url_for("raw_p_formula"),
	url_for("display_p_formula")
	]
	#if the request isn't for a public path
	if request.path not in public and request.method != "OPTIONS":
		#list of roles user has
		role = session.get('saml',{}).get('attributes',{}).get('role',[])
		if request.method == 'GET':
			#if request is a GET and the user is not a bug_viewer nor is public access allowed
			if SAML_VIEWER_ROLE != None and SAML_VIEWER_ROLE not in role and SAML_ADMIN_ROLE not in role:
				#return unauthorized
				return jsonify({"success":False,"message":"unauthorized"}),401

			#Ok but even if you are a bug_viewer you still shouldn't be allowed to see adminOnly stuff
			if SAML_ADMIN_ROLE not in role and request.path.startswith(tuple(adminOnly)):
				return jsonify({"success":False,"message":"unauthorized"}),401
		else:
			#if request is a POST and the user is not a bug_admin
			if SAML_ADMIN_ROLE not in role:
				#return unauthorized
				return jsonify({"success":False,"message":"unauthorized"}),401

@app.route('/api/check_auth')
def check_auth():
	subject = session.get('saml',{}).get('subject',False)
	d = {}
	d['isLoggedIn'] = True if subject else False
	d['session'] = session.get('saml')
	return jsonify(d)

@app.route('/api/debug',methods=["GET","POST"])
def debug():
	print(session.__repr__())
	return jsonify(session.get('saml'))

@app.route('/api/redirect')
def redirect_to():
	to = request.args.get('to') if request.args.get('to') else "/"
	if FRONTEND_URL in to:
		return redirect(to)
	else:
		return error("Cannot redirect to any other place besides the frontend")

@app.route('/api/')
def index():
	d = {'success':True}
	return jsonify(d)

@app.route('/api/jira_redirect/<issue_key>')
def jira_redirect(issue_key):
	try:
		return redirect(JIRA_URL+"/browse/"+issue_key)
	except Exception as e:
		return error(str(e))

@app.route('/api/jira_get/<path:apiEndpoint>')
def jira_get(apiEndpoint):
	try:
		return jsonify(jira.get(apiEndpoint+"?"+request.query_string.decode()))
	except Exception as e:
		return error(str(e))

@app.route('/api/jira_post/<path:endpoint>',methods=['POST'])
def jira_post(endpoint):
	try:
		return jsonify(jira.post(endpoint,request.json))
	except Exception as e:
		return error(str(e))

@app.route('/api/jira_put/<path:endpoint>',methods=['PUT'])
def jira_put(endpoint):
	try:
		return jsonify(jira.put(endpoint,request.json))
	except Exception as e:
		raise e
		return error(str(e))

@app.route('/api/jira_comments/<issue_key>',methods=['GET'])
def jira_comments(issue_key):
	return jsonify(jira.comments(issue_key))

@app.route('/api/weighted_variables', methods=['GET','POST','DELETE'])
def weighted_variables():
	d = {'errors':[]}
	if request.method == 'POST':
		try:
			body = request.json
			for variable in body:
				try:
					if variable['variable_name'] and variable['variable_weight']:
						if isNumeric(variable['variable_weight']):
							if not isNumeric(variable['variable_name']):
								new_var = WeightedVariable(variable_name=variable['variable_name'], variable_weight=variable['variable_weight'])
								db.session.add(new_var)
								db.session.commit()
							else:
								d['errors'].append("Variable name cannot be a number")
						else:
							d['errors'].append("Variable weight must be a number")
					else:
						d['errors'].append("Fields are missing")
				except:
					db.session.rollback()
					WeightedVariable.query.get(variable['variable_name']).variable_weight = variable['variable_weight']
					db.session.commit()
			calculateRawP()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("Variable already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			d['errors'].append("An unknown error occurred")

	if request.method == 'DELETE':
		try:
			body = request.json
			currentFormula = RawPFormula.query.first()
			try:
				currentFormula = Raw_P_Formula(currentFormula.formula).operands
			except:
				currentFormula = None
			for variable in body:
				if not currentFormula or variable['variable_name'] not in currentFormula:
					db.session.delete(WeightedVariable.query.get(variable['variable_name']))
					db.session.commit()
				else:
					d['errors'].append("Cannot delete weighted variable "+str(variable['variable_name'])+" as it is currently in use in the formula")
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("Variable already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("Variable already exists")
		except Exception as e:
			print(type(e).__name__,e)
			d['errors'].append("Variable already exists")

	#GET
	q = WeightedVariable.query.all()
	d['weighted_variables'] = serialize(q)
	return jsonify(d)

@app.route('/api/jira_projects', methods=['GET','POST','DELETE'])
def jira_projects():
	if request.method == 'POST':
		try:
			body = request.json
			desiredProject = str(body['project_id'])
			projectsOnJira = {str(project['id']):project['name'] for project in jira.project()}

			if desiredProject in projectsOnJira:
				print("Inserting")
				db.session.add(JiraProject(project_id=int(desiredProject), project_name=projectsOnJira[desiredProject]))
				db.session.commit()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An unknown error occurred")

	if request.method == 'DELETE':
		try:
			body = request.json
			project_id = body['project_id']
			#subquery -- get all JIRAIssue issue_id's for the project we're going to delete
			sq = db.session.query(JiraIssue.issue_id).filter_by(project_id=project_id).subquery()
			#now query for all SFIssue objects that are in the subquery
			db.session.query(SFIssue).filter(SFIssue.issue_id.in_(sq)).delete(synchronize_session='fetch')
			db.session.delete(JiraProject.query.get(project_id))
			db.session.commit()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			return error("IntegrityError")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		

	#GET
	q = JiraProject.query.all()
	d = serialize(q)
	return jsonify(d)

@app.route('/api/jira_issues', methods=['GET','POST','DELETE'])
def jira_issues():
	if request.method == 'POST':
		try:
			body = request.json
			issues = [issue['issue_key'] for issue in body]
			jiraIssues = jira.issues(issues,"summary,status,project")

			if jiraIssues.get("total") == 0:
				return error("Issue Key not found")

			for issue in jiraIssues['issues']:
				package = {
					'issue_id': issue['id'],
					'issue_key': issue['key'],
					'summary': issue['fields']['summary'],
					'status': issue['fields']['status']['name']
				}
				db.session.add(JiraIssue(**package))
				db.session.commit()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An unknown error occurred")

	if request.method == 'DELETE':
		try:
			body = request.json

			for issue in body:
				JiraIssue.query.filter_by(issue_id=issue['issue_id']).delete()
				SFIssue.query.filter_by(issue_id=issue['issue_id']).delete()
			db.session.commit()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An unknown error occurred")

	#GET
	#d = query("SELECT *,project_name,color FROM jira_issues NATURAL LEFT JOIN sf_issues LEFT JOIN jira_projects ON jira_issues.project_id = jira_projects.project_id LEFT JOIN display_p_formula ON display_p_formula.display_p = jira_issues.priority")
	q = db.session.query(JiraIssue, SFIssue, DisplayPFormula).outerjoin(SFIssue, SFIssue.issue_id == JiraIssue.issue_id).outerjoin(DisplayPFormula, DisplayPFormula.display_p == JiraIssue.priority).all()
	d = serialize(q)
	return jsonify(d)

@app.route('/api/raw_p_formula', methods=['GET','POST'])
def raw_p_formula():
	"""
	Please note: The RawPFormula class is the db.Model class (in model.py); the Raw_P_Formula class is for validating and running calculations with the raw p formula (in raw_p_formula.py)
	"""
	if request.method == 'POST':
		try:
			body = request.json
			formula = Raw_P_Formula(body['formula'])

			weighted_variables = db.session.query(WeightedVariable.variable_name).all()
			weighted_variables = {var[0] for var in weighted_variables}
			weighted_variables.add("cases_attached")

			print(formula.operands)
			print(weighted_variables)
			for var in formula.operands:
				if var not in weighted_variables:
					raise Exception("Supplied operand(s) not a weighted variable or cases_attached")
				

			RawPFormula.query.delete()
			db.session.add(RawPFormula(formula=formula.stringFormula()))
			db.session.commit()
			calculateRawP()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error(str(e))

	#GET
	q = db.session.query(RawPFormula).first()
	d = serialize(q)
	return jsonify(d)

@app.route('/api/display_p_formula', methods=['GET','POST'])
def display_p_formula():
	if request.method == 'POST':
		try:
			body = request.json
			DisplayPFormula.query.delete()
			for rule in body:
				display_p = rule['display_p']
				low = rule['low']
				color = rule['color']
				emoji = rule.get('emoji')

				db.session.add(DisplayPFormula(display_p=display_p, low=low, color=color, emoji=emoji))
			
			db.session.commit()
			calculateDisplayP()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An error occurred")

	#GET
	q = DisplayPFormula.query.order_by(DisplayPFormula.low.desc()).all()
	d = serialize(q)
	return jsonify(d)

@app.route('/api/weighted_variable_values', methods=['GET','POST','DELETE'])
def weighted_variable_values():
	d = {'errors':[]}
	if request.method == 'POST':
		try:
			body = request.json
			for weighted_variable_value in body:
				try:
					issue_id = weighted_variable_value['issue_id']
					variable_name = weighted_variable_value['variable_name']
					value = weighted_variable_value['value']

					if not issue_id:
						d['errors'].append("Issue ID is missing")
						continue

					if not variable_name:
						d['errors'].append("Variable name is missing")
						continue

					if not isNumeric(value):
						d['errors'].append("Value must be numeric")
						continue

					db.session.add(WeightedVariableValue(issue_id=issue_id, variable_name=variable_name, value=value))
					db.session.commit()
				except exc.IntegrityError:
					db.session.rollback()
					WeightedVariableValue.query.filter_by(issue_id=issue_id).filter_by(variable_name=variable_name).one().value = value
					db.session.commit()
			calculateRawP()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			return error("Variable already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An unknown error occurred")

	if request.method == 'DELETE':
		try:
			pass
		except exc.IntegrityError as e:
			print(type(e).__name__,e)
			return error("Variable already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An unknown error occurred")

	#GET
	if request.args.get('issue_id'):
		d['weighted_variable_values'] =serialize(WeightedVariableValue.query.filter_by(issue_id=request.args.get('issue_id')).all())
	else:
		d['weighted_variable_values'] = serialize(WeightedVariableValue.query.all())
	return jsonify(d)

@app.route('/api/sync')
def sync():
	d = {'errors':[],'suggested_for_deletion':[]}

	try:
		#first update data from salesforce
		sf_issues = sf.get_issues()
		for issue_id,sf_issue in sf_issues.items():
			try:
				#try to insert it into the db
				package = {
					'issue_id': issue_id,
					'total_spend': sf_issue.get('total_spend'),
					'cases_attached': sf_issue.get('cases_attached'),
					'created_by': sf_issue.get('created_by')
				}
				db.session.add(SFIssue(**package))
				db.session.commit()
			except:
				#update the record if it exists already
				db.session.rollback()
				current = SFIssue.query.filter_by(issue_id=issue_id).update(package)
				db.session.commit()
	except Exception as e:
		db.session.rollback()
		d['errors'].append("Could not fetch data from Salesforce")
		print(e)

	#update jira_projects table
	try:
		projects = jira.project()
		for project in projects:
			try:
				#try to insert project into db
				db.session.add(JiraProject(project_id=project.get('id'), project_name=project.get('name')))
				db.session.commit()
			except:
				#update the project if it exists
				db.session.rollback()
				JiraProject.query.get(project.get('id')).project_name = project.get('name')
				db.session.commit()
	except:
		db.session.rollback()
		d['errors'].append("Could not fetch projects from JIRA")

	#get the list of all issue_ids, whether they be from jira or sf
	try:
		trackedIssues = db.session.query(JiraIssue.issue_id).union(db.session.query(SFIssue.issue_id)).all()
		trackedIssues = [issue_id[0] for issue_id in trackedIssues]
	except Exception as e:
		return error("Could not fetch issues from database")

	#get all the info from jira on these trackedIssues
	try:
		issues = jira.issues(trackedIssues,"status,project,summary,priority,updated,created,assignee,reporter",100,0)
		startAt = 100
		while startAt < issues.get('total'):
			moreData = jira.issues(trackedIssues,"status,project,summary,priority,updated,created,assignee,reporter",100,startAt)
			if moreData.get('issues'):
				issues['issues'].extend(moreData['issues'])
			startAt += 100
	except Exception as e:
		return error("Could not fetch issues from JIRA")

	#for each issue
	try:
		for issue in issues.get('issues'):
		#if we are tracking the issue, update it
			try:
				issue_id = int(issue['id'])
				issue_key = issue['key']
				status = issue['fields']['status']['name']
				project_id = int(issue['fields']['project']['id'])
				summary = issue['fields']['summary']
				priority = issue['fields'].get('priority',{}).get('name',None)
				updated = issue['fields'].get('updated')
				created = issue['fields'].get('created')
				assignee = issue['fields']['assignee'].get('displayName') if issue['fields']['assignee'] else "Unassigned"
				reporter = issue['fields']['reporter'].get('displayName') if issue['fields']['reporter'] else "Unknown"
				newInfo = {
					'issue_id':issue_id,
					'issue_key':issue_key,
					'status':status,
					'project_id':project_id,
					'summary':summary,
					'priority':priority,
					'updated':jira.parse_time(updated),
					'created':jira.parse_time(created),
					'assignee':assignee,
					'reporter':reporter
				}
				columns = set(newInfo)
				columns.remove('created')
				columns.remove('updated')
				columns = tuple(columns)
				issueAlreadyTracked = JiraIssue.query.get(issue_id)

				if issueAlreadyTracked:
					#if every column for this issue in the db matches what we got from jira...
					if all(getattr(issueAlreadyTracked, k) == v for k,v in newInfo.items()):
						#nothing to update
						pass
					else:
						print("Updating db with:")
						print(newInfo)
						old = json.dumps(serialize(issueAlreadyTracked,only=columns)[0])
						JiraIssue.query.filter_by(issue_id=issue_id).update(newInfo)
						new = json.dumps(serialize(issueAlreadyTracked,only=columns)[0])
						if old != new:
							db.session.add(Change(issue_id=issue_id, old=old, new=new))
						db.session.commit()
				else:
					#if we aren't tracking that issue, insert it into the db
					print("Inserting into db with:")
					print(newInfo)
					db.session.add(JiraIssue(**newInfo))
					newIssue = JiraIssue.query.get(issue_id)
					new = json.dumps(serialize(newIssue,only=columns)[0])
					db.session.add(Change(issue_id=issue_id, new=new))
					db.session.commit()
			except Exception as e:
				db.session.rollback()
				d['errors'].append("Skipping issue due to exception because "+str(e))
				continue
	except Exception as e:
		raise e
		return error("Could not loop through issues because "+str(e))
	return jsonify(d)

@app.route('/api/concierge')
def concierge():
	d = {}
	
	#this route will return a list of recent issue changes
	#if the user exists within users table, then only return changes with id > change_seen
	#otherwise, return the top X most recent changes
	"""
	output schema:
	[
		{issue_key:"CS-925", summary:"vsubmit blah blah", changes:[
			{
				field:"Priority",
				old:"P2",
				new:"P1"
			}
		]}
	]
	"""

	#this method takes in 2 dicts and returns a list of differences between them; see output schema for schema
	def __diff(old, new):
		if old is None:
			old = '{}'
		if new is None:
			new = '{}'

		old = json.loads(old)
		new = json.loads(new)

		oldSet = set(old)
		newSet = set(new)
		superset = oldSet if oldSet >= newSet else newSet

		output = []
		for field in superset:
			if (old.get(field) != new.get(field)):
				output.append(
					{'field': field, 'old':old.get(field), 'new':new.get(field)}
				)
		return output

	email = session.get('saml',{}).get('subject')
	user = None
	if email:
		user = User.query.get(email)

	if user:
		changes = Change.query.filter(Change.change_id > user.seen_change).order_by(Change.change_id.desc()).limit(100).all()
	else:
		changes = Change.query.order_by(Change.change_id.desc()).limit(100).all()

	d = []
	for change in changes:
		output = {
			'change_id': change.change_id,
			'issue_key': change.issue.issue_key,
			'summary': change.issue.summary,
			'changes': __diff(change.old, change.new)
		}
		if output['changes']:
			d.append(output)

	return jsonify(d)

@app.route('/api/seen_change',methods=['POST'])
def seen_change():
	d = {'errors':[]}
	if request.method == 'POST':
		print(session.get('subject'))
		if session.get('saml',{}).get('subject'):
			try:
				body = request.json
				#body should be of the form {"seen_change":10}
				email = session.get('saml',{}).get('subject')
				change_id = int(body['seen_change'])
				try:
					db.session.add(User(email=email, seen_change=change_id))
					db.session.commit()
				except:
					db.session.rollback()
					User.query.get(email).seen_change = change_id
					db.session.commit()
				finally:
					d['success'] = True
			except exc.IntegrityError as e:
				db.session.rollback()
				print(type(e).__name__,e)
				d['errors'].append("Attribute already exists")
			except KeyError as e:
				print(type(e).__name__,e)
				d['errors'].append("One or more fields are missing")
			except Exception as e:
				print(type(e).__name__,e)
				d['errors'].append("An unknown error occurred")
	return jsonify(d)


@app.route('/api/custom_attributes', methods=['GET','POST'])
def custom_attributes():
	d = {'errors':[]}
	if request.method == 'POST':
		try:
			body = request.json
			#body should be a dict of lists w/ format {attr_name:[list, of, attr_options],...}
			for attr_name in body:
				for option in body.get(attr_name):
					if option:
						try:
							db.session.add(CustomAttribute(attr_name=attr_name, attr_option=option))
							db.session.commit()
						except Exception as e:
							print(str(e))
							db.session.rollback()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("Attribute already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			d['errors'].append("An unknown error occurred")

	#GET
	d["attributes"] = {}
	for attr in serialize(CustomAttribute.query.all()):
		if (d['attributes'].get(attr['attr_name'])): #if the object alrady exists in the response
			d["attributes"][attr['attr_name']].append(attr.get('attr_option'))
		else:
			d["attributes"][attr['attr_name']] = [attr.get('attr_option')]

	return jsonify(d)

@app.route('/api/custom_attributes/<attr_name>', methods=['POST','DELETE'])
def custom_attributes_attr_name(attr_name):
	d = {'errors':[]}
	if request.method == 'POST':
		#Update the attribute name
		try:
			#body should look like {"attr_name":"Some New Name"}
			body = request.json

			new_attr_name = body['attr_name']
			CustomAttribute.query.filter_by(attr_name=attr_name).update({CustomAttribute.attr_name:new_attr_name})
			db.session.commit()
			d['success'] = True
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("Attribute already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			d['errors'].append("An unknown error occurred")

	if request.method == 'DELETE':
		#Delete the attribute
		try:
			CustomAttribute.query.filter_by(attr_name=attr_name).delete()
			db.session.commit()
			d['success'] = True
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("Attribute already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("One or more fields are missing")
		except Exception as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("An unknown error occurred")

	return jsonify(d)

@app.route('/api/custom_attributes/<attr_name>/<attr_option>', methods=['POST','DELETE'])
def custom_attributes_attr_name_attr_option(attr_name, attr_option):
	d = {'errors':[]}
	if request.method == 'POST':
		#Update the attribute option
		try:
			#body should look like {"attr_option":"Some New Name"}
			body = request.json

			new_attr_option = body['attr_option']
			CustomAttribute.query.filter_by(attr_name=attr_name, attr_option=attr_option).update({CustomAttribute.attr_option:new_attr_option})
			db.session.commit()
			d['success'] = True
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("Attribute already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			d['errors'].append("An unknown error occurred")

	if request.method == 'DELETE':
		#Delete the attribute option
		try:
			CustomAttribute.query.filter_by(attr_name=attr_name, attr_option=attr_option).delete()
			db.session.commit()
			d['success'] = True
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("Attribute already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("One or more fields are missing")
		except Exception as e:
			db.session.rollback()
			print(type(e).__name__,e)
			d['errors'].append("An unknown error occurred")

	if len(d['errors']):
		return jsonify(d),400
	return jsonify(d)

@app.route('/api/issue_attributes', methods=['GET','POST'])
def issue_attributes():
	d = {}

	if request.method == 'POST':
		try:
			body = request.json
			issue_id = body['issue_id']
			attr_name = body['attr_name']
			attr_option = body['attr_option']

			issue = JiraIssue.query.get(issue_id)
			attr = CustomAttribute.query.with_parent(issue).filter_by(attr_name=attr_name).first()
			new_attr = CustomAttribute.query.get((attr_name,attr_option))
			try:
				issue.attributes.remove(attr)
			except:
				pass
			issue.attributes.append(new_attr)
			db.session.commit()
		except exc.IntegrityError as e:
			db.session.rollback()
			print(type(e).__name__,e)
		except KeyError as e:
			print(type(e).__name__,e)
		except Exception as e:
			print(type(e).__name__,e)

	#GET

	records = JiraIssue.query.join(JiraIssue.attributes)
	for record in records:
		if not d.get(record.issue_id):
			d[record.issue_id] = {}
		for attribute in record.attributes:
			d[record.issue_id][attribute.attr_name] = attribute.attr_option
	return jsonify(d)

if __name__ == '__main__':
	app.run()




