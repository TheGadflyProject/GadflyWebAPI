from runserver import db, ma
from sqlalchemy.dialects.postgresql import JSON, ARRAY


class QuestionGenRequest(db.Model):
    __tablename__ = 'question_generation_request'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    questions = db.Column(JSON)
    question_type = db.Column(db.String())

    def __repr__(self):
        return '<id {}'.format(self.id)


class NewsArticle(db.Model):
    __tablename__ = 'news_article'

    id = db.Column(db.String(), primary_key=True)
    url = db.Column(db.String())
    article_text = db.Column(db.Text())
    domain = db.Column(db.String())
    questions = db.relationship('Question', backref='news_article',
                                lazy='dynamic')


class Question(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.String(), primary_key=True)
    question_text = db.Column(db.Text())
    source_sentence = db.Column(db.Text())
    answer_choices = db.relationship('AnswerChoice', backref='question',
                                     lazy='dynamic')
    correct_answer = db.Column(db.String())
    # reactions = db.Column(ARRAY())
    good_question_votes = db.Column(db.Integer)
    bad_question_votes = db.Column(db.Integer)
    news_article_id = db.Column(db.String(), db.ForeignKey('news_article.id'))


class AnswerChoice(db.Model):
    __tablename__ = "answer_choice"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_id = db.Column(db.String(), db.ForeignKey('question.id'))
    answer = db.Column(db.String())

    def __repr__(self):
        return '<answer: {}>'.format(self.answer)


class NewsArticleSchema(ma.ModelSchema):
    class Meta:
        model = NewsArticle


class QuestionSchema(ma.ModelSchema):
    class Meta:
        model = Question


class AnswerChoice(ma.ModelSchema):
    class Meta:
        model = AnswerChoice
