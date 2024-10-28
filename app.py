from flask import Flask, request, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/quiz_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Error(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)

db.create_all()

# 여러 챕터의 문제 리스트를 CSV 파일로부터 불러옵니다.
chapters = {}
chapter_files = ['chapter1.csv', 'chapter2.csv', 'chapter3.csv']
for chapter_file in chapter_files:
    chapter_name = chapter_file.replace('.csv', '')
    questions = []
    with open(chapter_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            questions.append({'sentence': row[0].replace('"', ''), 'answer': row[1].strip().replace('"', '')})
    chapters[chapter_name] = questions

remaining_questions = []
correct_answers = 0
answered_questions = 0

@app.route('/')
def index():
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>챕터 선택</title>
        </head>
        <body>
            <h1>챕터 선택</h1>
            <form action="{{ url_for('select_chapter') }}" method="post">
                {% for chapter in chapters %}
                    <input type="checkbox" name="chapters" value="{{ chapter }}"> {{ chapter }}<br>
                {% endfor %}
                <button type="submit">선택 완료</button>
            </form>
        <h2>오류 게시판</h2>
<form action="{{ url_for('report_error') }}" method="post">
    <label for="error_message">오류 내용:</label><br>
    <textarea id="error_message" name="error_message" rows="4" cols="50"></textarea><br><br>
    <button type="submit">오류 제출</button>
</form>
<hr>
<h3>제출된 오류들:</h3>
<ul>
    {% for error in Error.query.all() %}
        <li>{{ error.message }}</li>
    {% endfor %}
</ul>
</body>
</html>
    ''', chapters=chapters)

@app.route('/select_chapter', methods=['POST'])
def select_chapter():
    global remaining_questions, answered_questions, correct_answers

    selected_chapters = request.form.getlist('chapters')
    remaining_questions = []
    for chapter in selected_chapters:
        remaining_questions.extend(chapters[chapter])
    random.shuffle(remaining_questions)
    correct_answers = 0
    answered_questions = 0
    return redirect(url_for('quiz'))

@app.route('/report_error', methods=['POST'])
def report_error():
    error_message = request.form['error_message']
    if error_message:
        new_error = Error(message=error_message)
        db.session.add(new_error)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/quiz')
def quiz():
    global remaining_questions, answered_questions, correct_answers

    if len(remaining_questions) == 0:
        return render_template_string('''
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>퀴즈 완료</title>
            </head>
            <body>
                <h1>퀴즈 완료!</h1>
                <p>{{ correct_answers }} / {{ answered_questions }} 문제 맞음</p>
                <a href="{{ url_for('index') }}">다시 시작하기</a>
            </body>
            </html>
        ''', correct_answers=correct_answers, answered_questions=answered_questions)

    question = random.choice(remaining_questions)
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>빈칸 채우기 퀴즈</title>
        </head>
        <body>
            <h1>빈칸 채우기 퀴즈</h1>
            <p>{{ correct_answers }} / {{ answered_questions }} 문제 맞음</p>
            <div style="width: 100%; background-color: #f3f3f3;">
                <div style="width: {{ progress }}%; background-color: #4caf50; height: 20px;"></div>
            </div>
            <form action="{{ url_for('check_answer') }}" method="post">
                <p>{{ question['sentence'] }}</p>
                <input type="hidden" name="sentence" value="{{ question['sentence'] }}">
                <input type="hidden" name="answer" value="{{ question['answer'] }}">
                <input type="text" name="user_answer">
                <button type="submit">제출</button>
            </form>
        </body>
        </html>
    ''', question=question, correct_answers=correct_answers, answered_questions=answered_questions, progress=(correct_answers / max(answered_questions, 1)) * 100)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    global remaining_questions, answered_questions, correct_answers

    sentence = request.form['sentence']
    correct_answer = request.form['answer'].strip().lower()
    user_answer = request.form['user_answer'].strip().lower()

    answered_questions += 1

    if user_answer == correct_answer:
        correct_answers += 1
        remaining_questions = [q for q in remaining_questions if q['sentence'] != sentence]
        return redirect(url_for('quiz'))
    else:
        return render_template_string('''
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>틀렸습니다!</title>
            </head>
            <body>
                <h1>틀렸습니다!</h1>
                <p>정답: {{ correct_answer }}</p>
                <a href="{{ url_for('quiz') }}">다음 문제로 넘어가기</a>
            </body>
            </html>
        ''', correct_answer=correct_answer)

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
