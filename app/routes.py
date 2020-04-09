from flask import render_template, redirect
from app import app
from app.forms import LoginForm
from app.core import Core

fut = ''

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    global fut
    loginForm = LoginForm()

    if loginForm.validate_on_submit():
        fut = Core('slats1999@gmail.com', '$Logan1992')
        return redirect('/landingPage')

    return render_template('login.html', title='Sign In', loginForm=loginForm)


@app.route('/landingPage')
def landingPage():
    """ renders the navigation menu (langing page) """

    # while(1):
    #     print('1')

    return render_template('landingPage.html', title='Navigation Menu')

@app.route('/bronzePackMethod')
def bronzePackMethod():
    """ renders the bronze pack menu """
    global fut

    while(True):
        resp = fut.bronzePackMethod()
        if resp == 'error':
            break
        print(resp)
    
    return redirect('/landingPage')

@app.route('/sellTradePile', methods=['GET', 'POST'])
def sellTradePile():
    print('sell trade pile')

@app.route('/sellClub', methods=['GET', 'POST'])
def sellClub():
    print('sell club')

@app.route('/snipePlayer', methods=['GET', 'POST'])
def snipePlayer():
    print('snipe player')
