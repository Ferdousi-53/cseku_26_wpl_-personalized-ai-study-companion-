import os
import json
from datetime import datetime, timedelta, date
from flask import render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Subject, Document, QuizResult, TopicPerformance, QuizAnswer, ChatMessage, ChatSession, StudyTask, Flashcard
from app.rag import process_document, delete_document_chunks
from app.ai_tutor import get_ai_answer
from app.quiz import generate_quiz, get_weak_topics
from app.gemini import GeminiError
from app.study_plan import build_plan
from app.flashcards import build_cards
from app.gamification import award, quiz_lines, achievements_data, XP_CARD, XP_TASK
from app.dashboard_data import build_dashboard

quiz_store = {}


def recent_chat(session_id, limit=6):
    """Last few real messages of one chat (oldest first), used as AI context."""
    rows = (ChatMessage.query.filter(ChatMessage.session_id == session_id,
                                     ChatMessage.role.in_(['user', 'ai']))
            .order_by(ChatMessage.id.desc()).limit(limit).all())
    return [{'role': m.role, 'text': m.text} for m in reversed(rows)]


def queue_rewards(rewards):
    """Shows the XP toast on the next page that is rendered."""
    if rewards:
        session['_rewards'] = rewards


def register_routes(app):

    from app.premium_routes import register_premium_routes
    register_premium_routes(app)

    @app.context_processor
    def inject_rewards():
        return {'rewards': session.pop('_rewards', None)}

    @app.route('/')
    def home():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('landing.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered!')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password)
            new_user = User(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! Please login.')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password')
                return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', user=current_user, **build_dashboard(current_user))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/subject/add', methods=['GET', 'POST'])
    @login_required
    def add_subject():
        if request.method == 'POST':
            subject_name = request.form['subject_name']
            subject_code = request.form['subject_code']
            exam_date_str = request.form['exam_date']

            exam_date = None
            if exam_date_str:
                exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date()

            new_subject = Subject(
                subject_name=subject_name,
                subject_code=subject_code,
                exam_date=exam_date,
                user_id=current_user.id
            )
            db.session.add(new_subject)
            db.session.commit()

            flash('Subject added successfully!')
            return redirect(url_for('dashboard'))

        return render_template('add_subject.html')

    @app.route('/subject/delete/<int:subject_id>')
    @login_required
    def delete_subject(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id == current_user.id:
            documents = Document.query.filter_by(subject_id=subject.id).all()
            for doc in documents:
                delete_document_chunks(doc.id)
                file_path = os.path.join('uploads', doc.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(doc)

            QuizAnswer.query.filter_by(subject_id=subject.id).delete()
            ChatMessage.query.filter_by(subject_id=subject.id).delete()
            ChatSession.query.filter_by(subject_id=subject.id).delete()
            StudyTask.query.filter_by(subject_id=subject.id).delete()
            Flashcard.query.filter_by(subject_id=subject.id).delete()
            QuizResult.query.filter_by(subject_id=subject.id).delete()
            TopicPerformance.query.filter_by(subject_id=subject.id).delete()

            db.session.delete(subject)
            db.session.commit()
            flash('Subject and its documents deleted.')
        return redirect(url_for('dashboard'))

    @app.route('/subject/<int:subject_id>/upload', methods=['GET', 'POST'])
    @login_required
    def upload_document(subject_id):
        subject = Subject.query.get_or_404(subject_id)

        if request.method == 'POST':
            file = request.files['document']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join('uploads', filename)
                file.save(upload_path)

                new_doc = Document(filename=filename, subject_id=subject_id)
                db.session.add(new_doc)
                db.session.commit()

                try:
                    num_chunks = process_document(upload_path, subject_id, new_doc.id)
                except Exception as e:
                    print('UPLOAD ERROR:', repr(e))
                    num_chunks = 0

                if num_chunks == 0:
                    delete_document_chunks(new_doc.id)
                    db.session.delete(new_doc)
                    db.session.commit()
                    flash('Ei PDF theke kono text pawa jayni. Scanned ba chhobi-r PDF-er text select kora jay na, '
                          'text-wala PDF diye try koro.')
                    return redirect(url_for('upload_document', subject_id=subject_id))

                flash(f'Document uploaded and processed into {num_chunks} chunks!')
                return redirect(url_for('dashboard'))

        documents = Document.query.filter_by(subject_id=subject_id).all()
        return render_template('upload_document.html', subject=subject, documents=documents)

    @app.route('/document/delete/<int:document_id>')
    @login_required
    def delete_document(document_id):
        document = Document.query.get_or_404(document_id)
        subject = Subject.query.get_or_404(document.subject_id)

        if subject.user_id != current_user.id:
            flash('Ei document delete korar permission nei.')
            return redirect(url_for('dashboard'))

        delete_document_chunks(document.id)

        file_path = os.path.join('uploads', document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        db.session.delete(document)
        db.session.commit()

        flash('Document deleted.')
        return redirect(url_for('upload_document', subject_id=subject.id))

    @app.route('/subject/<int:subject_id>/tutor', methods=['GET', 'POST'])
    @login_required
    def ai_tutor(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))

        documents = Document.query.filter_by(subject_id=subject_id).all()
        valid_ids = [d.id for d in documents]
        selection_key = f'tutor_docs_{subject_id}'

        if request.method == 'POST':
            question = request.form.get('question', '').strip()
            selected_ids = [int(i) for i in request.form.getlist('document_ids')]
            selected_ids = [i for i in selected_ids if i in valid_ids]
            chat_id = request.form.get('chat_id', type=int)
            chat = None
            if chat_id:
                chat = ChatSession.query.filter_by(id=chat_id, user_id=current_user.id,
                                                   subject_id=subject_id).first()

            if not selected_ids:
                flash('Kompokkhe ekta document select koro.')
            elif question:
                session[selection_key] = selected_ids
                if chat is None:  # first message of a new chat
                    title = question if len(question) <= 45 else question[:45] + '...'
                    chat = ChatSession(user_id=current_user.id, subject_id=subject_id, title=title)
                    db.session.add(chat)
                    db.session.flush()

                history = recent_chat(chat.id)
                db.session.add(ChatMessage(session_id=chat.id, user_id=current_user.id, subject_id=subject_id,
                                           role='user', text=question))
                chat.updated_at = datetime.utcnow()
                db.session.commit()

                answer, sources = get_ai_answer(question, subject_id, document_ids=selected_ids, history=history)

                db.session.add(ChatMessage(session_id=chat.id, user_id=current_user.id, subject_id=subject_id,
                                           role='ai' if sources is not None else 'error',
                                           text=answer, sources=json.dumps(sources or [])))
                chat.updated_at = datetime.utcnow()
                db.session.commit()

            return redirect(url_for('ai_tutor', subject_id=subject_id, chat=chat.id if chat else 'new'))

        sessions = (ChatSession.query.filter_by(user_id=current_user.id, subject_id=subject_id)
                    .order_by(ChatSession.updated_at.desc()).all())
        chat_param = request.args.get('chat', '')
        active = None
        if chat_param != 'new':
            if chat_param.isdigit():
                active = next((s for s in sessions if s.id == int(chat_param)), None)
            if active is None and sessions:
                active = sessions[0]  # no chat chosen: open the latest one

        messages = []
        if active:
            rows = ChatMessage.query.filter_by(session_id=active.id).order_by(ChatMessage.id).all()
            messages = [{'role': 'user' if m.role == 'user' else 'ai', 'text': m.text,
                         'sources': json.loads(m.sources) if m.sources else []} for m in rows]

        chat_list = [{'id': s.id, 'title': s.title,
                      'when': (s.updated_at + timedelta(hours=6)).strftime('%d %b')} for s in sessions]
        selected_ids = [i for i in session.get(selection_key, valid_ids) if i in valid_ids] or valid_ids
        return render_template('ai_tutor.html', subject=subject, documents=documents,
                               messages=messages, selected_ids=selected_ids,
                               chat_list=chat_list, active_id=active.id if active else None,
                               prefill=request.args.get('q', '')[:300])

    @app.route('/subject/<int:subject_id>/tutor/<int:chat_id>/delete', methods=['POST'])
    @login_required
    def delete_chat(subject_id, chat_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id == current_user.id:
            chat = ChatSession.query.filter_by(id=chat_id, user_id=current_user.id, subject_id=subject_id).first()
            if chat:
                ChatMessage.query.filter_by(session_id=chat.id).delete()
                db.session.delete(chat)
                db.session.commit()
        return redirect(url_for('ai_tutor', subject_id=subject_id))

    @app.route('/subject/<int:subject_id>/quiz/setup')
    @login_required
    def quiz_setup(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        documents = Document.query.filter_by(subject_id=subject_id).all()
        return render_template('quiz_setup.html', subject=subject, documents=documents,
                               has_weak=bool(get_weak_topics(subject_id)))

    @app.route('/subject/<int:subject_id>/quiz', methods=['POST'])
    @login_required
    def start_quiz(subject_id):
        subject = Subject.query.get_or_404(subject_id)

        try:
            num_questions = int(request.form['num_questions'])
        except (KeyError, ValueError):
            num_questions = 5

        if num_questions < 1:
            num_questions = 1
        if num_questions > 20:
            num_questions = 20

        selected_ids = request.form.getlist('document_ids')
        document_ids = [int(i) for i in selected_ids]

        valid_ids = [d.id for d in Document.query.filter_by(subject_id=subject_id).all()]
        document_ids = [i for i in document_ids if i in valid_ids]

        if not document_ids:
            flash('Kompokkhe ekta document select koro.')
            return redirect(url_for('quiz_setup', subject_id=subject_id))

        try:
            quiz_data = generate_quiz(subject_id, document_ids, num_questions=num_questions)
        except GeminiError as e:
            flash(e.user_message)
            return redirect(url_for('quiz_setup', subject_id=subject_id))

        if not quiz_data:
            flash('Quiz generate kora jayni. Abar try koro.')
            return redirect(url_for('quiz_setup', subject_id=subject_id))

        quiz_store[current_user.id] = quiz_data
        return render_template('quiz.html', subject=subject, quiz=quiz_data)

    @app.route('/subject/<int:subject_id>/quiz/weak', methods=['POST'])
    @login_required
    def start_weak_quiz(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))

        # a study-plan "practice" task sends one specific topic; otherwise use the weak topics
        chosen = request.form.get('topic', '').strip()[:200]
        topics = [chosen] if chosen else get_weak_topics(subject_id)
        if not topics:
            flash('Ekhono kono weak topic nai. Age kichu quiz dao, tarpor dubol topic gulo ekhane ashbe.')
            return redirect(url_for('quiz_setup', subject_id=subject_id))

        document_ids = [d.id for d in Document.query.filter_by(subject_id=subject_id).all()]
        if not document_ids:
            flash('Age ekta document upload koro.')
            return redirect(url_for('upload_document', subject_id=subject_id))

        try:
            quiz_data = generate_quiz(subject_id, document_ids, num_questions=5, focus_topics=topics)
        except GeminiError as e:
            flash(e.user_message)
            return redirect(url_for('quiz_setup', subject_id=subject_id))

        quiz_store[current_user.id] = quiz_data
        return render_template('quiz.html', subject=subject, quiz=quiz_data)

    @app.route('/subject/<int:subject_id>/quiz/submit', methods=['POST'])
    @login_required
    def submit_quiz(subject_id):
        quiz_data = quiz_store.get(current_user.id)
        if not quiz_data:
            flash('Quiz session expire hoye geche, abar shuru koro.')
            return redirect(url_for('dashboard'))

        score = 0
        results = []
        for idx, q in enumerate(quiz_data):
            selected = request.form.get(f'q{idx}')
            selected_index = int(selected) if selected is not None else -1
            is_correct = selected_index == q['correct_index']
            if is_correct:
                score += 1

            topic = q.get('topic', 'General')
            topic_record = TopicPerformance.query.filter_by(subject_id=subject_id, topic=topic).first()
            if not topic_record:
                topic_record = TopicPerformance(subject_id=subject_id, topic=topic, correct_count=0, wrong_count=0)
                db.session.add(topic_record)

            if is_correct:
                topic_record.correct_count += 1
            else:
                topic_record.wrong_count += 1

            results.append({
                'question': q['question'],
                'options': q['options'],
                'correct_index': q['correct_index'],
                'selected_index': selected_index,
                'is_correct': is_correct,
                'topic': topic,
                'explanation': q.get('explanation', '')
            })

        quiz_result = QuizResult(subject_id=subject_id, score=score, total_questions=len(quiz_data))
        db.session.add(quiz_result)
        db.session.flush()  # gives quiz_result an id

        for item in results:
            db.session.add(QuizAnswer(
                quiz_result_id=quiz_result.id, subject_id=subject_id,
                question=item['question'], options=json.dumps(item['options']),
                correct_index=item['correct_index'], selected_index=item['selected_index'],
                is_correct=item['is_correct'], topic=item['topic'],
                explanation=item.get('explanation', '')))
        db.session.commit()

        queue_rewards(award(current_user.id, 'quiz', quiz_lines(score, len(quiz_data)),
                            f'quiz:{quiz_result.id}', subject_id=subject_id))

        subject = Subject.query.get_or_404(subject_id)
        return render_template('quiz_result.html', subject=subject, results=results, score=score, total=len(quiz_data))

    @app.route('/subject/<int:subject_id>/history')
    @login_required
    def quiz_history(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))

        results = QuizResult.query.filter_by(subject_id=subject_id).order_by(QuizResult.date_taken.desc()).all()

        answered_ids = {row[0] for row in db.session.query(QuizAnswer.quiz_result_id)
                        .filter(QuizAnswer.subject_id == subject_id).distinct().all()}

        history = []
        for r in results:
            percent = round(r.score * 100 / r.total_questions)
            local_time = r.date_taken + timedelta(hours=6)
            history.append({
                'id': r.id,
                'has_details': r.id in answered_ids,
                'score': r.score,
                'total': r.total_questions,
                'percent': percent,
                'date': local_time.strftime('%d %b %Y, %I:%M %p')
            })

        total_attempts = len(history)
        average_percent = 0
        best_percent = 0
        if total_attempts > 0:
            average_percent = round(sum(h['percent'] for h in history) / total_attempts)
            best_percent = max(h['percent'] for h in history)

        return render_template('quiz_history.html', subject=subject, history=history,
                               total_attempts=total_attempts,
                               average_percent=average_percent,
                               best_percent=best_percent)

    @app.route('/subject/<int:subject_id>/history/<int:result_id>')
    @login_required
    def review_quiz(subject_id, result_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))

        result = QuizResult.query.get_or_404(result_id)
        if result.subject_id != subject_id:
            return redirect(url_for('quiz_history', subject_id=subject_id))

        answers = QuizAnswer.query.filter_by(quiz_result_id=result_id).order_by(QuizAnswer.id).all()
        if not answers:
            flash('Ei quiz-er question gulo save kora hoy ni. Notun quiz theke shob save hobe.')
            return redirect(url_for('quiz_history', subject_id=subject_id))

        taken = result.date_taken + timedelta(hours=6)
        return render_template('quiz_result.html', subject=subject,
                               results=[a.as_dict() for a in answers],
                               score=result.score, total=result.total_questions,
                               is_review=True, review_date=taken.strftime('%d %b %Y, %I:%M %p'))

    def local_today():
        return (datetime.utcnow() + timedelta(hours=6)).date()

    @app.route('/subject/<int:subject_id>/plan')
    @login_required
    def study_plan(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))

        today = local_today()
        tasks = (StudyTask.query.filter_by(user_id=current_user.id, subject_id=subject_id)
                 .order_by(StudyTask.task_date, StudyTask.position, StudyTask.id).all())
        total = len(tasks)
        completed = sum(1 for t in tasks if t.done)
        missed = [t for t in tasks if t.task_date < today and not t.done]

        def label(day):
            if day == today:
                text = 'Today'
            elif day == today + timedelta(days=1):
                text = 'Tomorrow'
            else:
                text = day.strftime('%a, %d %b')
            if subject.exam_date and day == subject.exam_date:
                text += ' - Exam day'
            return text

        days = []
        for t in tasks:
            if t.task_date < today:
                continue
            if not days or days[-1]['date'] != t.task_date:
                days.append({'date': t.task_date, 'label': label(t.task_date),
                             'is_today': t.task_date == today, 'tasks': []})
            days[-1]['tasks'].append(t)

        days_left = (subject.exam_date - today).days if subject.exam_date else None
        return render_template('study_plan.html', subject=subject, days=days, missed=missed,
                               total=total, completed=completed,
                               percent=round(completed * 100 / total) if total else 0,
                               days_left=days_left, has_plan=bool(days))

    @app.route('/subject/<int:subject_id>/plan/generate', methods=['POST'])
    @login_required
    def generate_study_plan(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))

        today = local_today()
        if not subject.exam_date or subject.exam_date < today:
            flash('Age ekta bhobishyot-er exam date set koro.')
            return redirect(url_for('study_plan', subject_id=subject_id))
        if not Document.query.filter_by(subject_id=subject_id).first():
            flash('Plan banate age ekta document upload koro.')
            return redirect(url_for('upload_document', subject_id=subject_id))

        hours = request.form.get('hours', type=int)
        hours = hours if hours in (1, 2, 3) else 2

        try:
            items = build_plan(subject, today, hours)
        except GeminiError as e:
            flash(e.user_message)
            return redirect(url_for('study_plan', subject_id=subject_id))

        # replace today's and future tasks; earlier days stay as history
        StudyTask.query.filter(StudyTask.user_id == current_user.id, StudyTask.subject_id == subject_id,
                               StudyTask.task_date >= today).delete()
        for item in items:
            db.session.add(StudyTask(user_id=current_user.id, subject_id=subject_id, task_date=item['date'],
                                     title=item['title'], kind=item['kind'], topic=item['topic'],
                                     position=item['position']))
        db.session.commit()
        return redirect(url_for('study_plan', subject_id=subject_id))

    @app.route('/subject/<int:subject_id>/plan/task/<int:task_id>/toggle', methods=['POST'])
    @login_required
    def toggle_task(subject_id, task_id):
        task = StudyTask.query.filter_by(id=task_id, subject_id=subject_id, user_id=current_user.id).first()
        if not task:
            return jsonify(error='not found'), 404
        task.done = not task.done
        db.session.commit()
        total = StudyTask.query.filter_by(user_id=current_user.id, subject_id=subject_id).count()
        completed = StudyTask.query.filter_by(user_id=current_user.id, subject_id=subject_id, done=True).count()
        rewards = None
        if task.done:
            rewards = award(current_user.id, 'task', [('Study plan task done', XP_TASK)],
                            f'task:{task.id}', subject_id=subject_id)
        return jsonify(done=task.done, completed=completed, total=total, rewards=rewards)

    @app.route('/subject/<int:subject_id>/exam-date', methods=['POST'])
    @login_required
    def set_exam_date(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))
        try:
            subject.exam_date = datetime.strptime(request.form.get('exam_date', ''), '%Y-%m-%d').date()
            db.session.commit()
        except ValueError:
            flash('Date ta thik na, abar try koro.')
        return redirect(url_for('study_plan', subject_id=subject_id))

    @app.route('/subject/<int:subject_id>/flashcards')
    @login_required
    def flashcards(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))
        documents = Document.query.filter_by(subject_id=subject_id).all()
        cards = (Flashcard.query.filter_by(user_id=current_user.id, subject_id=subject_id)
                 .order_by(Flashcard.id).all())
        data = [{'id': c.id, 'front': c.front, 'back': c.back, 'topic': c.topic or '', 'known': bool(c.known)}
                for c in cards]
        return render_template('flashcards.html', subject=subject, documents=documents,
                               cards=data, known=sum(1 for c in data if c['known']))

    @app.route('/subject/<int:subject_id>/flashcards/generate', methods=['POST'])
    @login_required
    def generate_flashcards(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id != current_user.id:
            return redirect(url_for('dashboard'))

        valid_ids = [d.id for d in Document.query.filter_by(subject_id=subject_id).all()]
        document_ids = [i for i in (request.form.getlist('document_ids', type=int)) if i in valid_ids]
        if not document_ids:
            flash('Kompokkhe ekta document select koro.')
            return redirect(url_for('flashcards', subject_id=subject_id))

        count = request.form.get('count', 10, type=int)
        existing = [c.front for c in Flashcard.query.filter_by(user_id=current_user.id, subject_id=subject_id).all()]
        try:
            cards = build_cards(subject_id, document_ids, count, existing_fronts=existing)
        except GeminiError as e:
            flash(e.user_message)
            return redirect(url_for('flashcards', subject_id=subject_id))

        for c in cards:
            db.session.add(Flashcard(user_id=current_user.id, subject_id=subject_id,
                                     front=c['front'], back=c['back'], topic=c['topic']))
        db.session.commit()
        return redirect(url_for('flashcards', subject_id=subject_id))

    @app.route('/subject/<int:subject_id>/flashcards/<int:card_id>/mark', methods=['POST'])
    @login_required
    def mark_flashcard(subject_id, card_id):
        card = Flashcard.query.filter_by(id=card_id, subject_id=subject_id, user_id=current_user.id).first()
        if not card:
            return jsonify(error='not found'), 404
        card.known = request.form.get('known') == '1'
        db.session.commit()
        total = Flashcard.query.filter_by(user_id=current_user.id, subject_id=subject_id).count()
        known = Flashcard.query.filter_by(user_id=current_user.id, subject_id=subject_id, known=True).count()
        rewards = None
        if card.known:
            rewards = award(current_user.id, 'card', [('Flashcard learned', XP_CARD)],
                            f'card:{card.id}', subject_id=subject_id)
        return jsonify(known=card.known, known_count=known, total=total, rewards=rewards)

    @app.route('/subject/<int:subject_id>/flashcards/clear', methods=['POST'])
    @login_required
    def clear_flashcards(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        if subject.user_id == current_user.id:
            Flashcard.query.filter_by(user_id=current_user.id, subject_id=subject_id).delete()
            db.session.commit()
        return redirect(url_for('flashcards', subject_id=subject_id))

    @app.route('/achievements')
    @login_required
    def achievements():
        return render_template('achievements.html', **achievements_data(current_user.id))

    @app.route('/subject/<int:subject_id>/weak-topics')
    @login_required
    def weak_topics(subject_id):
        subject = Subject.query.get_or_404(subject_id)
        topics = TopicPerformance.query.filter_by(subject_id=subject_id).all()

        topic_list = []
        for t in topics:
            total = t.correct_count + t.wrong_count
            accuracy = round(t.correct_count * 100 / total) if total > 0 else 0
            topic_list.append({
                'topic': t.topic,
                'correct': t.correct_count,
                'wrong': t.wrong_count,
                'accuracy': accuracy
            })

        topic_list.sort(key=lambda x: x['accuracy'])

        return render_template('weak_topics.html', subject=subject, topics=topic_list)