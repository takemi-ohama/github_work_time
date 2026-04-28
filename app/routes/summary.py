from datetime import date, timedelta
from collections import defaultdict
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import WorkEntry, Project

summary_bp = Blueprint('summary', __name__, url_prefix='/summary')


@summary_bp.route('/')
@login_required
def index():
    # Default: last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=29)

    start_str = request.args.get('start_date', start_date.strftime('%Y-%m-%d'))
    end_str = request.args.get('end_date', end_date.strftime('%Y-%m-%d'))

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError:
        pass

    # Hours by project
    project_data = db.session.query(
        Project.name,
        func.sum(WorkEntry.hours).label('total_hours')
    ).join(WorkEntry, WorkEntry.project_id == Project.id)\
     .filter(
        WorkEntry.user_id == current_user.id,
        WorkEntry.work_date >= start_date,
        WorkEntry.work_date <= end_date
     ).group_by(Project.id, Project.name)\
     .order_by(func.sum(WorkEntry.hours).desc())\
     .all()

    # Entries without project
    no_project_hours = db.session.query(func.sum(WorkEntry.hours))\
        .filter(
            WorkEntry.user_id == current_user.id,
            WorkEntry.project_id.is_(None),
            WorkEntry.work_date >= start_date,
            WorkEntry.work_date <= end_date
        ).scalar() or 0.0

    if no_project_hours > 0:
        project_data = list(project_data) + [('未分類', no_project_hours)]

    # Hours by date (daily)
    daily_data = db.session.query(
        WorkEntry.work_date,
        func.sum(WorkEntry.hours).label('total_hours')
    ).filter(
        WorkEntry.user_id == current_user.id,
        WorkEntry.work_date >= start_date,
        WorkEntry.work_date <= end_date
    ).group_by(WorkEntry.work_date)\
     .order_by(WorkEntry.work_date)\
     .all()

    # Fill missing dates
    daily_dict = {row.work_date: float(row.total_hours) for row in daily_data}
    all_dates = []
    current_d = start_date
    while current_d <= end_date:
        all_dates.append(current_d)
        current_d += timedelta(days=1)

    daily_labels = [d.strftime('%m/%d') for d in all_dates]
    daily_hours = [daily_dict.get(d, 0.0) for d in all_dates]

    # Hours by week
    weekly_data = defaultdict(float)
    for d, h in daily_dict.items():
        week_start = d - timedelta(days=d.weekday())
        weekly_data[week_start] += h

    weekly_labels = [d.strftime('%Y/%m/%d') for d in sorted(weekly_data.keys())]
    weekly_hours = [weekly_data[d] for d in sorted(weekly_data.keys())]

    # Hours by month
    monthly_data = defaultdict(float)
    for d, h in daily_dict.items():
        month_key = date(d.year, d.month, 1)
        monthly_data[month_key] += h

    monthly_labels = [d.strftime('%Y/%m') for d in sorted(monthly_data.keys())]
    monthly_hours = [monthly_data[d] for d in sorted(monthly_data.keys())]

    total_hours = sum(h for _, h in project_data)

    return render_template(
        'summary/index.html',
        start_date=start_str,
        end_date=end_str,
        project_labels=[p[0] for p in project_data],
        project_hours=[float(p[1]) for p in project_data],
        daily_labels=daily_labels,
        daily_hours=daily_hours,
        weekly_labels=weekly_labels,
        weekly_hours=weekly_hours,
        monthly_labels=monthly_labels,
        monthly_hours=monthly_hours,
        total_hours=total_hours,
    )
