from flask import Flask, request, render_template, jsonify, abort, make_response, url_for
from newspaper import Article

# output:
# [
#   {
#         'question': question_text,
#         'answer': answer_text,
#         'question_type': question_type, 
#         'source_sentence': source_sentence
#   }, 
#   {..}, {..}, {..}
# ]

app = Flask(__name__)

# use this method to get questions
@app.route('/gadfly/api/v1.0/questions', methods=['GET'])
def get_questions():
    url = request.args.get('url')
    articleText = get_article_text(url)
    # send articleText to nlp, get a list of dict
    return jsonify({'questions': [make_public_question(question) for question in questions]})

@app.route('/gadfly/api/v1.0/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    question = [question for question in questions if question['id'] == question_id]
    if len(question) == 0:
        abort(404)
    return jsonify({'questions': [make_public_question(question) for question in questions]})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

def make_public_question(question):
    new_question = {}
    for field in question:
        if field == 'id':
            new_question['uri'] = url_for('get_question', question_id=question['id'], _external=True)
        else:
            new_question[field] = question[field]
    return new_question

def get_article_text(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text.replace("\n", "")

if __name__ == '__main__':
    app.run(debug=True)