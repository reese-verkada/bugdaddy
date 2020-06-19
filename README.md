Libs required on system:
- python3
- pip3
- xmlsec1

How to set up app in Salesforce
- Go to Setup and search for App Manager
- Make a new connected app
- Call it whatever you want
- Ensure that the redirect url is https://login.salesforce.com/services/oauth2/success
- Make sure that OAuth is enabled
- Make sure the api and refresh_token scopes are added
- Save the app and write down the client/consumer ID and the client/consumer secret
- Click manage and policies and ensure that the expiration for the refresh token is "until revoked" (basically, we want the refresh token to never expire)

How to get a refresh token from Salesforce
- This guide will help you get a refresh token from Salesforce to put in the config.py file.
- Go to https://login.salesforce.com/services/oauth2/authorize?response_type=code&redirect_uri=https://login.salesforce.com/services/oauth2/success&client_id=<ConnectedAppClientID> in a web browser, making sure that <ConnectedAppClientID> is replaced with the client ID from App Manager
- You will be taken to SFDC and asked to sign in.  You should then be taken to a success page.  Please write down the code returned in the URL of this page
- Send a POST request (using curl or postman) to https://login.salesforce.com/services/oauth2/token?grant_type=authorization_code&redirect_uri=https://login.salesforce.com/services/oauth2/success&client_id=<ConnectedAppClientID>&client_secret=ConnectedAppSecret&code=<CodeFromStep1> replacing <ConnectedAppClientID> with the client ID from app manager, replacing CoonectedAppSecret with the secret from App Manager, and <CodeFromStep1> with the code you received in the response from the GET request
- This should return a JSON object with a refresh_token
- Write down the refresh_token
- In the config.py file, ensure there is a line that reads:
SALESFORCE_REFRESH_TOKEN = <refresh_token> replacing <refresh_token> with the one received from the previous step


