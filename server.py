
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.75.150.200/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.75.150.200/proj1part2"
#
DATABASEURI = "postgresql://jp4107:5290@34.75.150.200/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  # DEBUG: this is debugging code to see what request looks like
  print(request.args)
  return render_template("index.html")


@app.route('/clogin',methods=['GET','POST'])
def clogin():
  if request.method == 'GET':
    return render_template('clogin.html')
  user_id=request.form.get('user id')
  cursor = g.conn.execute("SELECT user_id FROM customers")
  indicate=0
  for i in cursor:
    if i['user_id']==user_id:
      indicate=1
      break
  cursor.close()
  if indicate==1:
    return redirect(url_for('user_info', user_id=user_id))
  else:
    return render_template('clogin.html', **{'msg': 'user id doesn\'t exist!'})

@app.route('/blogin',methods=['GET','POST'])
def blogin():
  if request.method == 'GET':
    return render_template('blogin.html')
  business_id=request.form.get('business id')
  cursor = g.conn.execute("SELECT business_id FROM business")
  indicate=0
  for i in cursor:
    if i['business_id']==business_id:
      indicate=1
      break
  cursor.close()
  if indicate==1:
    return redirect(url_for('busi_info', business_id=business_id))
  else:
    return render_template('blogin.html',**{'msg': 'business id doesn\'t exist!'})

@app.route('/search',methods=['GET','POST'])
def search():
  if request.method == 'GET':
    return render_template('search.html')
  bname = request.form.get("business name") if request.form.get("business name") !='' else '0'
  bstars = request.form.get("star rating") if request.form.get("star rating") !='' else '0'
  city = request.form.get("city") if request.form.get("city") !='' else '0'
  state = request.form.get("state") if request.form.get("state") !='' else '0'
  if bname=='0' and bstars=='0' and city=='0' and state=='0':
    return (render_template('search.html', **{'msg':'Can\'t search without any input!'}))
  return redirect(url_for('search_busi', bname=bname, bstars = bstars, city = city, state = state))


@app.route('/search_busi/<bname>/<bstars>/<city>/<state>/')
def search_busi(bname,bstars,city,state):
  s = text("SELECT business_id, bname, address, city, state, bstars, category FROM business WHERE bname LIKE :a and bstars >= :b and city like :c and state like :d")
  value={}
  value['a']= str('%'+bname+'%') if bname != '0' else '%'
  value['b']= float(bstars) if bstars != '0' else 0
  value['c']= str('%'+city+'%') if city != '0' else '%'
  value['d']= state if state != '0' else '%'
  cursor = g.conn.execute(s, value)
  busi = []
  busi_s = []
  for i in cursor:
    busi.append(i['business_id'])
    busi.append(i['bname'])
    busi.append(i['category'])
    busi.append(i['bstars'])
    busi.append(i['address'])
    busi.append(i['city'])
    busi.append(i['state'])
    busi_s.append(busi[:])
    busi.clear()
  cursor.close()
  context = dict(data=busi_s)
  return (render_template('search_busi.html',**context))



@app.route('/orders/<user_id>/<business_id>/')
def orders(user_id, business_id):
  if user_id == "0":
    s = text("SELECT user_id, cname, order_id, odate, bname FROM customers natural join place_orders natural join orders natural join receive_orders natural join business WHERE business_id LIKE :x")
    value = {'x': business_id}
    cursor = g.conn.execute(s, value)
  else:
    s = text("SELECT user_id, cname, order_id, odate, bname FROM customers natural join place_orders natural join orders natural join receive_orders natural join business WHERE user_id LIKE :x")
    value = {'x': user_id}
    cursor = g.conn.execute(s, value)
  order=[]
  orders=[]
  for i in cursor:
    order.append(i['order_id'])
    order.append(i['odate'])
    order.append(i['user_id'])
    order.append(i['cname'])
    order.append(i['bname'])
    orders.append(order[:])
    order.clear()
  cursor.close()
  context=dict(data=orders)

  return render_template('orders.html',**context)


@app.route('/tips/<user_id>/<business_id>/')
def tips(user_id, business_id):
  if user_id == "0":
    s = text("SELECT user_id, business_id, tdate, ttext FROM  tips WHERE business_id LIKE :x")
    value = {'x': business_id}
    cursor = g.conn.execute(s, value)
  else:
    s = text("SELECT user_id, business_id, tdate, ttext FROM tips WHERE user_id LIKE :x")
    value = {'x': user_id}
    cursor = g.conn.execute(s, value)
  tips = []
  tip = []
  for i in cursor:
    tip.append(i['user_id'])
    tip.append(i['business_id'])
    tip.append(i['tdate'])
    tip.append(i['ttext'])
    tips.append(tip[:])
    tip.clear()
  cursor.close()
  context=dict(data=tips)

  return render_template('tips.html',**context)


@app.route('/covid_19/<business_id>/')
def covid_19(business_id):
  s = text("SELECT business_id, bname, grubhub, delivery_or_takeout, temporary_close FROM business WHERE business_id LIKE :x")
  value = {'x': business_id}
  cursor = g.conn.execute(s, value)
  covid = []
  for i in cursor:
    covid.append(i['business_id'])
    covid.append(i['bname'])
    covid.append(i['grubhub'])
    covid.append(i['delivery_or_takeout'])
    covid.append(i['temporary_close'])
  cursor.close()
  context = dict(data=covid)
  return render_template('covid_19.html',**context)


@app.route('/user_info/<user_id>/')
def user_info(user_id):
  user_return = text("SELECT user_id, cname, yelping_since, useful, "
                     "funny, cool FROM customers WHERE user_id LIKE :x")
  value = {'x': user_id}
  cursor = g.conn.execute(user_return, value)
  user = []
  for results in cursor:
    user.append(results["user_id"])
    user.append(results["cname"])
    user.append(results["yelping_since"])
    user.append(results["useful"])
    user.append(results["funny"])
    user.append(results["cool"])
  cursor.close()
  context = dict(data=user)
  id_info={'user_id_':user_id,'busi_id':0}
  context.update(id_info)
  return render_template('user_info.html', **context)

@app.route('/busi_info/<business_id>/')
def busi_info(business_id):
  business_return = text("SELECT business_id, bname, category, hours, bstars, "
                         "address, city, state, postal_code FROM business WHERE business_id LIKE :x")
  value = {'x': business_id}
  cursor = g.conn.execute(business_return, value)
  busi = []
  for i in cursor:
    busi.append(i["business_id"])
    busi.append(i["bname"])
    busi.append(i["category"])
    busi.append(i["hours"])
    busi.append(i["bstars"])
    busi.append(i["address"])
    busi.append(i["city"])
    busi.append(i["state"])
    busi.append(i["postal_code"])
  cursor.close()
  context = dict(data = busi)
  id_info = {'user_id_': 0, 'busi_id': business_id}
  context.update(id_info)
  return render_template('busi_info.html', **context)



@app.route('/orders_review/<order_id>/')
def orders_review(order_id):
  s = text("SELECT user_id, cname, rstars, bname, rtext FROM customers natural join review_post natural join business WHERE order_id LIKE :x")
  value = {'x': order_id}
  cursor = g.conn.execute(s, value)
  review = []
  for i in cursor:
    review.append(i['user_id'])
    review.append(i['cname'])
    review.append(i['bname'])
    review.append(i['rstars'])
    review.append(i['rtext'])
  cursor.close()
  context = dict(data=review)
  return render_template('orders_review.html',**context)





if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
