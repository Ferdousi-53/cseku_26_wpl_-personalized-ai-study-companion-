import json
from app import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    premium_until = db.Column(db.DateTime)  # None = free account

    @property
    def is_premium(self):
        return bool(self.premium_until and self.premium_until > datetime.utcnow())

    @property
    def is_admin(self):
        from app.premium import ADMIN_EMAILS
        return (self.email or '').strip().lower() in [e.lower() for e in ADMIN_EMAILS]

    @property
    def has_premium(self):
        """Premium members and the admin (so the owner can test) can use premium features."""
        return self.is_premium or self.is_admin


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    subject_code = db.Column(db.String(20))
    exam_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)


class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)

class TopicPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    correct_count = db.Column(db.Integer, default=0)
    wrong_count = db.Column(db.Integer, default=0)


class QuizAnswer(db.Model):
    """One row per question of a submitted quiz, so past quizzes can be reviewed in full."""
    id = db.Column(db.Integer, primary_key=True)
    quiz_result_id = db.Column(db.Integer, db.ForeignKey('quiz_result.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON list of option strings
    correct_index = db.Column(db.Integer, nullable=False)
    selected_index = db.Column(db.Integer, nullable=False, default=-1)  # -1 = not answered
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    topic = db.Column(db.String(200))
    explanation = db.Column(db.Text)

    def as_dict(self):
        return {
            'question': self.question,
            'options': json.loads(self.options),
            'correct_index': self.correct_index,
            'selected_index': self.selected_index,
            'is_correct': self.is_correct,
            'topic': self.topic or 'General',
            'explanation': self.explanation or '',
        }


class ChatSession(db.Model):
    """One Ask AI conversation. A subject can have many, listed in the chat sidebar."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False, default='New chat')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    """A single message inside a ChatSession."""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer)  # which ChatSession it belongs to
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user', 'ai' or 'error'
    text = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text)  # JSON list of source chunks
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudyTask(db.Model):
    """One item of a subject's study plan."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    task_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    kind = db.Column(db.String(20), default='revise')  # read, revise, practice, quiz
    topic = db.Column(db.String(200))
    position = db.Column(db.Integer, default=0)
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Flashcard(db.Model):
    """A question/answer revision card made from the student's own documents."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(200))
    known = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class XpEvent(db.Model):
    """One XP award. ref_key makes every award happen only once (no farming by re-clicking)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer)
    action = db.Column(db.String(20), nullable=False)  # quiz, card, task, daily
    points = db.Column(db.Integer, nullable=False)
    ref_key = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'ref_key', name='uq_xp_user_ref'),)


class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(40), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'code', name='uq_badge_user_code'),)


class PremiumRequest(db.Model):
    """A student says 'I paid by bKash, this is my TrxID'. The admin approves or rejects it."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trx_id = db.Column(db.String(30), nullable=False, index=True)
    sender_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(12), default='pending', nullable=False)  # pending / approved / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)


class StudySummary(db.Model):
    """Premium feature: an AI summary of the student's documents."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
