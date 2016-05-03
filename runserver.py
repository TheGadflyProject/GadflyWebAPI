from flask import Flask, request, jsonify, make_response
from newspaper import Article, Config
from TheGadflyProject.gadfly import gap_fill_generator as gfg
from TheGadflyProject.gadfly import mcq_generator as mcq
from flask.ext.cors import CORS, cross_origin
from flask.ext.sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from urllib.parse import urlparse
from hashlib import md5
from random import shuffle
import re
import os
import pprint


app = Flask(__name__)
app.config['DEBUG'] = True
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# Newspaper Config
config = Config()
config.fetch_images = False
# Postgres Config
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
ma = Marshmallow(app)


from models import QuestionGenRequest, NewsArticle, Question, QuestionSchema, AnswerChoice


question_schema = QuestionSchema(many=True)
pp = pprint.PrettyPrinter(indent=4)


# use this method to get questions
@app.route('/api/gap_fill_questions', methods=['GET'])
@cross_origin()
def get_gap_fill_questions():
    url = request.args.get('url')
    limit = int(request.args.get('limit') or 50)
    article_text = get_article_text(url)
    questions = generate_gap_fill_questions(article_text)
    num_questions = len(questions)

    for key in ["_type", "_subtype"]:
        for q in questions:
            q.pop(key)

    try:
        db.session.add(QuestionGenRequest(url=url, questions=questions,
                                          question_type="gap_fill"))
        db.session.commit()
    except Exception as e:
        print(e)

    try:
        parsed_url = urlparse(url)
        article_id = md5(article_text.strip().encode('utf-8'))

        if not NewsArticle.query.get(article_id.hexdigest()):
            db.session.add(
                NewsArticle(id=article_id.hexdigest(), url=url,
                            article_text=article_text.strip(),
                            domain=parsed_url.netloc)
            )
            db.session.commit()
    except Exception as e:
        print(e)

    for q in questions:
        q_id = md5(q.get('question').encode('utf-8'))

        if not Question.query.get(q_id.hexdigest()):
            try:
                db.session.add(
                    Question(id=q_id.hexdigest(),
                             question_text=q.get("question"),
                             source_sentence=q.get("source_sentence"),
                             correct_answer=q.get("answer"),
                             good_question_votes=0,
                             bad_question_votes=0,
                             news_article_id=article_id.hexdigest())
                )
                db.session.commit()

            except Exception as e:
                print("Unable to add item to database.")
                print(e)

    news_article = NewsArticle.query.get(article_id.hexdigest())
    questions = question_schema.dump(news_article.questions.all()).data
    shuffle(questions)
    return jsonify({
            'num_questions': min(limit, num_questions),
            'questions': questions[:limit]
            })


# use this method to get questions
@app.route('/api/multiple_choice_questions', methods=['GET'])
@cross_origin()
def get_multiple_choice_questions():
    url = request.args.get('url')
    limit = int(request.args.get('limit') or 50)
    article_text = get_article_text(url)
    questions = generate_multiple_choice_questions(article_text)
    num_questions = len(questions)

    for key in ["_type", "_subtype"]:
        for q in questions:
            q.pop(key)

    try:
        db.session.add(QuestionGenRequest(
                    url=url,
                    questions=questions,
                    question_type="multiple_choice",
                ))
        db.session.commit()
    except Exception as e:
        print(e)

    try:
        parsed_url = urlparse(url)
        article_id = md5(article_text.strip().encode('utf-8'))

        if not NewsArticle.query.get(article_id.hexdigest()):
            db.session.add(
                NewsArticle(
                    id=article_id.hexdigest(),
                    url=url,
                    article_text=article_text.strip(),
                    domain=parsed_url.netloc
                ))
            db.session.commit()
    except Exception as e:
        print(e)

    for q in questions:
        q_id = md5(q.get('question').encode('utf-8'))

        if not Question.query.get(q_id.hexdigest()):
            try:
                db.session.add(
                    Question(
                        id=q_id.hexdigest(),
                        question_text=q.get("question"),
                        source_sentence=q.get("source_sentence"),
                        correct_answer=q.get("answer"),
                        # reactions=[],
                        good_question_votes=0,
                        bad_question_votes=0,
                        news_article_id=article_id.hexdigest()
                    )
                )
                db.session.commit()

                for answer_choice in q.get("answer_choices"):
                    ac = AnswerChoice(
                            question_id=q_id.hexdigest(),
                            answer=answer_choice
                            )
                    db.session.add(ac)
                    db.session.commit()

            except Exception as e:
                print("Unable to add item to database.")
                print(e)

    # news_article = NewsArticle.query.get(article_id.hexdigest())
    # questions = question_schema.dump(news_article.questions.all()).data
    shuffle(questions)
    return jsonify({
            'num_questions': min(limit, num_questions),
            'questions': questions[:limit]
            })


@app.route('/api/question/<q_id>', methods=['GET'])
@cross_origin()
def question(q_id):
    question = {}
    try:
        question = Question.query.get(q_id)
        question = question_schema.dump([question]).data
    except Exception as e:
        print(e)
        print("unable to find {} in database".format(q_id))
    return jsonify({"question": question})


@app.route('/api/good_question/<q_id>', methods=['POST'])
@cross_origin()
def good_question(q_id):
    try:
        question = Question.query.get(q_id)
        question.good_question_votes += 1
        db.session.commit()
        return jsonify({'status': "success"})
    except Exception as e:
        print(e)
        print("unable to find {} in database".format(q_id))
        return jsonify({"status": "failed"})


@app.route('/api/bad_question/<q_id>', methods=['POST'])
@cross_origin()
def bad_question(q_id):
    try:
        question = Question.query.get(q_id)
        question.bad_question_votes += 1
        db.session.commit()
        return jsonify({'status': "success"})
    except Exception as e:
        print(e)
        print("unable to find {} in database".format(q_id))
        return jsonify({"status": "failed"})


@app.route('/api/article', methods=['GET'])
@cross_origin()
def get_article():
    url = request.args.get('url')
    article_text = get_article_text(url)
    return (article_text)


@app.route('/api/top_sentences', methods=['GET'])
@cross_origin()
def get_top_sentences():
    url = request.args.get('url')
    article_text = get_article_text(url)
    g = gfg.GapFillGenerator(article_text)
    top_sents = [sent.text for sent in g.top_sents]
    return jsonify({"top_sents": top_sents})


@app.route('/api/sentences', methods=['GET'])
@cross_origin()
def get_sentences():
    url = request.args.get('url')
    article_text = get_article_text(url)
    g = gfg.GapFillGenerator(article_text)
    sents = [sent.text for sent in g.sents]
    return jsonify({"sents": sents})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def generate_gap_fill_questions(article_text):
    q_gen = gfg.GapFillGenerator(article_text)
    return q_gen.output_questions()


def generate_multiple_choice_questions(article_text):
    q_gen = mcq.MCQGenerator(article_text)
    return q_gen.output_questions()


def get_article_text(url):
    article = Article(url, config)
    article.download()
    article.parse()
    return clean_text(article.text)


def clean_text(article):
    article = re.sub("“", '"', article)
    article = re.sub("”", '"', article)
    article = re.sub("’", "'", article)
    article = re.sub("Advertisement ", "", article)
    article = re.sub("Continue reading the main story", "", article)
    # Should replace "Photo RIO DE JANEIRO — BRAZIL" with "Photo - Brazil"
    article = re.sub("([A-Z]|\s)+\—", "", article)
    article = re.sub("Photo ", "", article)
    return re.sub("[\n*]", " ", article)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8081)
