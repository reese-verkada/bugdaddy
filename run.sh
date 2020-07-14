#!/bin/bash

# If SECRET_ID has a value, pull secrets from AWS
if [[ ! -z $SECRET_ID ]]; then
	# Get secret from AWS and parse as JSON
	for s in $(aws secretsmanager get-secret-value --secret-id $SECRET_ID --query SecretString --output text | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" ); do
	    # Export env var
	    export $s
	done
fi

gunicorn -b 0.0.0.0:5000 --access-logfile - --log-level debug run:app
