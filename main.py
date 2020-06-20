#!/usr/bin/env python3

from flask import Flask, jsonify, request, Blueprint, redirect, url_for, session
from flask_cors import CORS
import flask_saml
import sqlite3 as sql
from config import *
from jira import Jira
from salesforce import Salesforce
from raw_p_formula import Raw_P_Formula
import init

init.run()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
conn = sql.connect('db/bugdaddy.db',check_same_thread=False)
conn.execute('pragma foreign_keys=ON')
conn.row_factory = dict_factory
jira = Jira(JIRA_USERNAME, JIRA_PASSWORD, JIRA_URL)
sf = Salesforce(SALESFORCE_INSTANCE, SALESFORCE_REFRESH_TOKEN, SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_REPORT_ID)
def query(q,p=()):
	cur = conn.cursor()
	cur.execute(q,p)
	result = cur.fetchall()
	return result
def push(q,p=()):
	cur = conn.cursor()
	cur.execute(q,p)
	conn.commit()
	return cur.fetchall()
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
	options = query("SELECT * FROM display_p_formula ORDER BY low DESC")
	if not options:
		return
	#For every row in jira_issues
	for issue in query("SELECT issue_id, raw_p FROM jira_issues"):
		if issue['raw_p'] == None:
			display_p = None
		else:
			#calculate the display_p based on the raw_p
			display_p = options[-1]['display_p']
			for option in options:
				if issue['raw_p'] >= option['low']:
					display_p = option['display_p']
					break
		push("UPDATE jira_issues SET display_p=? WHERE issue_id=?",(display_p,issue['issue_id']))

def calculateRawP():
	#Get the formula from the db
	formulaString = query("SELECT formula FROM raw_p_formula LIMIT 1")
	#if the formula exists, make the formula object
	formula = None
	if formulaString:
		formula = Raw_P_Formula(formulaString[0]['formula'])
	else:
		return
	#create a variable as a shortcut for the set of variables required
	variablesRequired = formula.operands
	#get the weighted_variables table so we know the weights
	variableWeights = query("SELECT * FROM weighted_variables")
	variableWeights = {weight['variable_name']:weight['variable_weight'] for weight in variableWeights}
	#get the required rows
	issues = query("SELECT issue_id, cases_attached FROM jira_issues NATURAL JOIN sf_issues")
	#for each row
	for issue in issues:
		try:
			#get the list of variable values from weighted_variable_values
			variableValues = query("SELECT issue_id, variable_name, value FROM weighted_variable_values WHERE issue_id=?",(issue['issue_id'],))
			if variableValues:
				variableValues = {variable['variable_name']:variable['value'] for variable in variableValues}
			else:
				variableValues = {}
			variablesAvailable = set(variableValues)
			variablesAvailable.add("cases_attached")
			#if the set of variables available is not the set of variables required, skip to the next row
			print("variables required: ",variablesRequired)
			print("variables available: ",variablesAvailable)
			if not variablesAvailable.issuperset(variablesRequired):
				push("UPDATE jira_issues SET raw_p=NULL WHERE issue_id=?",(issue['issue_id'],))
			#otherwise, evaluate the raw p using the formula object and update jira_issues
			else:
				package = dict()
				if 'cases_attached' in variablesRequired:
					variableWeights['cases_attached'] = 1.0
					variableValues['cases_attached'] = issue['cases_attached']
				package = {v:variableWeights[v]*variableValues[v] for v in variablesRequired}
				
				raw_p = formula.evaluate(package)
				push("UPDATE jira_issues SET raw_p=? WHERE issue_id=?",(raw_p,issue['issue_id']))
		except Exception as e:
			print("skipping cause ",e,type(e))
			continue
	calculateDisplayP()

app = Flask(__name__)
cors = CORS(app, supports_credentials=True)
app.config.update({
	'SECRET_KEY': SAML_SECRET_KEY,
	'SAML_METADATA_URL': SAML_METADATA_URL,
	'SAML_DEFAULT_REDIRECT': '/api/redirect?to='+FRONTEND_URL,
	'SERVER_NAME': BACKEND_URL
})
flask_saml.FlaskSAML(app)

@app.before_request
def before_request():
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
								push("INSERT INTO weighted_variables (variable_name,variable_weight) VALUES (?,?)",(variable['variable_name'],variable['variable_weight']))
							else:
								d['errors'].append("Variable name cannot be a number")
						else:
							d['errors'].append("Variable weight must be a number")
					else:
						d['errors'].append("Fields are missing")
				except sql.IntegrityError:
					push("UPDATE weighted_variables SET variable_weight=? WHERE variable_name=?",(variable['variable_weight'],variable['variable_name']))
			calculateRawP()
		except sql.IntegrityError as e:
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
			currentFormula = query("SELECT * FROM raw_p_formula LIMIT 1")
			try:
				currentFormula = Raw_P_Formula(currentFormula[0]['formula']).operands
			except:
				currentFormula = None
			for variable in body:
				if not currentFormula or variable['variable_name'] not in currentFormula:
					push("DELETE FROM weighted_variables WHERE variable_name = ?",(variable['variable_name'],))
				else:
					d['errors'].append("Cannot delete weighted variable "+str(variable['variable_name'])+" as it is currently in use in the formula")
		except sql.IntegrityError as e:
			print(type(e).__name__,e)
			d['errors'].append("Variable already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("Variable already exists")
		except Exception as e:
			print(type(e).__name__,e)
			d['errors'].append("Variable already exists")

	#GET
	d['weighted_variables'] = query("SELECT * FROM weighted_variables")
	return jsonify(d)

@app.route('/api/jira_url', methods=['GET','POST'])
def jira_url():
	if request.method == 'POST':
		try:
			body = request.json
			push("DELETE FROM jira_url WHERE 1")
			push("INSERT INTO jira_url (jira_url) VALUES (?)",(body['jira_url'],))
		except sql.IntegrityError as e:
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An unknown error occurred")

	#GET
	d = query("SELECT * FROM jira_url")
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
				push("INSERT INTO jira_projects (project_id,project_name) VALUES (?,?)",(int(desiredProject),projectsOnJira[desiredProject]))
		except sql.IntegrityError as e:
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
			push("DELETE FROM sf_issues WHERE issue_id IN (SELECT issue_id FROM jira_issues WHERE project_id = ?)",(project_id,))
			push("DELETE FROM jira_projects WHERE project_id = ?",(project_id,))
		except sql.IntegrityError as e:
			print(type(e).__name__,e)
			return error("IntegrityError")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An unknown error occurred")

	#GET
	d = query("SELECT * FROM jira_projects")
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
				package = (
					issue['id'],
					issue['key'],
					None,
					issue['fields']['summary'],
					issue['fields']['status']['name']
				)
				push("INSERT INTO jira_issues (issue_id, issue_key, project_id, summary, status) VALUES (?,?,?,?,?)",package)
		except sql.IntegrityError as e:
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
				push("DELETE FROM jira_issues WHERE issue_id = ?",(issue['issue_id'],))
				push("DELETE FROM sf_issues WHERE issue_id = ?",(issue['issue_id'],))
		except sql.IntegrityError as e:
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error("An unknown error occurred")

	#GET
	d = query("SELECT *,project_name,color FROM jira_issues NATURAL LEFT JOIN sf_issues LEFT JOIN jira_projects ON jira_issues.project_id = jira_projects.project_id LEFT JOIN display_p_formula ON display_p_formula.display_p = jira_issues.priority")
	return jsonify(d)

@app.route('/api/raw_p_formula', methods=['GET','POST'])
def raw_p_formula():
	if request.method == 'POST':
		try:
			body = request.json
			formula = Raw_P_Formula(body['formula'])

			weighted_variables = query("SELECT variable_name FROM weighted_variables")
			weighted_variables = {var['variable_name'] for var in weighted_variables}
			weighted_variables.add("cases_attached")

			print(formula.operands)
			print(weighted_variables)
			for var in formula.operands:
				if var not in weighted_variables:
					raise Exception("Supplied operand(s) not a weighted variable or cases_attached")
				

			push("DELETE FROM raw_p_formula WHERE 1")
			push("INSERT INTO raw_p_formula (formula) VALUES (?)",(formula.stringFormula(),))
			calculateRawP()
		except sql.IntegrityError as e:
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error(str(e))

	#GET
	d = query("SELECT * FROM raw_p_formula")
	return jsonify(d)

@app.route('/api/display_p_formula', methods=['GET','POST'])
def display_p_formula():
	if request.method == 'POST':
		try:
			body = request.json
			push("DELETE FROM display_p_formula WHERE 1")
			for rule in body:
				display_p = rule['display_p']
				low = rule['low']
				color = rule['color']
				emoji = rule.get('emoji')

				push("INSERT INTO display_p_formula (display_p,low, color, emoji) VALUES (?,?,?,?)",(display_p,low,color,emoji))
			
			calculateDisplayP()
		except sql.IntegrityError as e:
			print(type(e).__name__,e)
			return error("Value already exists")
		except KeyError as e:
			print(type(e).__name__,e)
			return error("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			return error(str(e))

	#GET
	d = query("SELECT * FROM display_p_formula ORDER BY low DESC")
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

					push("INSERT INTO weighted_variable_values (issue_id,variable_name,value) VALUES (?,?,?)",(issue_id,variable_name,value))
				except sql.IntegrityError:
					push("UPDATE weighted_variable_values SET value = ? WHERE issue_id = ? and variable_name = ?",(value,issue_id,variable_name))
			calculateRawP()
		except sql.IntegrityError as e:
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
		except sql.IntegrityError as e:
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
		d['weighted_variable_values'] = query("SELECT * FROM weighted_variable_values WHERE issue_id = ?",(request.args.get('issue_id'),))
	else:
		d['weighted_variable_values'] = query("SELECT * FROM weighted_variable_values")
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
				push("INSERT INTO sf_issues (issue_id, total_spend, cases_attached, created_by) VALUES (?,?,?,?)",(
					issue_id,
					sf_issue.get('total_spend'),
					sf_issue.get('cases_attached'),
					sf_issue.get('created_by')
				))
			except sql.DatabaseError:
				#update the record if it exists already
				push("UPDATE sf_issues SET total_spend=?, cases_attached=?, created_by=? WHERE issue_id=?",(
					sf_issue.get('total_spend'),
					sf_issue.get('cases_attached'),
					sf_issue.get('created_by'),
					issue_id
				))
	except Exception as e:
		d['errors'].append("Could not fetch data from Salesforce")
		print(e)

	#update jira_projects table
	try:
		projects = jira.project()
		for project in projects:
			try:
				#try to insert project into db
				push("INSERT INTO jira_projects (project_id, project_name) VALUES (?,?)",(project.get('id'),project.get('name')))
			except sql.DatabaseError:
				#update the project if it exists
				push("UPDATE jira_projects SET project_name=? WHERE project_id=?",(project.get('name'),project.get('id')))
	except:
		d['errors'].append("Could not fetch projects from JIRA")

	#get the list of all issue_ids, whether they be from jira or sf
	try:
		trackedIssues = query("SELECT issue_id FROM sf_issues UNION SELECT issue_id FROM jira_issues")
		trackedIssues = [issue_id.get('issue_id') for issue_id in trackedIssues]
	except Exception as e:
		return error("Could not fetch issues from database")

	#get all the info from jira on these trackedIssues
	try:
		issues = jira.issues(trackedIssues,"status,project,summary,priority",100,0)
		startAt = 100
		while startAt < issues.get('total'):
			moreData = jira.issues(trackedIssues,"status,project,summary,priority",100,startAt)
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
				newInfo = {
					'issue_id':issue_id,
					'issue_key':issue_key,
					'status':status,
					'project_id':project_id,
					'summary':summary,
					'priority':priority,
				}
				issueAlreadyTracked = query("SELECT issue_id,issue_key,status,project_id,summary,priority FROM jira_issues WHERE issue_id = ? LIMIT 1",(issue_id,))

				if issueAlreadyTracked:
					if issueAlreadyTracked[0] == newInfo:
						#nothing to update
						pass
					else:
						print("Updating db with:")
						print(newInfo)
						push("UPDATE jira_issues SET issue_key=?, status=?, project_id=?, summary=?, delete_ignore=0, priority=? WHERE issue_id = ?",(issue_key,status,project_id,summary,priority,issue_id))
				else:
					#if we aren't tracking that issue, insert it into the db
					print("Inserting into db with:")
					print(newInfo)
					push("INSERT INTO jira_issues (issue_key,status,issue_id,project_id,summary,priority) VALUES (?,?,?,?,?,?)",(issue_key,status,issue_id,project_id,summary,priority))
			except Exception as e:
				d['errors'].append("Skipping issue due to exception because "+str(e))
				continue
	except Exception as e:
		return error("Could not loop through issues because "+str(e))
	"""
	touchedIssues = set()
	d = {'errors':[],'suggested_for_deletion':[]}
	suggested_for_deletion = None

	#for each project we track
	try:
		trackedProjects = query("SELECT project_id FROM jira_projects")
	except:
		return error("Could not fetch tracked projects from database")

	for trackedProject in trackedProjects:
		#reach out to jira and get a list of all issues for that project
		try:
			issues = jira.search("project="+str(trackedProject['project_id'])+" and resolution={} order by id desc".format(JIRA_TRACK_RESOLUTION),"status,project,summary",100)
			startAt = 100
			while startAt < issues.get('total'):
				moreData = jira.search("project="+str(trackedProject['project_id'])+" and resolution={} order by id desc".format(JIRA_TRACK_RESOLUTION),"status,project,summary",100,startAt)
				if moreData.get('issues'):
					issues['issues'].extend(moreData['issues'])
				startAt += 100
		except:
			return error("Could not fetch issues from JIRA")
		#update the project name in the db
		try:
			projectName = jira.project(trackedProject['project_id'])['name']
			push("UPDATE jira_projects SET project_name = ? WHERE project_id = ?",(projectName,trackedProject['project_id']))
		except:
			d['errors'].append("Could not update project name. Oh well!")
		#for each issue
		try:
			for issue in issues['issues']:
			#if we are tracking the issue, update it
				try:
					issue_id = int(issue['id'])
					issue_key = issue['key']
					status = issue['fields']['status']['name']
					project_id = int(issue['fields']['project']['id'])
					summary = issue['fields']['summary']
					newInfo = {
						'issue_id':issue_id,
						'issue_key':issue_key,
						'status':status,
						'project_id':project_id,
						'summary':summary
					}
					touchedIssues.add(issue_id)
					issueAlreadyTracked = query("SELECT issue_id,issue_key,status,project_id,summary FROM jira_issues WHERE issue_id = ? LIMIT 1",(issue_id,))

					if issueAlreadyTracked:
						if issueAlreadyTracked[0] == newInfo:
							#nothing to update
							pass
						else:
							print("Updating db with:")
							print(newInfo)
							push("UPDATE jira_issues SET issue_key=?, status=?, project_id=?, summary=?, delete_ignore=0 WHERE issue_id = ?",(issue_key,status,project_id,summary,issue_id))
					else:
						#if we aren't tracking that issue, insert it into the db
						print("Inserting into db with:")
						print(newInfo)
						push("INSERT INTO jira_issues (issue_key,status,issue_id,project_id,summary) VALUES (?,?,?,?,?)",(issue_key,status,issue_id,project_id,summary))
				except Exception as e:
					d['errors'].append("Skipping issue due to exception because "+str(e))
					continue
		except Exception as e:
			return error("Could not loop through issues because "+str(e))

	#query the db for a set of all project ids
	try:
		query_result = query("SELECT issue_id, issue_key, status, summary, display_p FROM jira_issues WHERE delete_ignore = 0")
		suggestedIssues = []
		for issue in query_result:
			try:
				if issue['issue_id'] not in touchedIssues: 
					suggestedIssues.append(issue['issue_id'])
			except Exception as e:
				d['errors'].append("Skipping the issue deletion suggestion check for issue because "+str(e))
		d['suggested_for_deletion'] = jira.issues(suggestedIssues,"status,project,summary")
		if d['suggested_for_deletion']:
			suggested_for_deletion = d['suggested_for_deletion']['issues']
	except Exception as e:
		d['errors'].append("Could not do the issue deletion suggestion check because "+str(e))
		print(e)

	if suggested_for_deletion:
		print("Updating info on issues that are now resolved")
		for issue in suggested_for_deletion:
			try:
				issue_key = issue['key']
				status = issue['fields']['status']['name']
				project_id = int(issue['fields']['project']['id'])
				summary = issue['fields']['summary']
				issue_id = int(issue['id'])
				push("UPDATE jira_issues SET issue_key=?, status=?, summary=? WHERE issue_id = ?",(issue_key,status,summary,issue_id))
			#TODO: except sql.IntegrityError (occurs when an issue has been moved to a project that's not in jira_projects table)
			except Exception as e:
				d['errors'].append("Skipping updating the db because of "+str(e))"""
	return jsonify(d)

@app.route('/api/concierge')
def concierge():
	d = {}
	#Track a project [show if no projects tracked]
	try:
		task = {}
		task['title'] = 'Track a project'
		task['description'] = "Tracking a JIRA project will import and continually sync the project's issues."
		task['data'] = len(jira_projects().get_json())
		d['jira_projects'] = task
	except Exception as e:
		pass

	#Add weighted variables [show if no weighted variables set]
	try:
		task = {}
		task['title'] = 'Add weighted variables'
		task['description'] = "Weighted variables are used as metrics when calculating bug priority. An example might be Impact or Scope. The weight is the coefficient of the variable in the Raw P formula."
		task['data'] = len(weighted_variables().get_json()['weighted_variables'])
		d['weighted_variables'] = task
	except:
		pass

	#Set a raw p formula [show if no raw p formula set]
	try:
		task = {}
		task['title'] = 'Set the Raw P formula'
		task['description'] = "The Raw P formula is used to calculate each issue's raw priority value. It can consist of weighted variables, real numbers, and the special variable cases_attached, which represents the number of Salesforce cases attached to the issue."
		task['data'] = len(raw_p_formula().get_json())
		d['raw_p_formula'] = task
	except:
		pass

	#Set a display p formula [show if no display p formula set]
	try:
		task = {}
		task['title'] = 'Configure the Display P formula'
		task['description'] = "The Display P formula assigns a priority label (e.g., P0, P1, etc.) and color to each issue, depending on its Raw P value."
		task['data'] = len(display_p_formula().get_json())
		d['display_p_formula'] = task
	except:
		pass

	#Set variable values for issues [show if any values are missing]
	try:
		task = {}
		task['title'] = 'Enter variable values for issues'
		task['description'] = "Each issue must have a value entered for each weighted variable before its priority can be calculated."

		sql = query("select jira_issues.issue_id, issue_key, project_name, cases_attached, summary, status from jira_issues LEFT JOIN jira_projects ON jira_projects.project_id = jira_issues.project_id where raw_p is null")
		task['data'] = sql
		d['weighted_variable_values'] = task
	except:
		pass

	#Delete or ignore issues that are not found in JIRA, but exist locally [/sync will return a list of issues that may need to be deleted]
	try:
		task = {}
		task['title'] = 'Delete issue that have been resolved in JIRA'
		task['description'] = "When an issue is marked as resolved in JIRA, you have the option to delete the local copy of the issue (so as to remove it from the table of issues), or ignore (and keep the local copy of the issue in the table). If the issue is ever reopened in JIRA, it will be imported as a new issue."
		d['suggested_for_deletion'] = task
	except:
		pass

	return jsonify(d)

@app.route('/api/custom_attributes', methods=['GET','POST'])
def custom_attributes():
	d = {'errors':[]}
	if request.method == 'POST':
		try:
			body = request.json
			push("DELETE FROM custom_attributes WHERE 1")
			for attr_name in body:
				for option in body.get(attr_name):
					if option:
						push("INSERT INTO custom_attributes (attr_name, attr_option) VALUES (?,?)",(attr_name,option))
		except sql.IntegrityError as e:
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
	for attr in query("SELECT * FROM custom_attributes"):
		if (d['attributes'].get(attr['attr_name'])): #if the object alrady exists in the response
			d["attributes"][attr['attr_name']].append(attr.get('attr_option'))
		else:
			d["attributes"][attr['attr_name']] = [attr.get('attr_option')]

	return jsonify(d)

@app.route('/api/issue_attributes', methods=['GET','POST'])
def issue_attributes():
	if request.method == 'POST':
		try:
			body = request.json
			issue_id = body['issue_id']
			attr_name = body['attr_name']
			attr_option = body['attr_option']
			try:
				push("INSERT INTO issue_attributes (issue_id, attr_name, attr_option) VALUES (?,?,?)",(issue_id, attr_name, attr_option))
			except:
				push("UPDATE issue_attributes SET attr_option = ? WHERE issue_id = ? AND attr_name = ?",(attr_option, issue_id, attr_name))
		except sql.IntegrityError as e:
			print(type(e).__name__,e)
			d['errors'].append("Integrity Error")
		except KeyError as e:
			print(type(e).__name__,e)
			d['errors'].append("One or more fields are missing")
		except Exception as e:
			print(type(e).__name__,e)
			d['errors'].append("An unknown error occurred")

	#GET
	d = {}
	records = query("SELECT issue_id, attr_name, attr_option FROM issue_attributes")
	for record in records:
		if not d.get(record['issue_id']):
			d[record['issue_id']] = {}
		d[record['issue_id']][record['attr_name']] = record['attr_option']
	return jsonify(d)

if __name__ == '__main__':
	app.run()




