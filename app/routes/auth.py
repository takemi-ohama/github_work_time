from flask import Blueprint, redirect, url_for, session, flash, render_template, current_app, request
from flask_login import login_user, logout_user, current_user
from app import db, oauth
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('work_entries.list_entries'))

    # Demo mode: if no GitHub OAuth configured, create/login as demo user
    if not current_app.config.get('GITHUB_CLIENT_ID'):
        demo_user = User.query.filter_by(github_login='demo').first()
        if not demo_user:
            demo_user = User(
                github_login='demo',
                name='デモユーザー',
                email='demo@example.com',
                avatar_url='https://github.com/identicons/demo.png'
            )
            db.session.add(demo_user)
            db.session.commit()
        login_user(demo_user)
        flash('デモモードでログインしました。', 'info')
        return redirect(url_for('work_entries.list_entries'))

    redirect_uri = url_for('auth.callback', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


@auth_bp.route('/callback')
def callback():
    if not current_app.config.get('GITHUB_CLIENT_ID'):
        return redirect(url_for('auth.login'))

    try:
        token = oauth.github.authorize_access_token()
        resp = oauth.github.get('user', token=token)
        profile = resp.json()

        user = User.query.filter_by(github_id=profile['id']).first()
        if not user:
            user = User.query.filter_by(github_login=profile['login']).first()

        if not user:
            user = User(
                github_id=profile.get('id'),
                github_login=profile.get('login'),
                name=profile.get('name') or profile.get('login'),
                email=profile.get('email'),
                avatar_url=profile.get('avatar_url'),
            )
            db.session.add(user)
        else:
            user.github_id = profile.get('id')
            user.github_login = profile.get('login')
            user.name = profile.get('name') or profile.get('login')
            user.email = profile.get('email')
            user.avatar_url = profile.get('avatar_url')

        db.session.commit()
        login_user(user)
        flash(f'ようこそ、{user.name}さん！', 'success')
        return redirect(url_for('work_entries.list_entries'))
    except Exception as e:
        flash(f'ログインに失敗しました: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('auth.login'))
