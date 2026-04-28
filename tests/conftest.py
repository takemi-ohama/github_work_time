import pytest
from app import create_app, db as _db
from app.models import User, Project, WorkEntry
from datetime import date


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()
        _db.create_all()


@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()


@pytest.fixture(scope='function')
def test_user(db):
    user = User(
        github_login='testuser',
        name='テストユーザー',
        email='test@example.com',
        avatar_url='https://example.com/avatar.png'
    )
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope='function')
def test_project(db, test_user):
    project = Project(
        name='テストプロジェクト',
        description='テスト用プロジェクト',
        user_id=test_user.id
    )
    _db.session.add(project)
    _db.session.commit()
    return project


@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return client
