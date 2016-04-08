from flask import Flask, request, jsonify, make_response
from newspaper import Article
from TheGadflyProject.gadfly import gap_fill_generator as gfg
import os
from flask.ext.cors import CORS, cross_origin
import re

# output:
# [
#   {
#         'question': question_text,
#         'answer': answer_text,
#         'source_sentence': source_sentence
#   },
#   {..}, {..}, {..}
# ]

app = Flask(__name__)
app.config['DEBUG'] = True
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# use this method to get questions
@app.route('/gadfly/api/v1.0/questions', methods=['GET'])
@cross_origin()
def get_questions():
    url = request.args.get('url')
    article_text = get_article_text(url)
    questions = generate_questions(article_text)
    for key in ["_type", "_subtype"]:
        for q in questions:
            q.pop(key)
    return jsonify({'questions': questions})


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
    article = Article(url)
    article.download()
    article.parse()
    return clean_text(article.text)


def clean_text(article):
    article = (re.sub(("“"),'"',article))
    article = (re.sub(("”"),'"',article))
    article = (re.sub(("’"),"'",article))
    return (re.sub(("[\n*]"),"",article))
    
    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8081)
