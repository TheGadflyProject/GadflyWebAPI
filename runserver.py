from flask import Flask, request, jsonify, make_response
from newspaper import Article, Config
from TheGadflyProject.gadfly import gap_fill_generator as gfg
from flask.ext.cors import CORS, cross_origin
from flask.ext.sqlalchemy import SQLAlchemy
from urllib.parse import urlparse
import re
import os


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


from models import QuestionGenRequest, NewsArticle, Question


# use this method to get questions
@app.route('/gadfly/api/v1.0/gap_fill_questions', methods=['GET'])
@cross_origin()
def get_gap_fill_questions():
    url = request.args.get('url')
    article_text = get_article_text(url)
    questions = generate_questions(article_text)
    for key in ["_type", "_subtype"]:
        for q in questions:
            q.pop(key)
    try:
        db.session.add(QuestionGenRequest(
                    url=url,
                    questions=questions,
                    question_type="gap_fill",
                ))
        parsed_url = urlparse(url)
        db.session.add(
                NewsArticle(
                    url=url,
                    article_text=article_text,
                    domain=parsed_url.netloc
                ))
        question_objects = []
        for q in questions:
            question_objects.append(
                    Question(
                        question_text=q.question,
                        # answer_choices=[],
                        correct_answer=q.answer,
                        # reactions=[],
                        good_question_votes=0,
                        bad_question_votes=0
                    )
            )
        db.session.bulk_save_objects(question_objects)
        db.session.commit()
    except:
        print("Unable to add item to database.")
    return jsonify({'questions': questions})


@app.route('/gadfly/api/v1.0/article', methods=['GET'])
@cross_origin()
def get_article():
    url = request.args.get('url')
    article_text = get_article_text(url)
    return (article_text)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def generate_questions(article_text):
    blank_types = [gfg.GapFillBlankType.named_entities,
                   gfg.GapFillBlankType.noun_phrases]
    q_gen = gfg.GapFillGenerator(article_text, gap_types=blank_types,
                                 summarizer=gfg.tfidf)
    return q_gen.output_questions_to_list()


def get_article_text(url):
    # up = urlparse(url)
    # if (up.netloc == "www.nytimes.com"):
        # url = re.sub("www.nytimes.com", "mobile.nytimes.com", url)
        # print(url)
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
    return re.sub("[\n*]", " ", article)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8081)
