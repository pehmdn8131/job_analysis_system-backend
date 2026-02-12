from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Job(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    job_name=db.Column(db.String(100))
    skills=db.Column(db.Text)
    salary_max=db.Column(db.Integer)
    city=db.Column(db.String(50))
