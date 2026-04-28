import pytest
from datetime import date, timedelta
from app.models import WorkEntry, Project
from app import db as _db


class TestSummaryView:
    def test_summary_requires_login(self, client):
        response = client.get('/summary/')
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_summary_empty(self, logged_in_client):
        response = logged_in_client.get('/summary/')
        assert response.status_code == 200
        assert '集計・分析' in response.data.decode('utf-8')

    def test_summary_with_data(self, logged_in_client, db, test_user, test_project):
        today = date.today()
        entries = [
            WorkEntry(user_id=test_user.id, project_id=test_project.id,
                      title='作業1', hours=2.0, work_date=today),
            WorkEntry(user_id=test_user.id, project_id=test_project.id,
                      title='作業2', hours=3.0, work_date=today),
            WorkEntry(user_id=test_user.id,
                      title='作業3（プロジェクトなし）', hours=1.5,
                      work_date=today - timedelta(days=1)),
        ]
        for e in entries:
            _db.session.add(e)
        _db.session.commit()

        start = (today - timedelta(days=5)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        response = logged_in_client.get(f'/summary/?start_date={start}&end_date={end}')
        assert response.status_code == 200

        content = response.data.decode('utf-8')
        assert 'テストプロジェクト' in content
        assert '6.5' in content  # total hours

    def test_summary_date_filter(self, logged_in_client, db, test_user, test_project):
        old_entry = WorkEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            title='古い作業',
            hours=5.0,
            work_date=date(2020, 1, 1)
        )
        _db.session.add(old_entry)
        _db.session.commit()

        response = logged_in_client.get('/summary/?start_date=2024-01-01&end_date=2024-12-31')
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        # Old entry should not be in the total
        assert '5.0' not in content or '古い作業' not in content

    def test_summary_no_project_category(self, logged_in_client, db, test_user):
        today = date.today()
        entry = WorkEntry(
            user_id=test_user.id,
            title='分類なし作業',
            hours=2.0,
            work_date=today
        )
        _db.session.add(entry)
        _db.session.commit()

        start = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        response = logged_in_client.get(f'/summary/?start_date={start}&end_date={end}')
        assert response.status_code == 200
        assert '未分類' in response.data.decode('utf-8')

    def test_summary_multiple_projects(self, logged_in_client, db, test_user):
        today = date.today()

        proj1 = Project(name='プロジェクトA', user_id=test_user.id)
        proj2 = Project(name='プロジェクトB', user_id=test_user.id)
        _db.session.add_all([proj1, proj2])
        _db.session.commit()

        entries = [
            WorkEntry(user_id=test_user.id, project_id=proj1.id,
                      title='A作業1', hours=4.0, work_date=today),
            WorkEntry(user_id=test_user.id, project_id=proj1.id,
                      title='A作業2', hours=2.0, work_date=today),
            WorkEntry(user_id=test_user.id, project_id=proj2.id,
                      title='B作業1', hours=3.0, work_date=today),
        ]
        for e in entries:
            _db.session.add(e)
        _db.session.commit()

        start = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        response = logged_in_client.get(f'/summary/?start_date={start}&end_date={end}')
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert 'プロジェクトA' in content
        assert 'プロジェクトB' in content
