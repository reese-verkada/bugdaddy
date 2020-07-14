#!/usr/bin/env python3

import flask
import sqlite3 as sql

def run():
	### init the database
	#connect to db
	conn = sql.connect('db/bugdaddy.db')
	conn.execute('pragma foreign_keys=ON')
	c = conn.cursor()

	#jira_projects table
	q = """
	CREATE TABLE IF NOT EXISTS jira_projects (
		project_id INTEGER PRIMARY KEY NOT NULL,
		project_name TEXT NOT NULL
	)
	"""
	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS jira_url (
		jira_url TEXT PRIMARY KEY NOT NULL
	)
	"""
	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS weighted_variables (
		variable_name TEXT PRIMARY KEY NOT NULL,
		variable_weight REAL NOT NULL
	)
	"""
	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS weighted_variable_values (
		issue_id INTEGER NOT NULL,
		variable_name TEXT NOT NULL,
		value REAL NOT NULL,
		PRIMARY KEY (issue_id, variable_name),
		FOREIGN KEY (issue_id) REFERENCES jira_issues (issue_id)
			ON DELETE CASCADE
			ON UPDATE CASCADE,
		FOREIGN KEY (variable_name) REFERENCES weighted_variables (variable_name)
			ON DELETE CASCADE
			ON UPDATE CASCADE
	)
	"""
	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS raw_p_formula (
		formula TEXT PRIMARY KEY
	)
	"""
	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS display_p_formula (
		display_p TEXT PRIMARY KEY NOT NULL,
		low REAL NOT NULL,
		color TEXT,
		emoji TEXT
	)
	"""
	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS jira_issues (
		issue_id INTEGER PRIMARY KEY NOT NULL,
		project_id INTEGER,
		issue_key TEXT NOT NULL UNIQUE,
		priority TEXT,
		raw_p REAL,
		display_p TEXT,
		delete_ignore BOOLEAN NOT NULL DEFAULT 0,
		summary TEXT,
		status TEXT NOT NULL,
		FOREIGN KEY (display_p) REFERENCES display_p_formula(display_p)
			ON DELETE SET NULL
			ON UPDATE CASCADE,
		FOREIGN KEY (project_id) REFERENCES jira_projects(project_id)
			ON DELETE CASCADE
			ON UPDATE CASCADE
	)
	"""
	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS sf_issues (
		issue_id INTEGER PRIMARY KEY NOT NULL,
		total_spend REAL NOT NULL DEFAULT 0.0,
		cases_attached INTEGER NOT NULL DEFAULT 0,
		created_by TEXT NOT NULL DEFAULT 'Unknown'
	)
	"""

	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS custom_attributes (
		attr_name TEXT NOT NULL,
		attr_option TEXT NOT NULL,
		PRIMARY KEY (attr_name, attr_option)
	)
	"""

	c.execute(q)

	q = """
	CREATE TABLE IF NOT EXISTS issue_attributes (
		issue_id INTEGER NOT NULL,
		attr_name TEXT NOT NULL,
		attr_option TEXT NOT NULL,
		PRIMARY KEY (issue_id, attr_name)
		FOREIGN KEY (issue_id) REFERENCES jira_issues(issue_id)
			ON DELETE CASCADE
			ON UPDATE CASCADE
	)
	"""

	c.execute(q)

	conn.commit()
	conn.close()

if __name__ == '__main__':
	run()


#tables needed
# jira_projects(*project_id,project_name)
# jira_url(*jira_url)
# weighted_variables(*variable_name,variable_weight)
# jira_issues(*issue_id,cases_attached,raw_p,status)
# raw_p_formula(formula)
# display_p_formula(*order,label,range)
# 

