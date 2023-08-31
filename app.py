# This section imports the necessary modules, sets up the Flask
# app, and initializes a connection to MongoDB using Flask-PyMongo.
import bcrypt
from flask import Flask, render_template, request, redirect, \
    url_for, jsonify, session, flash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from config import Config
from pymongo.errors import PyMongoError
import logging
from logging.handlers import RotatingFileHandler
from models import (
    get_user_by_email,
    add_user,
    get_all_todos_by_email,
    add_todo_for_email,
    get_todo_by_id,
    add_subtask_to_todo,
    update_todo_status,
    update_subtask_status)

app = Flask(__name__)
mongo = None


# This function checks if a user is logged in by checking
# if the 'email' key exists in the session.
def is_logged_in():
    return 'email' in session


# This route handler defines the root URL and returns
# a simple welcome message.
@app.route('/')
def index():
    return "Welcome to Todo!"


# This route handles user registration. It checks if
# the email is already registered, hashes the password,
# and inserts the user into the database.
@app.route('/register', methods=['POST'])
def register():

    db = MongoClient(
        app.config['MONGO_URI'],
        server_api=ServerApi('1'))[
        app.config['MONGO_DB']]
    try:
        existing_user = get_user_by_email(request.form['email'], db)

        if existing_user:
            app.logger.info('Email already registered!')
            flash('Email already registered!', 'warning')
        else:
            add_user(request.form['email'], request.form['password'], db)
            app.logger.info('Registration completed!')
            flash('Registration completed!', 'success')
    except PyMongoError:
        app.logger.error(
            'Database error occurred during registration!',
            exc_info=True)
        flash('Database error occurred!', 'danger')

    return redirect(url_for('login'))


# This route handles the login process. It checks if
# the user's credentials are correct, logs them in,
# and redirects them to the home page.
@app.route('/login', methods=['GET', 'POST'])
def login():
    db = MongoClient(
        app.config['MONGO_URI'],
        server_api=ServerApi('1'))[
        app.config['MONGO_DB']]
    if request.method == 'POST':
        try:
            email = request.form['email']
            login_user = get_user_by_email(email, db)
            if login_user:
                if bcrypt.hashpw(
                        request.form['password'].encode('utf-8'),
                        login_user['password']) == login_user['password']:
                    session['email'] = email
                    app.logger.info(f'User {email} logged in!')
                    return redirect(url_for('home'))
                else:
                    app.logger.info('Incorrect password!')
                    flash('Incorrect password!', 'danger')
                    return redirect(url_for('login'))
            else:
                app.logger.info('Incorrect email!')
                flash('Incorrect email!', 'warning')
                return redirect(url_for('login'))
        except PyMongoError:
            app.logger.error(
                'Database error occurred during login!',
                exc_info=True)
            flash('Database error occurred!', 'danger')

    return render_template('login.html')


# This route handles the user's home page. It fetches
# pending TODOs from the database and renders them on the page.
@app.route('/home', methods=['GET'])
def home():
    todos = []
    db = MongoClient(
        app.config['MONGO_URI'],
        server_api=ServerApi('1'))[
        app.config['MONGO_DB']]
    try:
        if not is_logged_in():
            # Redirect to login page if user is not logged in
            return redirect(url_for('login'))
        # Fetch pending TODOs from the database
        todos = get_all_todos_by_email(session.get('email'), db)
    except PyMongoError:
        app.logger.error(
            'Database error occurred while accessing home page!',
            exc_info=True)
        flash('Database error occurred!', 'danger')
    # Render them on the home page
    return render_template('home.html', todos=todos)


# This route adds a new to-do to the database based
# on user input.
@app.route('/add_todo', methods=['POST'])
def add_todo():
    db = MongoClient(
        app.config['MONGO_URI'],
        server_api=ServerApi('1'))[
        app.config['MONGO_DB']]
    try:
        # Get data from the frontend
        todo_text = request.form.get('text')

        # Check if the user is logged in
        if 'email' not in session:
            return jsonify(status="error", message="User not logged in")

        if 'email' not in session:
            return redirect(url_for('login'))

        user_email = session['email']  # Get user email from session

        # Check if the required data (text of the to-do) is present
        if not todo_text:
            return jsonify(status="error", message="Missing text")

        add_todo_for_email(user_email, todo_text, db)
        app.logger.info(f'Todo added for user {user_email}!')
    except PyMongoError:
        app.logger.error(
            'Database error occurred while adding Todo!',
            exc_info=True)
        flash('Database error occurred!', 'danger')

    return redirect(url_for('home'))


# This route handles user logout by clearing the
# session and redirecting to the login page.
@app.route('/logout')
def logout():
    # Clear the session data to log the user out
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    session.clear()
    app.logger.info(f'User {email} logged out!')
    # Redirect to the login page after logging out
    return redirect(url_for('login'))


# This route adds a subtask to an existing
# to-do based on user input.
@app.route('/add_subtask', methods=['POST'])
def add_subtask():
    db = MongoClient(
        app.config['MONGO_URI'],
        server_api=ServerApi('1'))[
        app.config['MONGO_DB']]
    try:
        # Retrieving the task_id and subtask_name from the form data
        task_id = request.form.get('task_id')
        # Getting the text of the new subtask from the request data
        subtask_name = request.form.get('subtask_name')

        # Finding the task using the task_id
        task = get_todo_by_id(ObjectId(task_id), db)

        # Check if the task exists
        if not task:
            return redirect(url_for('home'))

        # Add subtask to to-do
        add_subtask_to_todo(ObjectId(task_id), subtask_name, db)
        app.logger.info(f'Subtask added for task {task_id}!')

    except PyMongoError:
        app.logger.error(
            'Database error occurred while adding subtask!',
            exc_info=True)
        flash('Database error occurred!', 'danger')
    return redirect(url_for('home'))


# This route updates the status of a to-do
# item based on user input.
@app.route('/update_task', methods=['POST'])
def update_task():
    db = MongoClient(
        app.config['MONGO_URI'],
        server_api=ServerApi('1'))[
        app.config['MONGO_DB']]
    try:
        task_id = request.form.get('task_id')
        task_status = True if 'task_status' in request.form else False
        update_todo_status(task_id, task_status, db)
        app.logger.info(
            f'Todo status updated for task {task_id} to {task_status}!')
    except PyMongoError:
        app.logger.error(
            'Database error occurred while updating task!',
            exc_info=True)
        flash('Database error occurred!', 'danger')
    return redirect(url_for('home'))


# This route updates the status of a subtask within a
# to-do item based on user input.
@app.route('/update_subtask', methods=['POST'])
def update_subtask():
    db = MongoClient(
        app.config['MONGO_URI'],
        server_api=ServerApi('1'))[
        app.config['MONGO_DB']]
    try:
        subtask_id = request.form.get('subtask_id')
        task_status = True if 'subtask_status' in request.form else False
        update_subtask_status(subtask_id, task_status, db)
        app.logger.info(
            f'Todo status updated for task {subtask_id} to {task_status}!')
    except PyMongoError:
        app.logger.error(
            'Database error occurred while updating subtask!',
            exc_info=True)
        flash('Database error occurred!', 'danger')
    return redirect(url_for('home'))


if __name__ == '__main__':
    handler = RotatingFileHandler('todo.log', maxBytes=10000, backupCount=3)
    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler.setLevel(logging.INFO)
    app.logger.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.config.from_object(Config)
    app.run(debug=True)
