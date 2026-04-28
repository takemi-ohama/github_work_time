import pytest
from datetime import date, datetime
from app.models import User, Project, WorkEntry
from app import db as _db


class TestUserModel:
    def test_create_user(self, db, test_user):
        assert test_user.id is not None
        assert test_user.github_login == 'testuser'
        assert test_user.name == 'テストユーザー'
        assert test_user.email == 'test@example.com'

    def test_user_repr(self, db, test_user):
        assert 'testuser' in repr(test_user)

    def test_user_created_at(self, db, test_user):
        assert test_user.created_at is not None
        assert isinstance(test_user.created_at, datetime)

    def test_unique_github_login(self, db, test_user):
        duplicate = User(github_login='testuser', name='Duplicate')
        _db.session.add(duplicate)
        with pytest.raises(Exception):
            _db.session.commit()
        _db.session.rollback()


class TestProjectModel:
    def test_create_project(self, db, test_project):
        assert test_project.id is not None
        assert test_project.name == 'テストプロジェクト'
        assert test_project.description == 'テスト用プロジェクト'

    def test_project_user_relationship(self, db, test_project, test_user):
        assert test_project.user_id == test_user.id
        assert test_project.owner.github_login == 'testuser'

    def test_project_repr(self, db, test_project):
        assert 'テストプロジェクト' in repr(test_project)


class TestWorkEntryModel:
    def test_create_work_entry(self, db, test_user, test_project):
        entry = WorkEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            title='テスト作業',
            description='テストの詳細',
            hours=2.5,
            work_date=date(2024, 1, 15)
        )
        _db.session.add(entry)
        _db.session.commit()

        assert entry.id is not None
        assert entry.title == 'テスト作業'
        assert entry.hours == 2.5
        assert entry.work_date == date(2024, 1, 15)

    def test_work_entry_relationships(self, db, test_user, test_project):
        entry = WorkEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            title='リレーションテスト',
            hours=1.0,
            work_date=date.today()
        )
        _db.session.add(entry)
        _db.session.commit()

        assert entry.user.github_login == 'testuser'
        assert entry.project.name == 'テストプロジェクト'

    def test_work_entry_repr(self, db, test_user):
        entry = WorkEntry(
            user_id=test_user.id,
            title='repr テスト',
            hours=1.0,
            work_date=date(2024, 1, 1)
        )
        _db.session.add(entry)
        _db.session.commit()
        assert 'repr テスト' in repr(entry)

    def test_work_entry_without_project(self, db, test_user):
        entry = WorkEntry(
            user_id=test_user.id,
            title='プロジェクトなし',
            hours=0.5,
            work_date=date.today()
        )
        _db.session.add(entry)
        _db.session.commit()
        assert entry.project_id is None
        assert entry.project is None

    def test_cascade_delete_user(self, db):
        user = User(github_login='delete_test_user', name='Delete Test')
        _db.session.add(user)
        _db.session.commit()

        project = Project(name='削除テストプロジェクト', user_id=user.id)
        _db.session.add(project)
        _db.session.commit()

        entry = WorkEntry(
            user_id=user.id,
            project_id=project.id,
            title='削除テスト',
            hours=1.0,
            work_date=date.today()
        )
        _db.session.add(entry)
        _db.session.commit()

        entry_id = entry.id
        _db.session.delete(user)
        _db.session.commit()

        assert _db.session.get(WorkEntry, entry_id) is None
