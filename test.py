import pytest
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from app import app
import bcrypt


@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Use a different database for testing
    app.config['MONGO_URI'] = (
        'mongodb+srv://rtheman2305:Ef*tobe1@cluster0.xjjezs2.mongodb.net/'
        '?retryWrites=true&w=majority'
    )
    app.config['MONGO_DB'] = 'test_mytodo'
    app.config['SECRET_KEY'] = '0137d8c2665fd7b7e7b32f777a3e601e'
    client = app.test_client()
    email = 'test1@example.com'
    password = 'testpass'

    client.post(
        '/register',
        data={
            'email': email,
            'password': password},
        follow_redirects=True)
    yield client


def test_register(client):
    email = 'test2@example.com'
    password = 'testpass'
    mongo = MongoClient(
        app.config['MONGO_URI'],
        server_api=ServerApi('1'))[
        app.config['MONGO_DB']]

    client.post(
        '/register',
        data={
            'email': email,
            'password': password},
        follow_redirects=True)
    user = mongo.users.find_one({'username': email})

    # Assert that the user exists
    assert user is not None

    # Check that the password matches the stored hashed password
    hashed_pw_from_db = user['password']
    assert bcrypt.checkpw(password.encode('utf-8'), hashed_pw_from_db)

    count = mongo.users.count_documents({})
    client.post(
        '/register',
        data={
            'email': email,
            'password': password},
        follow_redirects=True)
    assert count is mongo.users.count_documents({})
    mongo.users.delete_one({'username': email})


def test_login(client):
    email = 'test1@example.com'
    wrong_password = 'wrongpass'
    wrong_email = 'wrongemail@gmail.com'
    client.post(
        '/login',
        data={
            'email': email,
            'password': wrong_password},
        follow_redirects=True)
    with client.session_transaction() as session:
        assert 'email' not in session
    right_password = 'testpass'
    client.post(
        '/login',
        data={
            'email': wrong_email,
            'password': right_password},
        follow_redirects=True)
    with client.session_transaction() as session:
        assert 'email' not in session
    client.post(
        '/login',
        data={
            'email': email,
            'password': right_password},
        follow_redirects=True)
    with client.session_transaction() as session:
        assert 'email' in session
