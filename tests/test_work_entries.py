import pytest
from datetime import date
from app.models import WorkEntry, Project
from app import db as _db


class TestWorkEntriesList:
    def test_list_requires_login(self, client):
        response = client.get('/work_entries/')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_list_entries_empty(self, logged_in_client):
        response = logged_in_client.get('/work_entries/')
        assert response.status_code == 200
        assert '日報一覧' in response.data.decode('utf-8')

    def test_list_entries_with_data(self, logged_in_client, db, test_user, test_project):
        entry = WorkEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            title='テスト作業タイトル',
            hours=2.0,
            work_date=date(2024, 1, 15)
        )
        _db.session.add(entry)
        _db.session.commit()

        response = logged_in_client.get('/work_entries/')
        assert response.status_code == 200
        assert 'テスト作業タイトル' in response.data.decode('utf-8')

    def test_list_filter_by_date(self, logged_in_client, db, test_user):
        entry = WorkEntry(
            user_id=test_user.id,
            title='フィルタテスト',
            hours=1.0,
            work_date=date(2024, 3, 15)
        )
        _db.session.add(entry)
        _db.session.commit()

        response = logged_in_client.get('/work_entries/?start_date=2024-03-01&end_date=2024-03-31')
        assert response.status_code == 200
        assert 'フィルタテスト' in response.data.decode('utf-8')

        response = logged_in_client.get('/work_entries/?start_date=2024-04-01&end_date=2024-04-30')
        assert response.status_code == 200
        assert 'フィルタテスト' not in response.data.decode('utf-8')


class TestWorkEntriesNew:
    def test_new_entry_form(self, logged_in_client):
        response = logged_in_client.get('/work_entries/new')
        assert response.status_code == 200
        assert '工数登録' in response.data.decode('utf-8')

    def test_new_entry_requires_login(self, client):
        response = client.get('/work_entries/new')
        assert response.status_code == 302


class TestWorkEntriesCreate:
    def test_create_entry(self, logged_in_client, db, test_user):
        response = logged_in_client.post('/work_entries/', data={
            'title': '新規作業',
            'description': '詳細説明',
            'hours': '2.5',
            'work_date': '2024-01-20',
            'project_name': '新規プロジェクト'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert '工数を登録しました' in response.data.decode('utf-8')

        entry = WorkEntry.query.filter_by(user_id=test_user.id, title='新規作業').first()
        assert entry is not None
        assert entry.hours == 2.5
        assert entry.work_date == date(2024, 1, 20)

    def test_create_entry_without_title(self, logged_in_client):
        response = logged_in_client.post('/work_entries/', data={
            'title': '',
            'hours': '1.0',
            'work_date': '2024-01-20'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert 'タイトルは必須' in response.data.decode('utf-8')

    def test_create_entry_invalid_hours(self, logged_in_client):
        response = logged_in_client.post('/work_entries/', data={
            'title': 'テスト',
            'hours': 'invalid',
            'work_date': '2024-01-20'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert '工数は0以上' in response.data.decode('utf-8')

    def test_create_entry_with_existing_project(self, logged_in_client, db, test_user, test_project):
        response = logged_in_client.post('/work_entries/', data={
            'title': '既存プロジェクト作業',
            'hours': '1.0',
            'work_date': '2024-01-20',
            'project_id': str(test_project.id)
        }, follow_redirects=True)

        assert response.status_code == 200
        entry = WorkEntry.query.filter_by(title='既存プロジェクト作業').first()
        assert entry is not None
        assert entry.project_id == test_project.id


class TestWorkEntriesEdit:
    def test_edit_entry_form(self, logged_in_client, db, test_user):
        entry = WorkEntry(
            user_id=test_user.id,
            title='編集前タイトル',
            hours=1.0,
            work_date=date(2024, 1, 15)
        )
        _db.session.add(entry)
        _db.session.commit()

        response = logged_in_client.get(f'/work_entries/{entry.id}/edit')
        assert response.status_code == 200
        assert '編集前タイトル' in response.data.decode('utf-8')

    def test_update_entry(self, logged_in_client, db, test_user):
        entry = WorkEntry(
            user_id=test_user.id,
            title='更新前',
            hours=1.0,
            work_date=date(2024, 1, 15)
        )
        _db.session.add(entry)
        _db.session.commit()

        response = logged_in_client.post(f'/work_entries/{entry.id}', data={
            '_method': 'PUT',
            'title': '更新後',
            'hours': '3.0',
            'work_date': '2024-02-01'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert '工数を更新しました' in response.data.decode('utf-8')

        _db.session.refresh(entry)
        assert entry.title == '更新後'
        assert entry.hours == 3.0

    def test_edit_other_users_entry(self, logged_in_client, db):
        from app.models import User
        other_user_entry_user = User(
            github_login='otheruser2',
            name='Other User'
        )
        _db.session.add(other_user_entry_user)
        _db.session.commit()

        other_entry = WorkEntry(
            user_id=other_user_entry_user.id,
            title='他人の作業',
            hours=1.0,
            work_date=date.today()
        )
        _db.session.add(other_entry)
        _db.session.commit()

        response = logged_in_client.get(f'/work_entries/{other_entry.id}/edit')
        assert response.status_code == 404


class TestWorkEntriesDelete:
    def test_delete_entry(self, logged_in_client, db, test_user):
        entry = WorkEntry(
            user_id=test_user.id,
            title='削除対象',
            hours=1.0,
            work_date=date.today()
        )
        _db.session.add(entry)
        _db.session.commit()
        entry_id = entry.id

        response = logged_in_client.post(f'/work_entries/{entry_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        assert '工数を削除しました' in response.data.decode('utf-8')
        assert _db.session.get(WorkEntry, entry_id) is None

    def test_delete_other_users_entry(self, logged_in_client, db):
        from app.models import User
        other_user = User(
            github_login='otheruser3',
            name='Other User 3'
        )
        _db.session.add(other_user)
        _db.session.commit()

        other_entry = WorkEntry(
            user_id=other_user.id,
            title='他人の削除対象',
            hours=1.0,
            work_date=date.today()
        )
        _db.session.add(other_entry)
        _db.session.commit()

        response = logged_in_client.post(f'/work_entries/{other_entry.id}/delete')
        assert response.status_code == 404
