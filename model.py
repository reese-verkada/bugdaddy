from main import db
from sqlalchemy_serializer import SerializerMixin

issue_attributes = db.Table('issue_attributes',
	db.Column('issue_id', db.Integer, db.ForeignKey('jira_issues.issue_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False),
	db.Column('attr_name', db.String(255), primary_key=True, nullable=False),
	db.Column('attr_option', db.String(255), nullable=False),
	db.ForeignKeyConstraint(["attr_name", "attr_option"],["custom_attributes.attr_name", "custom_attributes.attr_option"], ondelete="CASCADE", onupdate="CASCADE")
)

class JiraProject(db.Model, SerializerMixin):
	__tablename__ = "jira_projects"
	serialize_rules = ('-issues',)
	project_id = db.Column(db.Integer, primary_key=True, nullable=False)
	project_name = db.Column(db.String(255), nullable=False)
	issues = db.relationship('JiraIssue', backref='project', lazy=True, passive_deletes=True)

class WeightedVariable(db.Model, SerializerMixin):
	__tablename__ = "weighted_variables"
	variable_name = db.Column(db.String(255), primary_key=True, nullable=False)
	variable_weight = db.Column(db.Float, nullable=False)

class WeightedVariableValue(db.Model, SerializerMixin):
	__tablename__ = "weighted_variable_values"
	serialize_rules = ('-weighted_variable',)
	issue_id = db.Column(db.Integer, db.ForeignKey('jira_issues.issue_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
	variable_name = db.Column(db.String(255), db.ForeignKey('weighted_variables.variable_name', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
	value = db.Column(db.Float, nullable=False)
	weighted_variable = db.relationship('WeightedVariable')

class RawPFormula(db.Model, SerializerMixin):
	__tablename__ = "raw_p_formula"
	formula_id = db.Column(db.Integer, primary_key=True)
	formula = db.Column(db.Text, nullable=True)

class DisplayPFormula(db.Model, SerializerMixin):
	__tablename__ = "display_p_formula"
	serialize_rules = ('-issues',)
	display_p = db.Column(db.String(255), primary_key=True, nullable=False)
	low = db.Column(db.Float, nullable=False)
	color = db.Column(db.String(255), nullable=True)
	emoji = db.Column(db.String(255), nullable=True)
	issues = db.relationship('JiraIssue', backref='display_p_details', lazy=True, passive_deletes=True, passive_updates=True)

class JiraIssue(db.Model, SerializerMixin):
	__tablename__ = "jira_issues"
	serialize_rules = ('-variable_values','-attributes')
	issue_id = db.Column(db.Integer, primary_key=True, nullable=False)
	project_id = db.Column(db.Integer, db.ForeignKey('jira_projects.project_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
	issue_key = db.Column(db.String(255), nullable=False, unique=True)
	priority = db.Column(db.String(255), nullable=True)
	raw_p = db.Column(db.Float, nullable=True)
	display_p = db.Column(db.String(255), db.ForeignKey('display_p_formula.display_p', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
	delete_ignore = db.Column(db.Boolean, nullable=False, default=False)
	summary = db.Column(db.Text, nullable=True)
	status = db.Column(db.String(255), nullable=False)
	updated = db.Column(db.DateTime(timezone=True), nullable=True)
	created = db.Column(db.DateTime(timezone=True), nullable=True)
	assignee = db.Column(db.String(255), nullable=True)
	reporter = db.Column(db.String(255), nullable=True)
	variable_values = db.relationship('WeightedVariableValue', passive_deletes=True, passive_updates=True, lazy=True)
	attributes = db.relationship('CustomAttribute', secondary=issue_attributes, lazy=True, passive_updates=True, passive_deletes=True)

class SFIssue(db.Model, SerializerMixin):
	__tablename__ = "sf_issues"
	issue_id = db.Column(db.Integer, primary_key=True, nullable=False)
	total_spend = db.Column(db.Float, nullable=False, default=0.0)
	cases_attached = db.Column(db.Integer, nullable=False, default=0)
	created_by = db.Column(db.String(255), nullable=False, default="Unknown")

class CustomAttribute(db.Model, SerializerMixin):
	__tablename__ = "custom_attributes"
	attr_name = db.Column(db.String(255), primary_key=True, nullable=False)
	attr_option = db.Column(db.String(255), primary_key=True, nullable=False)

class User(db.Model, SerializerMixin):
	__tablename__ = "users"
	email = db.Column(db.String(255), primary_key=True, nullable=False)
	seen_change = db.Column(db.Integer, nullable=False)

class Change(db.Model, SerializerMixin):
	__tablename__ = "changes"
	change_id = db.Column(db.Integer, primary_key=True, nullable=False)
	issue_id = db.Column(db.Integer, db.ForeignKey('jira_issues.issue_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
	issue = db.relationship('JiraIssue', lazy=False, uselist=False, passive_deletes=True, passive_updates=True)
	old = db.Column(db.Text, nullable=True)
	new = db.Column(db.Text, nullable=True)
