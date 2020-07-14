from urllib3.util.url import parse_url
import json
import requests

class Salesforce:

	def __init__(self, url, refresh_token, clientId, secret, reportId):
		self.refresh_token = refresh_token
		self.client_id = clientId
		self.secret = secret
		self.reportId = reportId
		self.issues = {}
		self.instanceUrl = parse_url(url)
		self.instanceUrl = parse_url('https://'+self.instanceUrl.host+'/services/data/v48.0/')
		self.authUrl = "https://login.salesforce.com/services/oauth2/token"

	def __make_url(self,endpoint):
		url = parse_url(self.instanceUrl.scheme+"://"+self.instanceUrl.host+self.instanceUrl.path+endpoint).url
		return url

	def __get_access_token(self):
		data = {
			"grant_type":"refresh_token",
			"client_id":self.client_id,
			"client_secret":self.secret,
			"refresh_token":self.refresh_token
		}
		resp = requests.post(self.authUrl,data=data)
		resp.raise_for_status()
		return resp.json().get('access_token')


	def __get_report(self):
		self.issues = {}
		headers = {"Authorization": "Bearer "+self.__get_access_token()}
		resp = requests.get(self.__make_url("analytics/reports/"+self.reportId),headers=headers)
		resp.raise_for_status()
		data = resp.json()
		rows = data.get('factMap').get('T!T').get('rows')
	
		for row in rows:
			cols = row.get('dataCells')
			issue_id = cols[0].get('value')
			total_spend = cols[1].get('value').get('amount')
			issue_key = cols[2].get('value')
			created_by = cols[3].get('label')
			
			#if we haven't come across this issue yet
			if not self.issues.get(issue_id):
				#create the basic issue object
				self.issues[issue_id] = {
					'total_spend':0.0,
					'cases_attached':0,
					'issue_key':issue_key,
					'created_by':created_by
				}

			#update the issue object
			self.issues[issue_id]['total_spend'] += total_spend
			self.issues[issue_id]['cases_attached'] += 1

	def get_issue(self, issue_id):
		self.__get_report()
		return self.issues.get(issue_id)

	def get_issues(self):
		self.__get_report()
		return self.issues

