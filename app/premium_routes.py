"""Upgrade page, admin payment approval and the premium-only features."""
import json
import time
from datetime import datetime
from functools import wraps

from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import User, Subject, Document, PremiumRequest, StudySummary
from app.gemini import GeminiError
from app.gamification import LOCAL_OFFSET
from app.premium import (BKASH_NUMBER, PRICE_BDT, PREMIUM_DAYS, FEATURES, premium_required, clean_trx,
                         clean_phone, valid_phone, TRX_RE, extend_premium, days_left)
from app.summary import build_summary
from app.quiz import generate_quiz

MAX_PENDING = 3
EXAM_SIZES = (10, 20, 30)


def local(dt):
    return (dt + LOCAL_OFFSET).strftime('%d %b %Y, %I:%M %p') if dt else ''


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def own_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    return subject if subject.user_id == current_user.id else None


def register_premium_routes(app):

    @app.context_processor
    def inject_premium():
        if not current_user.is_authenticated:
            return {}
        info = {'active': current_user.is_premium, 'days': days_left(current_user),
                'admin': current_user.is_admin, 'pending': 0}
        if info['admin']:
            info['pending'] = PremiumRequest.query.filter_by(status='pending').count()
        return {'prem': info}

    # ---------- student: upgrade ----------
    @app.route('/upgrade')
    @login_required
    def upgrade():
        history = (PremiumRequest.query.filter_by(user_id=current_user.id)
                   .order_by(PremiumRequest.id.desc()).limit(10).all())
        rows = [{'trx': r.trx_id, 'status': r.status, 'when': local(r.created_at)} for r in history]
        has_pending = any(r['status'] == 'pending' for r in rows)
        return render_template('upgrade.html', number=BKASH_NUMBER, price=PRICE_BDT, days=PREMIUM_DAYS,
                               feature=FEATURES.get(request.args.get('feature', '')), features=list(FEATURES.values()),
                               rows=rows, has_pending=has_pending,
                               until=local(current_user.premium_until) if current_user.is_premium else '')

    @app.route('/upgrade/submit', methods=['POST'])
    @login_required
    def upgrade_submit():
        trx = clean_trx(request.form.get('trx_id'))
        phone = clean_phone(request.form.get('sender_number'))

        if not TRX_RE.match(trx):
            flash('TrxID ta thik na. bKash-er SMS-e deya TrxID (jemon 8N7A3B2C1D) hubohu likho.')
            return redirect(url_for('upgrade'))
        if not valid_phone(phone):
            flash('Je bKash number theke taka pathiyecho, shei 11 digit-er number ta thik moto likho.')
            return redirect(url_for('upgrade'))
        if PremiumRequest.query.filter_by(user_id=current_user.id, status='pending').count() >= MAX_PENDING:
            flash('Tomar kichu request ekhono pending. Admin approve korar jonno ektu opekkha koro.')
            return redirect(url_for('upgrade'))
        if PremiumRequest.query.filter(PremiumRequest.trx_id == trx,
                                       PremiumRequest.status.in_(['pending', 'approved'])).first():
            flash('Ei TrxID ager-i submit kora ba use kora hoyeche.')
            return redirect(url_for('upgrade'))

        db.session.add(PremiumRequest(user_id=current_user.id, trx_id=trx, sender_number=phone, amount=PRICE_BDT))
        db.session.commit()
        flash('Request pathano hoyeche. Admin payment check kore approve korle Premium chalu hoye jabe.')
        return redirect(url_for('upgrade'))

    # ---------- admin: approve payments ----------
    @app.route('/admin/payments')
    @login_required
    @admin_required
    def admin_payments():
        def rows(query):
            out = []
            for r in query:
                user = User.query.get(r.user_id)
                out.append({'id': r.id, 'trx': r.trx_id, 'phone': r.sender_number, 'amount': r.amount,
                            'status': r.status, 'when': local(r.created_at), 'reviewed': local(r.reviewed_at),
                            'name': user.name if user else '?', 'email': user.email if user else ''})
            return out
        pending = rows(PremiumRequest.query.filter_by(status='pending').order_by(PremiumRequest.id).all())
        done = rows(PremiumRequest.query.filter(PremiumRequest.status != 'pending')
                    .order_by(PremiumRequest.id.desc()).limit(30).all())
        return render_template('admin_payments.html', pending=pending, done=done, number=BKASH_NUMBER, days=PREMIUM_DAYS)

    @app.route('/admin/payments/<int:req_id>/<action>', methods=['POST'])
    @login_required
    @admin_required
    def admin_review(req_id, action):
        if action not in ('approve', 'reject'):
            abort(404)
        req = PremiumRequest.query.get_or_404(req_id)
        if req.status != 'pending':
            flash('Ei request ager-i dekha hoyeche.')
            return redirect(url_for('admin_payments'))
        if action == 'approve':
            user = User.query.get(req.user_id)
            if user:
                extend_premium(user)
            req.status = 'approved'
            flash(f'Approved. {user.name if user else "User"} ekhon Premium.')
        else:
            req.status = 'rejected'
            flash('Rejected.')
        req.reviewed_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('admin_payments'))

    # ---------- premium feature 1: smart summary ----------
    @app.route('/subject/<int:subject_id>/summary')
    @login_required
    @premium_required('summary')
    def summary_page(subject_id):
        subject = own_subject(subject_id)
        if not subject:
            return redirect(url_for('dashboard'))
        documents = Document.query.filter_by(subject_id=subject_id).all()
        saved = (StudySummary.query.filter_by(user_id=current_user.id, subject_id=subject_id)
                 .order_by(StudySummary.id.desc()).all())
        wanted = request.args.get('s', type=int)
        current = next((s for s in saved if s.id == wanted), saved[0] if saved else None)
        data = json.loads(current.content) if current else None
        return render_template('summary.html', subject=subject, documents=documents, saved=saved,
                               current=current, data=data, when=local(current.created_at) if current else '')

    @app.route('/subject/<int:subject_id>/summary/generate', methods=['POST'])
    @login_required
    @premium_required('summary')
    def summary_generate(subject_id):
        subject = own_subject(subject_id)
        if not subject:
            return redirect(url_for('dashboard'))
        valid = {d.id: d.filename for d in Document.query.filter_by(subject_id=subject_id).all()}
        ids = [i for i in request.form.getlist('document_ids', type=int) if i in valid]
        if not ids:
            flash('Kompokkhe ekta document select koro.')
            return redirect(url_for('summary_page', subject_id=subject_id))
        try:
            data = build_summary(subject_id, ids)
        except GeminiError as e:
            flash(e.user_message)
            return redirect(url_for('summary_page', subject_id=subject_id))
        title = ', '.join(valid[i] for i in ids)[:190]
        row = StudySummary(user_id=current_user.id, subject_id=subject_id, title=title, content=json.dumps(data))
        db.session.add(row)
        db.session.commit()
        return redirect(url_for('summary_page', subject_id=subject_id, s=row.id))

    @app.route('/subject/<int:subject_id>/summary/<int:summary_id>/delete', methods=['POST'])
    @login_required
    @premium_required('summary')
    def summary_delete(subject_id, summary_id):
        row = StudySummary.query.filter_by(id=summary_id, user_id=current_user.id, subject_id=subject_id).first()
        if row:
            db.session.delete(row)
            db.session.commit()
        return redirect(url_for('summary_page', subject_id=subject_id))

    # ---------- premium feature 2: mock exam ----------
    @app.route('/subject/<int:subject_id>/exam')
    @login_required
    @premium_required('exam')
    def exam_setup(subject_id):
        subject = own_subject(subject_id)
        if not subject:
            return redirect(url_for('dashboard'))
        documents = Document.query.filter_by(subject_id=subject_id).all()
        return render_template('exam_setup.html', subject=subject, documents=documents, sizes=EXAM_SIZES)

    @app.route('/subject/<int:subject_id>/exam/start', methods=['POST'])
    @login_required
    @premium_required('exam')
    def exam_start(subject_id):
        from app.routes import quiz_store  # same store the normal quiz uses, so submit_quiz grades it
        subject = own_subject(subject_id)
        if not subject:
            return redirect(url_for('dashboard'))
        size = request.form.get('size', 20, type=int)
        if size not in EXAM_SIZES:
            size = 20
        valid = [d.id for d in Document.query.filter_by(subject_id=subject_id).all()]
        ids = [i for i in request.form.getlist('document_ids', type=int) if i in valid]
        if not ids:
            flash('Kompokkhe ekta document select koro.')
            return redirect(url_for('exam_setup', subject_id=subject_id))
        try:
            quiz_data = generate_quiz(subject_id, ids, num_questions=size, exam=True)
        except GeminiError as e:
            flash(e.user_message)
            return redirect(url_for('exam_setup', subject_id=subject_id))
        quiz_store[current_user.id] = quiz_data
        minutes = len(quiz_data)  # one minute per question
        return render_template('exam.html', subject=subject, quiz=quiz_data, minutes=minutes,
                               deadline_ms=int((time.time() + minutes * 60) * 1000))
