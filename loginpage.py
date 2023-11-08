from flask import Flask, render_template, request, session, make_response
import threading
import time
from datetime import datetime
import bcrypt
from elasticsearch import Elasticsearch
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER, logging
import feedparser
import requests

# Disminuye la cantidad de logs 
LOGGER.setLevel(logging.WARNING)

# Crea la aplicacion con Flask
app = Flask(__name__)  
app.secret_key = "ayush"  

# Arrancamos la base de datos en el puerto 9200
es = Elasticsearch("http://localhost:9200")

'''
Esta funcion genera cookies para comprobar si un usuario accede por primera vez o no. En caso afirmativo devuelve una web
u otra.
La funcion se activa al acceder al recurso ubicado en /.
'''
@app.route('/')  
def home():    
  if 'first_time' in request.cookies:
    if 'username' in session:
      username = session['username']
      return make_response(render_template("homepageRegistered.html",username=username))
    else:
      return make_response(render_template("homepage2.html"))
  else:
    resp = make_response(render_template("homepage_firstTime.html"))
    resp.set_cookie('first_time', 'false', max_age=60*60*24*365)
    return resp
'''
La funcion logged 
'''
@app.route('/registered')
def logged():
  if 'email' in session:   
    username = session['username']
    return make_response(render_template('homepageRegistered.html',username=username))

@app.route('/gold',methods=['GET'])
def gold_inst():
  op = webdriver.ChromeOptions()
  op.add_argument('headless')
  driver = webdriver.Chrome(options=op)
  url = 'https://es.investing.com/commodities/gold'
  driver.get(url)
  valores = driver.find_elements(By.XPATH, '//div/div/div/div/div/div/div/div/div')
  val = valores[13].text
  gold = val[:9]
  username = session['username']
  return render_template("homepageRegistered.html",gold_val=gold,username=username)

@app.route('/goldFirst',methods=['GET'])
def gold_inst_first():
  op = webdriver.ChromeOptions()
  op.add_argument('headless')
  driver = webdriver.Chrome(options=op)
  url = 'https://es.investing.com/commodities/gold'
  driver.get(url)
  valores = driver.find_elements(By.XPATH, '//div/div/div/div/div/div/div/div/div')
  val = valores[13].text
  gold = val[:9]
  return render_template("homepage_firstTime.html",gold_val=gold)
  
@app.route('/register')  
def register():  
	return render_template("registerpage3.html")  

@app.route('/login')
def login():
   return render_template("loginpage.html")

@app.route('/graph',methods=['GET'])
def show_graph():
  return render_template('graph.html')

@app.route('/feed',methods=['GET'])
def show_feed():
   feed_url = 'https://grovestreams.com/api/component/114b6faa-03b2-39d7-8308-4ab2a358782d/stream/5bb43b08-138a-3643-9f5d-5dd1c95e6afe/feed/rss.xml?org=228f917a-23b6-3211-a99e-cef65d08d9ca&api_key=4b93d65d-6597-3b18-8c64-004b39c0e5b9'
   feed = feedparser.parse(feed_url)
   print("------------",feed.entries[0].description)
   return render_template('feed.html',entries=feed.entries)

@app.route('/time', methods=['GET', 'POST'])
def get_Time():
    print("------Estas en la funcion de la hora---------")
    hora = None
    if 'username' in session:
      print("-------La sesion es: ",session)
      if request.method == 'GET':
        username = session['username']
        hora = datetime.now().strftime('%H:%M:%S')
      return render_template('homepageRegistered.html', hora=hora,username=username)
    return render_template('homepage2.html', hora=hora)

@app.route('/externMean', methods=['GET'])
def extern_mean():
  api_key = '7fc35707-ca78-34f7-9882-9673c9e4357e'
  compId = "valor oro"     
  streamId  = "gold"
  urlBase = "https://grovestreams.com/api/"
  response = requests.get(urlBase + "comp/" + compId + "/stream/" + streamId + "/cycle/year/stat/avg/last_value?api_key=" + api_key)
  json = response.json()
  media = "{:.2f}".format(float(str(json[0]["data"])))
  username = session['username']
  return render_template('homepageRegistered.html',ext_media=media,username=username)

@app.route('/mean', methods=['GET'])
def get_Average():
  if request.method == 'GET':
    media = 0
    sum = 0
    total = 0
    body = {"query": {"match_all": {}},"size": 1000}
    response = es.search(index='gold_values',body=body)
    for hit in response['hits']['hits']:
      gold = hit['_source']['gold']
      sum += float(gold)
      total += 1
    media = "{:.2f}".format(sum/total)
    username = session['username']
    return render_template('homepageRegistered.html', media=media, username=username)
  
@app.route('/access',methods=["POST"])
def access():
  email = request.form['email']
  password = request.form['pass']
  password = password.encode('utf-8')
  search_query = {"query": {"term": {"email.keyword": email}}}
  result = es.search(index="users", body=search_query)
  if result['hits']['total']['value'] == 0:
      return render_template('unsuccess.html')

  user = result['hits']['hits'][0]['_source']
  if bcrypt.checkpw(password, user['password'].encode('utf-8')):

    session['username'] = user['username']
    session['email']=request.form['email']
    return render_template('success3.html')
  else:
    return render_template('unsuccess.html')

@app.route('/success',methods = ["POST"])   
def success(): 
  email = request.form['email']
  response = es.count(index='users',body={"query":{"match":{"email.keyword":str(email)}}})['count']
  if response >= 1:
    return render_template('unsuccess.html')
  else:
    session['email']=request.form['email']
    session['username']=request.form['username']

    username = request.form['username']
    password = request.form['pass']
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'),salt)
    doc = {'email':email,'username':username,'password':hashed_password.decode('utf-8')}
    es.index(index='users',document=doc)
    return render_template('success3.html')

@app.route('/logout')  
def logout(): 
  if 'email' or 'username' in session:  
    session.pop('email',None)  
    session.pop('username',None)
    return render_template('logoutpage2.html');  
  else:  
    return '<p>user already logged out</p>'   
  
@app.route('/profile')  
def profile():  
		if 'email' in session:  
			email = session['email']  
			print("--------El email es: ",email)
			user_name = es.search(index='users',body={"query":{"match":{"email":str(email)}}})
			if user_name['hits']['total']['value'] > 0:
				documento=user_name['hits']['hits'][0]['_source']
				return render_template('profile.html',name=email,usuario=documento['username'])
			else:
				user_name = "Not found"
				return render_template('profile.html',name=email,usuario=user_name)
		else:  
			return '<p>Please login first</p><br><a href = "/">Volver a la pantalla principal</a><br>'  

def show_gold():
  while True:
    media = 0
    sum = 0
    total = 0
    body = {"query": {"match_all": {}},"size": 1000}
    response = es.search(index='oro',body=body)
    for hit in response['hits']['hits']:
      gold = hit['_source']['gold_val']
      sum += float(gold)
      total += 1
    media = "{:.2f}".format(sum/total)
    print("La media es: ",media)
    time.sleep(120)

def save_gold_local():
  op = webdriver.ChromeOptions()
  op.add_argument('headless')
  driver = webdriver.Chrome(options=op)
  url = 'https://es.investing.com/commodities/gold' 
  while True:
    driver.get(url)
    valores = driver.find_elements(By.XPATH, '//div/div/div/div/div/div/div/div/div')
    val = valores[13].text
    now = datetime.now().strftime('%H:%M')
    gold = val[:9]
    goldNew = str(gold).replace(".", "").replace(",", ".")
    gold = float(goldNew)
    doc = {'gold':gold,'time':now}
    es.index(index='gold_values',document=doc)
    time.sleep(120)


if __name__ == "__main__":
  t1 = threading.Thread(target=save_gold_local)
  t1.start()
  app.run(host='0.0.0.0', port=5000)