from datetime import date, datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import WorkEntry, Project

work_entries_bp = Blueprint('work_entries', __name__, url_prefix='/work_entries')


def get_or_create_project(name, user_id):
    """Get or create a project by name for the current user."""
    project = Project.query.filter_by(name=name, user_id=user_id).first()
    if not project:
        project = Project(name=name, user_id=user_id)
        db.session.add(project)
        db.session.flush()
    return project


@work_entries_bp.route('/')
@login_required
def list_entries():
    # Filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    project_id = request.args.get('project_id', type=int)

    query = WorkEntry.query.filter_by(user_id=current_user.id)

    if start_date:
        try:
            query = query.filter(WorkEntry.work_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        except ValueError:
            pass

    if end_date:
        try:
            query = query.filter(WorkEntry.work_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        except ValueError:
            pass

    if project_id:
        query = query.filter_by(project_id=project_id)

    entries = query.order_by(WorkEntry.work_date.desc(), WorkEntry.created_at.desc()).all()

    # Group by date
    entries_by_date = {}
    for entry in entries:
        d = entry.work_date
        if d not in entries_by_date:
            entries_by_date[d] = {'entries': [], 'total_hours': 0.0}
        entries_by_date[d]['entries'].append(entry)
        entries_by_date[d]['total_hours'] += entry.hours

    # Sort by date desc
    entries_by_date = dict(sorted(entries_by_date.items(), reverse=True))

    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.name).all()

    return render_template(
        'work_entries/list.html',
        entries_by_date=entries_by_date,
        projects=projects,
        start_date=start_date or '',
        end_date=end_date or '',
        selected_project_id=project_id,
        total_hours=sum(e.hours for e in entries)
    )


@work_entries_bp.route('/new')
@login_required
def new_entry():
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.name).all()
    today = date.today().strftime('%Y-%m-%d')
    return render_template('work_entries/form.html', entry=None, projects=projects, today=today)


@work_entries_bp.route('/', methods=['POST'])
@login_required
def create_entry():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    hours_str = request.form.get('hours', '0')
    work_date_str = request.form.get('work_date', '')
    project_name = request.form.get('project_name', '').strip()
    project_id = request.form.get('project_id', type=int)

    if not title:
        flash('タイトルは必須です。', 'danger')
        return redirect(url_for('work_entries.new_entry'))

    try:
        hours = float(hours_str)
        if hours < 0:
            raise ValueError
    except ValueError:
        flash('工数は0以上の数値を入力してください。', 'danger')
        return redirect(url_for('work_entries.new_entry'))

    try:
        work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('作業日の形式が正しくありません。', 'danger')
        return redirect(url_for('work_entries.new_entry'))

    # Handle project
    if project_name and not project_id:
        project = get_or_create_project(project_name, current_user.id)
        project_id = project.id
    elif project_id:
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
        if not project:
            project_id = None

    entry = WorkEntry(
        user_id=current_user.id,
        project_id=project_id,
        title=title,
        description=description,
        hours=hours,
        work_date=work_date,
    )
    db.session.add(entry)
    db.session.commit()
    flash('工数を登録しました。', 'success')
    return redirect(url_for('work_entries.list_entries'))


@work_entries_bp.route('/<int:entry_id>/edit')
@login_required
def edit_entry(entry_id):
    entry = WorkEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.name).all()
    return render_template('work_entries/form.html', entry=entry, projects=projects, today=None)


@work_entries_bp.route('/<int:entry_id>', methods=['POST'])
@login_required
def update_entry(entry_id):
    # Support method override
    method = request.form.get('_method', '').upper()
    if method == 'DELETE':
        return delete_entry(entry_id)

    entry = WorkEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    hours_str = request.form.get('hours', '0')
    work_date_str = request.form.get('work_date', '')
    project_name = request.form.get('project_name', '').strip()
    project_id = request.form.get('project_id', type=int)

    if not title:
        flash('タイトルは必須です。', 'danger')
        return redirect(url_for('work_entries.edit_entry', entry_id=entry_id))

    try:
        hours = float(hours_str)
        if hours < 0:
            raise ValueError
    except ValueError:
        flash('工数は0以上の数値を入力してください。', 'danger')
        return redirect(url_for('work_entries.edit_entry', entry_id=entry_id))

    try:
        work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('作業日の形式が正しくありません。', 'danger')
        return redirect(url_for('work_entries.edit_entry', entry_id=entry_id))

    # Handle project
    if project_name and not project_id:
        project = get_or_create_project(project_name, current_user.id)
        project_id = project.id
    elif project_id:
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
        if not project:
            project_id = entry.project_id

    entry.title = title
    entry.description = description
    entry.hours = hours
    entry.work_date = work_date
    entry.project_id = project_id
    entry.updated_at = datetime.now(timezone.utc)

    db.session.commit()
    flash('工数を更新しました。', 'success')
    return redirect(url_for('work_entries.list_entries'))


@work_entries_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = WorkEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash('工数を削除しました。', 'success')
    return redirect(url_for('work_entries.list_entries'))
