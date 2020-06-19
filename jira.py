from urllib3.util.url import parse_url
import requests
import re

class Jira:

	def __init__(self, username, password, url):
		self.username = username
		self.password = password
		self.url = parse_url(url)
		self.url = parse_url('https://'+self.url.host+'/rest/api/2/')

	def __make_url(self,endpoint):
		url = parse_url(self.url.scheme+"://"+self.url.host+self.url.path+endpoint).url
		return url

	def get(self,endpoint,params={}):
		resp = requests.get(self.__make_url(endpoint),auth=(self.username,self.password),params=params)
		resp.raise_for_status()
		return resp.json()

	def post(self,endpoint,payload):
		resp = requests.post(self.__make_url(endpoint),auth=(self.username,self.password),json=payload)
		resp.raise_for_status()
		try:
			return response.json()
		except:
			return {}

	def put(self,endpoint,payload):
		resp = requests.put(self.__make_url(endpoint),auth=(self.username,self.password),json=payload)
		resp.raise_for_status()
		try:
			return response.json()
		except:
			return {}

	def project(self,projectId=None):
		if projectId:
			return self.get('project/'+str(projectId))
		return self.get('project')

	def search(self,jql="",fields="id",maxResults=100,startAt=0):
		params = {
			'jql':jql,
			'fields':fields,
			'maxResults':maxResults,
			'startAt':startAt
		}
		return self.get('search',params)

	def issues(self,issues,fields="id",maxResults=100,startAt=0):
		if issues:
			jql="id="+str(issues[0])
			for issue in issues[1:]:
				jql += " or id="+str(issue)
			return self.search(jql,fields,maxResults,startAt)
		else:
			return []

	def comments(self,issue_key):

		def account_replace(match):
			string = match.group()
			accountid = string.split(':')[1][:-1]
			try:
				account = self.get('user',{'accountId':accountid})
				displayName = account.get('displayName',"Unknown")
				return "@" + displayName
			except:
				return "@Unknown"


		if issue_key:
			comments = []
			try:
				data = self.get('issue/'+issue_key+'/comment?maxResults=2&orderBy=-created')
				comments = data.get('comments',[])
				comments.reverse()
				for comment in comments:
					comment['body'] = re.sub(r'\[~accountid:[a-z0-9]*\]', account_replace, comment['body'])
			finally:
				return comments

		else:
			return []