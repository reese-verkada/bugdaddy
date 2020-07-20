# BugDaddy
BugDaddy is a web app for tracking and displaying product issues.  It pulls data from JIRA (the source of truth for bugs) and Salesforce (the source of truth for information about cases linked to bugs) and presents these data to you in a unified and easy-to-digest manner.  There are two components to BugDaddy: a backend (written in Python using Flask) and a frontend (written in Javascript using Vue.js).  The frontend is a single page application (SPA) which interacts with the backend using a REST API.  The app can be deployed in one of three main ways:

1. In development mode by running the backend with `python3 run.py` and frontend with `npm run dev`
2. In production mode by using Docker-Compose with the included `docker-compose.yml` file (`docker-compose up --build -d`)
3. In production mode by using some other container orchestration system, such as Kubernetes (using Docker as the underlying container engine)

Development mode runs the backend using Flask's built-in WSGI web server, and runs the frontend using a built-in node web server.  Production mode runs the backend with a Gunicorn web server in one container, and runs the frontend using an nginx reverse proxy in another container.

In depth instructions for each of these three methods are provided further on.

## Index of this directory
This section provides a brief overview of the files and folders located within this directory.
- `backend/`: This is the backend Python package and contains all the code for the backend service
- `db/`: If a local SQLite database is being used, it will be stored in this folder
- `frontend/`: This is the project folder for the frontend service
- `docker-compose.yml`: If using Docker-Compose, this file will be used by the command `docker-compose up --build -d`
- `Dockerfile`: This is the Dockerfile used to build the bugdaddy-backend Docker image
- `run.py`: This is the main entrypoint for running the backend (either directly with `python3 run.py` or using Gunicorn)
- `run.sh`: This bash script is run by the backend container to load secret values from AWS Secrets Manager and start the app with Gunicorn

## Salesforce and JIRA Setup
Before installing and running BugDaddy, please follow these steps to get everything you need from JIRA and Salesforce.

### How to set up app in Salesforce
You will need some values from Salesforce for your config file.  Please follow the steps below to set up BugDaddy as an app in SFDC and obtain the required tokens.
- Log in to Salesforce
- Go to Setup and search for App Manager
- Make a new connected app
- Call it whatever you want
- Ensure that the redirect url is https://login.salesforce.com/services/oauth2/success
- Make sure that OAuth is enabled
- Make sure the api and refresh_token scopes are added
- Save the app and write down the client/consumer ID and the client/consumer secret
- Click manage and policies and ensure that the expiration for the refresh token is "until revoked" (basically, we want the refresh token to never expire)

### How to get a refresh token from Salesforce
This guide will help you get a refresh token from Salesforce to put in the config.py file.
- Go to https://login.salesforce.com/services/oauth2/authorize?response_type=code&redirect_uri=https://login.salesforce.com/services/oauth2/success&client_id=<ConnectedAppClientID> in a web browser, making sure that <ConnectedAppClientID> is replaced with the client ID from App Manager
- You will be taken to SFDC and asked to sign in.  You should then be taken to a success page.  Please write down the code returned in the URL of this page
- Send a POST request (using curl or postman) to https://login.salesforce.com/services/oauth2/token?grant_type=authorization_code&redirect_uri=https://login.salesforce.com/services/oauth2/success&client_id=<ConnectedAppClientID>&client_secret=ConnectedAppSecret&code=<CodeFromStep1> replacing <ConnectedAppClientID> with the client ID from app manager, replacing CoonectedAppSecret with the secret from App Manager, and <CodeFromStep1> with the code you received in the response from the GET request
- This should return a JSON object with a refresh_token
- Write down the refresh_token
- In the config.py file, ensure there is a line that reads:
SALESFORCE_REFRESH_TOKEN = <refresh_token> (replacing <refresh_token> with the one received from the previous step)
Please note: if you are using AWS Secrets Manager or environment variables instead of hard-coded values in the config.py file, this refresh token should go there instead
- In the config.py file, ensure there is a line that reads:
SALESFORCE_INSTANCE = <url> (replacing <url> with the URL of your Salesforce instance.  For example, "https://company.my.salesforce.com")
Please note: if you are using AWS Secrets Manager or environment variables instead of hard-coded values in the config.py file, this URL should go there instead
- In the config.py file, ensure there is a line that reads:
SALESFORCE_CLIENT_ID = <client_id> (replacing <client_id> with the client ID from App Manager)
Please note: if you are using AWS Secrets Manager or environment variables instead of hard-coded values in the config.py file, this client ID should go there instead
- In the config.py file, ensure there is a line that reads:
SALESFORCE_CLIENT_SECRET = <secret> (replacing <secret> with the client secret from App Manager)
Please note: if you are using AWS Secrets Manager or environment variables instead of hard-coded values in the config.py file, this client secret should go there instead
  
### Creating the BugDaddy Salesforce report
BugDaddy relies on pulling data from a Saleforce report with a specific schema.  This guide will tell you how to make this report.
- Log in to SFDC and go to Reports
- Create a new report
- The type of the report should be `ZIssues with ZIssue_Case and Cases`
- The columns of the report should be (in this exact order):
  1. IssueId
  2. CaseId: Total Spend
  3. IssueKey
  4. ZIssue: Created By
- `Show Me` should be `All zissues`
- `Created` should be `All Time`
- Filters should be:
  1. Status not equal to Done
  2. Status not equal to Closed
  3. IssueType equals Bug
  4. IssueType equals Epic
  5. IssueType equals Story
- The logic for these filters should be `1 AND 2 AND (3 OR 4 OR 5)`
- Save the report
- In the config.py file, ensure there is a line that reads:
SALESFORCE_REPORT_ID = <report_id> (replacing <report_id> with the ID of the SFDC report found in its URL)
Please note: if you are using AWS Secrets Manager or environment variables instead of hard-coded values in the config.py file, this report ID should go there instead
  
### How to get an API token from JIRA
This guide will help you get an API token from JIRA to put in the config.py file.
- Log in to JIRA
- Go to Atlassian account settings
- Click the Security tab
- Click Create and manage API tokens
- Create a new API token and write it down
- In the config.py file, ensure there is a line that reads:
JIRA_URL = <url> (replacing <url> with the URL of your JIRA instance. For example, "https://company.atlassian.net")
Please note: if you are using AWS Secrets Manager or environment variables instead of hard-coded values in the config.py file, this URL should go there instead
- In the config.py file, ensure there is a line that reads:
JIRA_USERNAME = <username> (replacing <username> with your JIRA username)
Please note: if you are using AWS Secrets Manager or environment variables instead of hard-coded values in the config.py file, this username should go there instead
- In the config.py file, ensure there is a line that reads:
JIRA_PASSWORD = <api_token> (replacing <api_token> with the one received from the previous step)
Please note: if you are using AWS Secrets Manager or environment variables instead of hard-coded values in the config.py file, this api token should go there instead

## Development Mode
If you are not running the app using one of the containerized methods listed above, you will need to ensure these prerequisites are met first.

### Libraries required on system
- python3 (used for running the backend)
- pip3 (used for installing Python dependencies listed in `requirements.txt`
- xmlsec1 (used for the SAML portion of the backend)
- npm (used for running and installing the dependencies for the frontend)




