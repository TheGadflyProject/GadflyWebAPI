from runserver import db
from sqlalchemy.dialects.postgresql import JSON


class QuestionGenRequest(db.Model):
    __tablename__ = 'question_generation_request'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    questions = db.Column(JSON)
    question_type = db.Column(db.String())

    def __init__(self, url, questions, question_type):
        self.url = url
        self.questions = questions
        self.question_type = question_type

    def __repr__(self):
        return '<id {}'.format(self.id)
