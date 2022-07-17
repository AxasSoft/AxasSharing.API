import enum
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import inspect


from app import db


class CommitMixin:

    def commit(self):
        fail_reason = None
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as ex:
            db.session.rollback()
            fail_reason = ex
        except ValueError as ex:
            db.session.rollback()
            fail_reason = ex
        finally:
            return self, fail_reason


class DeleteMixin:
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return None
        except SQLAlchemyError as ex:
            db.session.rollback()
            return ex
        except ValueError as ex:
            db.session.rollback()
            return ex


class SyntheticKeyMixin:
    @declared_attr
    def pk(self):
        for base in self.__mro__[1:-1]:
            if getattr(base, '__table__', None) is not None:
                t = db.ForeignKey(base.pk)
                break
        else:
            t = db.Integer

        return db.Column('id', t, primary_key=True)


class HistoryMixin:

    @property
    def history(self):
        state = inspect(self)

        changes = {}

        for attr in state.attrs:
            hist = state.get_history(attr.key, True)

            if not hist.has_changes():
                continue

            old_value = hist.deleted[0] if hist.deleted else None
            new_value = hist.added[0] if hist.added else None
            if old_value != new_value:
                changes[attr.key] = [old_value, new_value]

        return changes


class OrderMixin:
    order_num = db.Column(db.Integer(), nullable=True)


class UtcCreatedMixin:
    created = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)


class User(db.Model, DeleteMixin, CommitMixin, HistoryMixin, UtcCreatedMixin):

    __tablename__ = 'users'

    class Meta:
        enable_in_sai = True
        column_searchable_list = []

    pk = db.Column('id', db.Integer(), primary_key=True, index=True, unique=True, nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False, default=False)

    tel = db.Column(db.String(), nullable=True)

    avatar = db.Column(db.String(), nullable=True)
    passport_photo = db.Column(db.String(), nullable=True)
    name = db.Column(db.String(), nullable=True)
    passport_issued = db.Column(db.String(), nullable=True)
    issue_date = db.Column(db.String(), nullable=True)
    department_code = db.Column(db.String(), nullable=True)
    passport_series = db.Column(db.String(), nullable=True)
    passport_num = db.Column(db.String(), nullable=True)
    surname = db.Column(db.String(), nullable=True)
    patronymic = db.Column(db.String(), nullable=True)
    gender = db.Column(db.String(), nullable=True)
    birthdate = db.Column(db.String(), nullable=True)
    birthplace = db.Column(db.String(), nullable=True)

    token_pairs = db.relationship('TokenPair', back_populates='user')
    devices = db.relationship('Device', back_populates='user')
    notifications = db.relationship('Notification', back_populates='user')
    rents = db.relationship('Rent', back_populates='user')


class Token(db.Model, SyntheticKeyMixin, DeleteMixin, CommitMixin, HistoryMixin,):

    __tablename__ = 'tokens'

    class Meta:
        enable_in_sai = True

    value = db.Column(db.String(), nullable=False)
    expires_at = db.Column(db.DateTime(), nullable=False)

    as_refresh = db.relationship(
        'TokenPair',
        uselist=False,
        back_populates='refresh_token',
        foreign_keys='[TokenPair.refresh_token_id]'
    )
    as_access = db.relationship(
        'TokenPair',
        uselist=False,
        back_populates='access_token',
        foreign_keys='[TokenPair.access_token_id]'

    )


class TokenPair(db.Model, SyntheticKeyMixin, DeleteMixin, CommitMixin, HistoryMixin,):

    __tablename__ = 'token_pairs'

    class Meta:
        enable_in_sai = True

    device = db.Column(db.String(), nullable=True)

    user_id = db.Column(db.Integer(), db.ForeignKey(User.pk), nullable=True)

    refresh_token_id = db.Column(db.Integer, db.ForeignKey(Token.pk), nullable=False)
    access_token_id = db.Column(db.Integer(), db.ForeignKey(Token.pk), nullable=False)

    user = db.relationship(User, back_populates='token_pairs')

    refresh_token = db.relationship(
        Token,
        foreign_keys=[refresh_token_id],
        back_populates='as_refresh'
    )
    access_token = db.relationship(
        Token,
        foreign_keys=[access_token_id],
        back_populates='as_access'
    )


class Device(db.Model, SyntheticKeyMixin, DeleteMixin, CommitMixin, HistoryMixin,):

    __tablename__ = 'devices'

    class Meta:
        enable_in_sai = True
        column_searchable_list = []
        column_filters = []

    user_id = db.Column(db.Integer(), db.ForeignKey(User.pk), nullable=False)
    firebase_id = db.Column(db.String(), nullable=True)
    user_agent = db.Column(db.String(), nullable=True)
    enable_notification = db.Column(db.Boolean(), nullable=False, default=True)

    user = db.relationship(User, back_populates='devices')


class Code(db.Model, SyntheticKeyMixin, DeleteMixin, CommitMixin, HistoryMixin,):

    __tablename__ = 'verification_codes'

    class Meta:
        enable_in_sai = True
        column_searchable_list = []
        column_filters = []

    target = db.Column(db.String(), nullable=False)
    code = db.Column(db.String(), nullable=False)
    used = db.Column(
        db.Boolean(),
        default=False,
        nullable=False
    )
    expired_at = db.Column(
        db.DateTime(),
        nullable=True,
        default=lambda: datetime.utcnow()+timedelta(minutes=5)
    )


class Notification(db.Model, SyntheticKeyMixin, DeleteMixin, CommitMixin, HistoryMixin,):

    __tablename__ = 'notifications'

    class Meta:
        enable_in_sai = True
        column_searchable_list = []
        column_filters = []

    text = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    read = db.Column(db.Boolean(), nullable=False, default=False)

    user_id = db.Column(db.Integer(), db.ForeignKey(User.pk), nullable=False)

    user = db.relationship(User, back_populates='notifications')


class Flat(db.Model, SyntheticKeyMixin, DeleteMixin, CommitMixin, HistoryMixin,):

    __tablename__ = 'flats'

    class Meta:
        enable_in_sai = True
        column_searchable_list = []
        column_filters = []

    room_count = db.Column(db.Integer(), nullable=False)
    has_balcony = db.Column(db.Boolean,nullable=False)
    has_loggia = db.Column(db.Boolean,nullable=False)
    address = db.Column(db.String(), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    area = db.Column(db.Float, nullable=False)
    price_short = db.Column(db.Integer, nullable=True)
    price_long = db.Column(db.Integer, nullable=True)
    children = db.Column(db.Boolean,nullable=False)
    animals = db.Column(db.Boolean,nullable=False)
    washing_machine = db.Column(db.Boolean,nullable=False)
    fridge = db.Column(db.Boolean,nullable=False)
    tv = db.Column(db.Boolean,nullable=False)
    dishwasher = db.Column(db.Boolean,nullable=False)
    air_conditioner = db.Column(db.Boolean,nullable=False)
    smoking = db.Column(db.Boolean,nullable=False)
    noise = db.Column(db.Boolean(),nullable=False)
    party = db.Column(db.Boolean(),nullable=False)
    title = db.Column(db.String(),nullable=False)
    guest_count = db.Column(db.Integer(),nullable=False)
    bed_count = db.Column(db.Integer,nullable=False)
    restroom_count = db.Column(db.Integer,nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey(User.pk), nullable=True)

    user = db.relationship(User)

    pictures = db.relationship('FlatPicture', back_populates='flat')
    rents = db.relationship('Rent', back_populates='flat')


class FlatPicture(db.Model, SyntheticKeyMixin, DeleteMixin, CommitMixin, HistoryMixin,):
    flat_id = db.Column(db.Integer, db.ForeignKey(Flat.pk),nullable=False)
    link = db.Column(db.String, nullable=False)

    flat = db.relationship(Flat, back_populates='pictures')


class Rent(db.Model, SyntheticKeyMixin, DeleteMixin, CommitMixin, HistoryMixin,):
    flat_id = db.Column(db.Integer, db.ForeignKey(Flat.pk),nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey(User.pk), nullable=True)
    start_at = db.Column(db.DateTime(), nullable=False)
    end_at = db.Column(db.DateTime(),  nullable=False)

    user = db.relationship(User, back_populates='rents')
    flat = db.relationship(Flat, back_populates='rents')
