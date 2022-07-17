import os
import os
import random
import re
from datetime import datetime
from operator import or_
from pathlib import Path
from typing import Optional

from dateutil.relativedelta import relativedelta
from flask import g, current_app, request
from flask import url_for
from flask_mail import Message
from greensms.client import GreenSMS
from sqlalchemy import desc

from app import app, schemas, request_validator, db, mail
from app.models import Token, TokenPair, Device, Code, User, Notification, Flat, FlatPicture, Rent
from utils.auth import auth
from utils.auth import gen_token
from utils.helpers import make_response
from utils.helpers import save_file

for_request = request_validator.validate
json_mt = ['application/json']
form_mt = ['multipart/form-data']


def _dt(unix: Optional[int]):
    return datetime.fromtimestamp(unix) if unix is not None else None


def _unix(dt: Optional[datetime]) -> Optional[int]:
    return int(dt.timestamp()) if dt is not None else None


def _create_token_pair(user, device: Optional[str] = None):
    existing_tokens = list(token.value for token in Token.query.all())

    refresh_token_value = None
    access_token_value = None

    while refresh_token_value is None or refresh_token_value in existing_tokens:
        refresh_token_value = gen_token(64, '00')

    while access_token_value is None or access_token_value in existing_tokens:
        access_token_value = gen_token(64, '00')

    refresh_token = Token()
    refresh_token.value = refresh_token_value
    refresh_token.expires_at = datetime.utcnow() + relativedelta(days=60)
    refresh_token.commit()

    access_token = Token()
    access_token.value = access_token_value
    access_token.expires_at = datetime.utcnow() + relativedelta(hours=12)
    access_token.commit()

    pair = TokenPair()
    pair.user = user
    pair.device = device
    pair.access_token = access_token
    pair.refresh_token = refresh_token
    pair.commit()

    return access_token, refresh_token


def _update_settings(user, firebase_device_id, enable_notification, user_agent):
    device = Device.query.filter(Device.firebase_id == firebase_device_id).first()
    if device is not None:
        device.user_agent = user_agent
        device.enable_notification = enable_notification
        device.user = user
        device.commit()
    else:
        device = Device()
        device.firebase_id = firebase_device_id
        device.user_agent = user_agent
        device.enable_notification = enable_notification
        device.user = user
        device.commit()

    user.commit()


def _delete_user(user):
    db.session.delete(user)

    for ref in User.query.filter(User.referrer == user):
        ref.referrer = None
        db.session.add(ref)

    for device in Device.query.filter(Device.user == user):
        db.session.delete(device)

    for notification in Notification.query.filter(Notification.user == user):
        db.session.delete(notification)

    for pair in TokenPair.query.filter(TokenPair.user == user):
        db.session.delete(pair)
        if pair.access_token is not None:
            db.session.delete(pair.access_token)
        if pair.refresh_token is not None:
            db.session.delete(pair.refresh_token)

    db.session.commit()


def _get_user(user: User):

    return {
        'id': user.pk,
        'tel': user.tel,
        'avatar': user.avatar,
        'name': user.name,
        'surname': user.surname,
        'patronymic': user.patronymic,
        'passport_issued': user.passport_issued,
        'issue_date': user.issue_date,
        'department_code': user.department_code,
        'passport_series': user.passport_series,
        'passport_num': user.passport_num,
        'gender':user.gender,
        'birthdate': user.birthdate,
        'birthplace': user.birthplace,
        'passport_photo': user.passport_photo
    }



@app.route('/tels/verify/', methods=['POST'])
@for_request(
    allowed_content_types=json_mt,
    body_fields=schemas.with_tel()
)
def generate_verification_code():
    body = g.received.body

    tel_white_list = current_app.config.get(
        'TEL_WHITE_LIST',
        ['79184167161', '79183657351', '79914202022', '79897687220','79298341480']
    )

    pattern = re.compile(r"^7\d{10}$")

    if pattern.match(body.tel) is not None:

        if body.tel in tel_white_list:
            code_value = '8085'
        else:

            green_sms_user = current_app.config.get(
                'GREEN_SMS_LOGIN',
                'AXAS'
            )

            green_sms_password = current_app.config.get(
                'GREEN_SMS_PASSWORD',
                '5mWS142rzAgr'
            )

            client = GreenSMS(user=green_sms_user, password=green_sms_password)
            response = client.call.send(to=body.tel)
            code_value = response.code

    else:

        with mail.connect() as conn:

            code_value = ''.join(str(random.randint(0,9)) for _ in range(4))

            message = f'Your verification code is {code_value}'
            subject = "Verification in Axas Sharing"
            msg = Message(
                recipients=[body.tel],
                body=message,
                subject=subject,
                sender=('Axas Sharing Team', 'v.rudomakha@gmail.com')
            )

            conn.send(msg)

    code = Code()
    code.code = code_value
    code.target = body.tel
    code.expired_at = datetime.utcnow() + relativedelta(minutes=30)

    code.commit()

    return make_response(
        data={
            'code': code_value
        }
    )


@app.route('/siw/tel/', methods=['POST'])
@for_request(
    allowed_content_types=json_mt,
    body_fields=schemas.siw_tel()
)
def siw_tel():

    tel = g.received.body.tel

    codes = Code.query.filter(Code.target == tel).order_by(desc(Code.expired_at), Code.used).all()

    if len(codes) == 0:
        return make_response(
            status=401,
            message='Authorization denied',
            errors=[
                {
                    'code': 1,
                    'message': 'Verification code not created',
                    'source': 'tel',
                    'path': '$.body',
                    'additional': None
                }
            ],
            description='На указанный телефон не отправлялся код подтверждения'
        )

    codes_with_value = list(filter(lambda it: it.code == g.received.body.code, codes))

    if len(codes_with_value) == 0:
        return make_response(
            status=401,
            message='Authorization denied',
            errors=[
                {
                    'code': 2,
                    'message': 'Verification code dont match',
                    'source': 'tel',
                    'path': '$.body',
                    'additional': None
                }
            ],
            description='Код подтверждения не совпадает'
        )

    code = codes_with_value[0]

    if code.used:
        return make_response(
            status=401,
            message='Authorization denied',
            errors=[
                {
                    'code': 3,
                    'message': 'Verification code already used',
                    'source': 'tel',
                    'path': '$.body',
                    'additional': None
                }
            ],
            description='Код подтверждения уже использован'
        )

    if code.expired_at < datetime.utcnow():
        return make_response(
            status=401,
            message='Authorization denied',
            errors=[
                {
                    'code': 3,
                    'message': 'Verification code expired',
                    'source': 'tel',
                    'path': '$.body',
                    'additional': None
                }
            ],
            description='Время жизни кода подтверждения истекло'
        )

    code.used = True
    code.commit()

    user = User.query.filter(User.tel == tel).order_by(User.pk).first()

    if user is None:

        user = User()
        user.tel = tel
        user.commit()

    device = request.headers.get('device', None)
    user_agent = request.headers.get('User-Agent', None)
    enable_notifications = bool(request.headers.get('Enable-Notifications', True))

    _update_settings(
        user,
        user_agent=user_agent,
        firebase_device_id=device,
        enable_notification=enable_notifications,
    )

    db.session.commit()

    access_token, refresh_token = _create_token_pair(user, device)

    return make_response(
        status=200,
        data={
            'user': _get_user(user),
            'tokens': {
                'access': {
                    'value': access_token.value,
                    'expire_at': _unix(access_token.expires_at)
                },
                'refresh': {
                    'value': refresh_token.value,
                    'expire_at': _unix(refresh_token.expires_at)
                },
            }
        }
    )


@app.route('/settings/', methods=['PUT'])
@auth()
@for_request(
    allowed_content_types=json_mt,
    body_fields=schemas.editing_device()
)
def edit_settings():
    body = g.received.body
    user = g.user

    user_agent = request.headers.get('User-Agent', None)
    firebase_id = body.device
    enable_notifications = body.enable_notifications

    _update_settings(
        user,
        user_agent=user_agent,
        firebase_device_id=firebase_id,
        enable_notification=enable_notifications,
    )

    return make_response(
        data=[
            {
                'device': device.firebase_id,
                'enable_notifications': device.enable_notification,
                'user_agent': device.user_agent
            }
            for device in g.user.devices
        ]
    )


@app.route('/profile/', methods=['GET'])
@auth()
def get_profile():
    return make_response(data=_get_user(g.user))


@app.route('/profile/', methods=['PUT'])
@auth()
@for_request(
    allowed_content_types=json_mt,
    body_fields=schemas.edit_profile()
)
def edit_profile():
    user = g.user
    body = g.received.body

    for field in [
        'name',
        'passport_issued',
        'issue_date',
        'department_code',
        'passport_series',
        'passport_num',
        'surname',
        'patronymic',
        'gender',
        'birthdate',
        'birthplace',
    ]:
        if field in body:
            setattr(user, field, body[field])

    user.commit()

    return make_response(data=_get_user(user))


@app.route('/profile/avatar/', methods=['PUT'])
@auth()
@for_request(
    allowed_content_types=form_mt,
    body_fields=schemas.edit_profile_avatar()
)
def edit_profile_avatar():
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day

    directory = os.path.join("avatars", str(year), str(month), str(day))

    Path(directory).mkdir(parents=True, exist_ok=True)

    file = save_file(g.received.body.image, current_app.static_folder, directory)

    link = url_for('static', filename=file, _external=True)

    g.user.avatar = link

    db.session.add(g.user)
    db.session.commit()

    return make_response(data=_get_user(g.user))


@app.route('/profile/passport-photo/', methods=['PUT'])
@auth()
@for_request(
    allowed_content_types=form_mt,
    body_fields=schemas.edit_profile_avatar()
)
def edit_passport_photo():
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day

    directory = os.path.join("passports", str(year), str(month), str(day))

    Path(directory).mkdir(parents=True, exist_ok=True)

    file = save_file(g.received.body.image, current_app.static_folder, directory)

    link = url_for('static', filename=file, _external=True)

    g.user.passport_photo = link

    db.session.add(g.user)
    db.session.commit()

    return make_response(data=_get_user(g.user))


@app.route('/profile/tel/', methods=['PUT'])
@auth()
@for_request(
    allowed_content_types=json_mt,
    body_fields=schemas.siw_tel()
)
def edit_tel():
    tel = g.received.body.tel

    codes = Code.query.filter(Code.target == tel).order_by(desc(Code.expired_at), Code.used).all()

    if len(codes) == 0:
        return make_response(
            status=401,
            message='Authorization denied',
            errors=[
                {
                    'code': 1,
                    'message': 'Verification code not created',
                    'source': 'tel',
                    'path': '$.body',
                    'additional': None
                }
            ],
            description='На указанный телефон не отправлялся код подтверждения'
        )

    codes_with_value = list(filter(lambda it: it.code == g.received.body.code, codes))

    if len(codes_with_value) == 0:
        return make_response(
            status=401,
            message='Authorization denied',
            errors=[
                {
                    'code': 2,
                    'message': 'Verification code dont match',
                    'source': 'tel',
                    'path': '$.body',
                    'additional': None
                }
            ],
            description='Код подтверждения не совпадает'
        )

    code = codes_with_value[0]

    if code.used:
        return make_response(
            status=401,
            message='Authorization denied',
            errors=[
                {
                    'code': 3,
                    'message': 'Verification code already used',
                    'source': 'tel',
                    'path': '$.body',
                    'additional': None
                }
            ],
            description='Код подтверждения уже использован'
        )

    if code.expired_at < datetime.utcnow():
        return make_response(
            status=401,
            message='Authorization denied',
            errors=[
                {
                    'code': 3,
                    'message': 'Verification code expired',
                    'source': 'tel',
                    'path': '$.body',
                    'additional': None
                }
            ],
            description='Время жизни кода подтверждения истекло'
        )

    code.used = True
    code.commit()

    user = g.user

    user.tel = tel
    user.commit()

    return make_response(data=_get_user(user))


@app.route('/profile/', methods=['DELETE'])
@auth()
def delete_user():
    user = g.user

    _delete_user(user)

    return make_response()


def _get_flat(flat):

    now = datetime.utcnow()

    rent = db.session.query(Rent).filter(Rent.flat == flat,Rent.start_at < now, Rent.end_at > now).first()
    if rent is None:
        near_rent = now
    else:
        while True:
            near_rent = rent.end_at
            rent = db.session.query(Rent).filter(Rent.flat == flat,Rent.start_at == near_rent).first()
            if rent is None:
                break

    current_rent = db.session.query(Rent).filter(Rent.end_at > now).first()
    if current_rent is None:
        status = "Свободна"
    elif current_rent.start_at > now:
        status = "Забронирована"
    else:
        status = "Арендована"

    return {
        'id': flat.pk,
        'title': flat.title,
        'room_count': flat.room_count,
        'has_balcony': flat.has_balcony,
        'address': flat.address,
        'lat': flat.lat,
        'lon': flat.lon,
        'area': flat.area,
        'price_short': flat.price_short,
        'price_long': flat.price_long,
        'children': flat.children,
        'animals': flat.animals,
        'washing_machine': flat.washing_machine,
        'fridge': flat.fridge,
        'tv': flat.tv,
        'dishwasher': flat.dishwasher,
        'air_conditioner': flat.air_conditioner,
        'smoking': flat.smoking,
        'noise': flat.noise,
        'party': flat.party,
        'guest_count': flat.guest_count,
        'bed_count': flat.bed_count,
        'restroom_count': flat.restroom_count,
        "near_rent": _unix(near_rent),
        'pictures': [
            fp.link for fp in flat.pictures
        ],
        "status": status
    }


def _get_flat_short(flat):

    now = datetime.utcnow()

    rent = db.session.query(Rent).filter(Rent.flat == flat,Rent.start_at < now, Rent.end_at > now).first()
    if rent is None:
        near_rent = now
    else:
        while True:
            near_rent = rent.end_at
            rent = db.session.query(Rent).filter(Rent.flat == flat,Rent.start_at == near_rent).first()
            if rent is None:
                break

    current_rent = db.session.query(Rent).filter(Rent.end_at > now, Rent.flat == flat).first()
    if current_rent is None:
        status = "Свободна"
    elif current_rent.start_at > now:
        status = "Забронирована"
    else:
        status = "Арендована"

    return {
        'id': flat.pk,
        'title': flat.title,
        'address': flat.address,
        'price_short': flat.price_short,
        'price_long': flat.price_long,
        'pictures': [
            fp.link
            for fp
            in flat.pictures
        ],
        "lat": flat.lat,
        "lon": flat.lon,
        "near_rent": _unix(near_rent),
        "status": status
    }


@app.route('/flats/', methods=['POST'])
@auth()
@for_request(
    body_fields=schemas.create_flat(),
    allowed_content_types=json_mt
)
def create_flat():
    body = g.received.body
    flat = Flat()
    flat.user = g.user
    flat.room_count = body.room_count
    flat.has_balcony = body.has_balcony
    flat.has_loggia = body.has_balcony
    flat.address = body.address
    flat.lat = body.lat
    flat.lon = body.lon
    flat.area = body.area
    flat.price_short = body.price_short
    flat.price_long = body.price_long
    flat.children = body.children
    flat.animals = body.animals
    flat.washing_machine = body.washing_machine
    flat.fridge = body.fridge
    flat.tv = body.tv
    flat.dishwasher = body.dishwasher
    flat.air_conditioner = body.air_conditioner
    flat.smoking = body.smoking
    flat.noise = body.noise
    flat.party = body.party
    flat.title = body.title
    flat.guest_count = body.guest_count
    flat.bed_count = body.bed_count
    flat.restroom_count = body.restroom_count
    flat.commit()

    return make_response(
        data=_get_flat(flat)
    )


@app.route('/flats/<int:flat_id>/pictures/', methods=['POST'])
@auth()
@for_request(
    body_fields=schemas.edit_profile_avatar(),
    allowed_content_types=form_mt
)
def add_flat_picture(flat_id):
    flat = db.session.query(Flat).get(flat_id)
    if flat is None:
        return make_response(
            status=404,
            message='Entity not found',
            errors=[
                {
                    'code': 1,
                    'message': 'Entity not found',
                    'source': 'flat_id',
                    'path': '$.url',
                    'additional': None
                }
            ],
            description='Комната не найдена'
        )

    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day

    directory = os.path.join("flats", str(year), str(month), str(day))

    Path(directory).mkdir(parents=True, exist_ok=True)

    file = save_file(g.received.body.image, current_app.static_folder, directory)

    link = url_for('static', filename=file, _external=True)

    fp = FlatPicture()
    fp.flat = flat
    fp.link = link
    fp.commit()

    return make_response(
        data=_get_flat(flat)
    )


@app.route('/flats/', methods=['GET'])
@for_request(
    query_params=schemas.search()
)
def get_flat_list():

    query = db.session.query(Flat)

    for field in [
        'has_balcony',
        'has_loggia',
        'children',
        'animals',
        'washing_machine',
        'fridge',
        'tv',
        'dishwasher',
        'air_conditioner',
        'smoking',
        'noise',
        'party',

    ]:
        filter_value = g.received.query.get(field,'0')
        if filter_value == '1':
            query = query.filter_by(**{field:True})
        elif filter_value == '2':
            query = query.filter_by(**{field:False})

    search = g.received.query.get('search','')
    if len(search) > 0:
        query = query.filter(or_(Flat.title.ilike(f'%{search}%'),Flat.address.ilike(f'%{search}%')))

    return make_response(
        data=[
            _get_flat_short(flat)
            for flat in query
        ]
    )


@app.route('/flats/<int:flat_id>/', methods=['GET'])
def get_flat(flat_id):
    flat = db.session.query(Flat).get(flat_id)
    if flat is None:
        return make_response(
            status=404,
            message='Entity not found',
            errors=[
                {
                    'code': 1,
                    'message': 'Entity not found',
                    'source': 'flat_id',
                    'path': '$.url',
                    'additional': None
                }
            ],
            description='Комната не найдена'
        )

    return make_response(
        data=_get_flat(flat)
    )

def _get_rent(rent):

    now = datetime.utcnow()

    if rent.end_at < now:
        status = "Прошедшая"
    elif rent.start_at <= now <= rent.end_at:
        status = "Текущая"
    else:
        status = "Предстоящая"

    days = (rent.end_at - rent.start_at).days
    if days > 30:
        total_price = days * rent.flat.price_long
    else:
        total_price = days * rent.flat.price_long

    return {
        'id': rent.pk,
        'flat': _get_flat_short(rent.flat),
        'user':{
            'id': rent.user.pk,
            'tel': rent.user.tel,
            'surname': rent.user.surname,
            'name': rent.user.name,
            'patronymic': rent.user.patronymic
        },
        'start_at': _unix(rent.start_at),
        'end_at': _unix(rent.end_at),
        'total_price': total_price,
        'status':status
    }

@app.route('/flats/<int:flat_id>/rents/', methods=['POST'])
@auth()
@for_request(
    allowed_content_types=json_mt,
    body_fields=schemas.create_rent()
)
def create_rent(flat_id):
    flat = db.session.query(Flat).get(flat_id)
    if flat is None:
        return make_response(
            status=404,
            message='Entity not found',
            errors=[
                {
                    'code': 1,
                    'message': 'Entity not found',
                    'source': 'flat_id',
                    'path': '$.url',
                    'additional': None
                }
            ],
            description='Комната не найдена'
        )

    rent = Rent()
    rent.flat = flat
    rent.user = g.user
    body = g.received.body
    rent.start_at = _dt(body.start_at)
    rent.end_at = _dt(body.end_at)
    print(rent.commit())

    return make_response(
        data=_get_rent(rent)
    )


@app.route('/flats/me/', methods=['GET'])
@for_request(
    query_params=schemas.search()
)
@auth()
def get_my_flat_list():

    query = db.session.query(Flat).filter(Flat.user == g.user)

    for field in [
        'has_balcony',
        'has_loggia',
        'children',
        'animals',
        'washing_machine',
        'fridge',
        'tv',
        'dishwasher',
        'air_conditioner',
        'smoking',
        'noise',
        'party',

    ]:
        filter_value = g.received.query.get(field, '0')
        if filter_value == '1':
            query = query.filter_by(**{field:True})
        elif filter_value == '2':
            query = query.filter_by(**{field:False})

    search = g.received.query.get('search','')
    if len(search) > 0:
        query = query.filter(or_(Flat.title.ilike(f'%{search}%'),Flat.address.ilike(f'%{search}%')))

    return make_response(
        data=[
            _get_flat_short(flat)
            for flat in query
        ]
    )


@app.route('/flats/me/rents/', methods=['GET'])
@auth()
def get_my_rents():

    query = db.session.query(Rent).join(Flat).filter(Flat.user == g.user)

    return make_response(
        data=[
            _get_rent(rent)
            for rent in query
        ]
    )