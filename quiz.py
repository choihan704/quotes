from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

import requests
from bs4 import BeautifulSoup as bs
import time

app = Flask(__name__)

# for local PostgreSql server with local execution
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:password@localhost/quotes'
# for heroku execution
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://bgxfydqzvnvhee:737860bce056fade50d32ecf235f955ebe36537fae785ab87c5b11b9d82d5f53@ec2-54-152-28-9.compute-1.amazonaws.com:5432/dc61fetp95p5mc'
# for local execution with Heroku postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bgxfydqzvnvhee:737860bce056fade50d32ecf235f955ebe36537fae785ab87c5b11b9d82d5f53@ec2-54-152-28-9.compute-1.amazonaws.com:5432/dc61fetp95p5mc'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Cashwalk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(2000))
    answer = db.Column(db.String(20))
    

@app.route('/')
def index():
    result = Cashwalk.query.order_by(desc(Cashwalk.id)).all()
    return render_template('quizindex.html', result=result)

@app.route('/quiz')
def quiz():
    main_scraper("https://luckyquiz3.blogspot.com/")

    return render_template('quiz.html')

@app.route('/process', methods = ['POST'])
def process():
    question = request.form['question']
    answer = request.form['answer']
    quiz = Cashwalk(question=question, answer=answer)
    db.session.add(quiz)
    db.session.commit()

    return redirect(url_for('index'))

def getnewquiz():
    return 

START_QUSETION_STR = "[퀴즈]"
START_ANSWER_STR = "정답은"
END_ANSWER_STR = "입니다."

def main_scraper(url):
    source_code = requests.get(url)
    source_text = source_code.text
    soup = bs(source_text, "html.parser")

    quizlist = soup.find_all("article")
    for q in quizlist:
        #print(q)
        tag = q.findAll('span', attrs={'class':'entry-tag'})
        if len(tag) > 0 :
            #print(tag[0].text)
            #if tag[0].text == "캐시워크 돈버는퀴즈" or tag[0].text == "캐시닥/타임스프레드 오늘의퀴즈":
            if "캐시워크" in tag[0].text or "캐시닥" in tag[0].text:
                #print(tag[0].text)
                url = q.find('a', attrs={'class':'entry-title-link'})
                #print(url['href'])

                quiz_code = requests.get(url['href'])
                quiz_text = quiz_code.text
                quiz = bs(quiz_text, "html.parser")
                #print(quiz)
                quizarea = quiz.findAll('div', attrs={'id': 'quizarea'})
                #print("=== START quizarea")
                #print(quizarea)
                #print("=== END quizarea")
                if len(quizarea) > 0 :
                    elements = quizarea[0].findAll('div', {'style':'text-align: center;'})

                    for e in elements:
                        #print("START DIV Element")
                        #print(e)
                        #print("END DIV Element")
                        divline = e.text
                        if len(divline) < 20:
                            continue
                        if divline == "[퀴즈]정답은 잠시 후 공개 입니다.":
                            break

                        #print("QUESTION: ", divline)
                        split_quiz(divline)

                time.sleep(1)

def strip_unknown(line):
    new_line = ""
    for c in line:
        if not c.isspace():
            new_line = new_line + c
        # else:
        #     print("Space")
            
    return new_line

def strip_white_space(line):
    return line.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "").replace("\xa0", "")

def split_quiz(line):
    start = line.find(START_QUSETION_STR)
    end = line.rfind(START_ANSWER_STR)
    # print(start)
    # print(end)
    if start == -1:
        if end == -1:
            question = line
            answer = ""
        else:
            question = line[0:end]
            aend = line.rfind(END_ANSWER_STR)
            if aend == -1:
                answer = ""
            else:
                answer = line[end + len(START_ANSWER_STR):aend]
    else:
        if end == -1:
            question = line[len(START_QUSETION_STR):]
            answer = ""
        else:
            question = line[len(START_QUSETION_STR):end]
            aend = line.rfind(END_ANSWER_STR)
            if aend == -1:
                answer = ""
            else:
                answer = line[end + len(START_ANSWER_STR):aend]

    strip_question = strip_white_space(question)
    strip_answer = strip_white_space(answer)
    strip_answer = strip_unknown(answer)
    #print("Q:", question)
    #print("A:", strip_answer)
    #print("K:", strip_question)

    result = Cashwalk.query.filter_by(question = question).all()
    if len(result) == 0 :
        #print("Add DB")
        #print("Q:", question)
        #print("A:", strip_answer)

        quiz = Cashwalk(question=question, answer=strip_answer)
        db.session.add(quiz)
        db.session.commit()
    # else:
    #     print("Found in DB")
    
    # if not strip_question in Quiz:
    #     if len(strip_answer) > 0:
    #         Quiz[strip_question] = strip_answer
    #     else:
    #         print("Not found answer for ", strip_question)
    # else:
    #     print("*** Answer is ", Quiz[strip_question])
    #     if new_answer != "" and Quiz[strip_white_space(question)] != new_answer:
    #         Quiz[strip_white_space(question)] = new_answer
