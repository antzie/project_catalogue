#!/usr/bin/env python2
# Catalogue Project

from flask import (Flask, render_template,
                   request, redirect, url_for, jsonify, flash)

# Database modules + database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool
from v2_db_setup import Base, FoodCategory, FoodItem

# User session modules
import random
import string
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Database Connection and Session
engine = create_engine('sqlite:///grocer.db?check_same_thread=False',
                       poolclass=SingletonThreadPool)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Client Info and Application Name.
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Grocer Catalogue"


#######################################################################
# Log-in/User Authorisation Section


# Create anti-forgery state token
@app.route('/login')
def log_in():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)

# Connect to Google and provide access token


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

        # check 'access_token is not already stored in login_session

        # Fixes issue where login_session'access_token' was
        # not being overwritten with a new acces_token
        # from credentials.access_token.

        if 'access_token' in login_session:
            del login_session['access_token']

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h4>Welcome, '
    output += login_session['username']
    output += '!</h4>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px; height: 150px;border-radius: 150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    return output


######
# Logout.

# Revoke current user's acess token and delete their login_session
@app.route('/gdisconnect', methods=['GET', 'POST'])
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = (
        'https://accounts.google.com/o/oauth2/revoke?token=%s' %
        access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    # Sucessful revocation of access token:
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('mainPage'))
    # Unsucessful revocation of access token.
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


#######################

# JSON API Endpoints

# Categories
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(FoodCategory).order_by('name').all()
    return jsonify(categories=[category.serialize for category in categories])


# Items within Category
@app.route('/category/<int:category_id>/JSON')
def categoryItemsJSON(category_id):
    food = session.query(FoodItem).filter_by(foodcategory_id=category_id).all()
    return jsonify(food=[fooditem.serialize for fooditem in food])

# Individual Item within Category


@app.route('/category/<int:category_id>/<int:food_id>/JSON')
def foodItemJSON(category_id, food_id):
    foodItem = session.query(FoodItem).filter_by(id=food_id).one()
    return jsonify(foodItem=foodItem.serialize)


#############################################################

# Website Framework and Endpoints

# About page.
@app.route('/about/')
def about():
    return render_template('about.html')


# Food Category

@app.route('/')
@app.route('/main_page/')
def mainPage():
    categories = session.query(FoodCategory).order_by('name').all()

    # Check to see if user is logged in
    if 'username' not in login_session:
        return render_template('main_page_public.html', categories=categories)

    categories = session.query(FoodCategory).order_by('name').all()
    return render_template('main_page.html', categories=categories)


# New Food Category

@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect(url_for('log_in'))

    # other categories is passed into template grocer_header.html
    other_categories = session.query(FoodCategory).all()
    if request.method == 'POST':
        new_category = FoodCategory(name=request.form['Category_Name'])
        session.add(new_category)
        session.commit()
        flash("New category: " + new_category.name + " added")
        return redirect(url_for('mainPage'))
    return render_template(
        'category_new.html',
        other_categories=other_categories)


# Edit Food Category

@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect(url_for('log_in'))

    edited_category = session.query(
        FoodCategory).filter_by(id=category_id).one()

    # Categories not being adjusted
    other_categories = session.query(FoodCategory).filter(
        FoodCategory.id != category_id).all()

    # Change category
    if request.method == 'POST':
        request.form['Category_Name']
        edited_category.name = request.form['Category_Name']
        session.add(edited_category)
        session.commit()
        flash(edited_category.name + " changed!")
        return redirect(url_for('mainPage'))

    # Do not change category
    return render_template(
        'category_edit.html',
        category_id=category_id,
        edited_category=edited_category,
        other_categories=other_categories)


# Delete Category

@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect(url_for('log_in'))

    deleted_category = session.query(
        FoodCategory).filter_by(id=category_id).one()
    other_categories = session.query(FoodCategory).filter(
        FoodCategory.id != category_id).all()

    if request.method == 'POST':
        session.delete(deleted_category)
        session.commit()
        flash(deleted_category.name + " deleted!")
        return redirect(url_for('mainPage'))

    return render_template(
        'category_delete.html',
        category_id=category_id,
        category=deleted_category,
        other_categories=other_categories)


#######################
# FoodItems Section

# Show Food for a specific category

@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/food/')
def showCategoryFood(category_id):
    category = session.query(FoodCategory).filter_by(id=category_id).one()
    other_categories = session.query(FoodCategory).filter(
        FoodCategory.id != category_id).all()
    food = session.query(FoodItem).filter_by(foodcategory_id=category_id).all()

    if 'username' not in login_session:
        return render_template('food_public.html',
                               category=category,
                               category_id=category_id,
                               food=food,
                               other_categories=other_categories)

    return render_template('food.html',
                           category=category,
                           category_id=category_id,
                           food=food,
                           other_categories=other_categories)


# New Food

@app.route('/category/<int:category_id>/food/new/', methods=['GET', 'POST'])
def newFoodItem(category_id):
    if 'username' not in login_session:
        return redirect(url_for('log_in'))

    category = session.query(FoodCategory).filter_by(id=category_id).one()
    other_categories = session.query(FoodCategory).filter(
        FoodCategory.id != category_id).all()

    if request.method == 'POST':
        newFood = FoodItem(
            name=request.form['Name'], description=request.form['Description'],
            price=request.form['Price'], foodcategory_id=category_id)
        session.add(newFood)
        session.commit()
        flash("New item" + newFood.name + " created!")
        return redirect(url_for('showCategoryFood',
                                category_id=category_id))

    return render_template(
        'food_new.html',
        category=category,
        category_id=category_id,
        other_categories=other_categories)


# Edit Food

@app.route('/category/<int:category_id>/food/<int:food_id>/edit/',
           methods=['GET', 'POST'])
def editFoodItem(category_id, food_id):
    if 'username' not in login_session:
        return redirect(url_for('log_in'))

    edited_food = session.query(FoodItem).filter_by(id=food_id).one()
    other_categories = session.query(FoodCategory).filter(
        FoodCategory.id != category_id).all()

    if request.method == 'POST':
        if request.form['name']:
            edited_food.name = request.form['name']
        if request.form['description']:
            edited_food.description = request.form['description']
        if request.form['price']:
            edited_food.price = request.form['price']
        session.add(edited_food)
        session.commit()
        flash("Food item: " + edited_food.name + " edited!")
        return redirect(url_for('showCategoryFood', category_id=category_id))

    return render_template(
        'food_edit.html',
        edited_food=edited_food,
        category_id=category_id,
        other_categories=other_categories)


# Delete Food

@app.route('/category/<int:category_id>/food/<int:food_id>/delete/',
           methods=['GET', 'POST'])
def deleteFoodItem(category_id, food_id):
    if 'username' not in login_session:
        return redirect(url_for('log_in'))

    deleted_food = session.query(FoodItem).filter_by(id=food_id).one()
    other_categories = session.query(FoodCategory).filter(
        FoodCategory.id != category_id).all()

    if request.method == 'POST':
        session.delete(deleted_food)
        session.commit()
        flash("Food item: " + deleted_food.name + " deleted!")
        return redirect(
            url_for(
                'showCategoryFood',
                category_id=deleted_food.foodcategory_id))

    return render_template('food_delete.html', deleted_food=deleted_food)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
