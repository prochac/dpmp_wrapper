from flask import Flask
from flask import session
from flask import make_response
from flask import render_template
from flask import url_for
from flask import redirect
from flask import request
from flask import send_file
from dpmp.card_info import prepare_login
from dpmp.card_info import get_card_info
from dpmp.fill_wallet import prepare_fill_wallet
from dpmp.fill_wallet import next_fill_wallet
from dpmp.fill_wallet import confirm_fill_wallet
from dpmp.time_ticket_order import get_delta_from_tariff
from dpmp.time_ticket_order import prepare_time_ticket_order
from dpmp.time_ticket_order import set_tariff_time_ticket_order
from dpmp.time_ticket_order import set_zone_time_ticket_order
from dpmp.time_ticket_order import set_date_from_time_ticket_order
from dpmp.time_ticket_order import next_time_ticket_order
from dpmp.time_ticket_order import confirm_time_ticket_order
import json
from datetime import datetime
from datetime import timedelta
import captcha_breaker

app = Flask(__name__)


@app.before_request
def make_session_permanent():
    session.permanent = True


with app.open_resource('secret_key.txt', 'rb') as f:
    app.secret_key = f.read()


@app.route("/")
def index():
    if 'active_card' in session:
        return redirect(url_for('card_info', utm_source=request.args.get('utm_source')))
    else:
        return redirect(url_for('login', utm_source=request.args.get('utm_source')))


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('active_card', None)
    if request.method == 'GET':
        last_card = session.get('last_card', None)
        if not last_card:
            last_card = ''

        render_data = {
            'page_name': 'Přihlášení',
            'menu_rows': load_drawer_data(),
            'toast_message': request.args.get('toast_message'),
            'last_card': last_card,
            'utm_source': request.args.get('utm_source'),
        }
        resp = make_response(render_template('login.jinja2', **render_data))
        return resp

    if request.method == 'POST':
        card_no = request.form.get('card_no')
        if not card_no:
            return redirect(url_for('login', toast_message='Chyba&nbsp;přihlášení!'))
        session['last_card'] = card_no
        session['active_card'] = {
            'card_no': card_no,
            'dpmp_cookies': None,
        }
        resp = make_response(redirect(url_for('card_info')))
        return resp


@app.route("/card-info")
def card_info():
    active_card = session.get('active_card', None)
    if not active_card:
        return redirect(url_for('login'))

    for x in range(5):
        cookies, view_state, captcha = prepare_login()

        captcha_code = captcha_breaker.get_captcha(captcha['img_url'])
        card_info_data, time_tickets = get_card_info(cookies, view_state, active_card['card_no'], captcha_code)
        if card_info_data:
            session['active_card']['dpmp_cookies'] = cookies
            session['active_card'] = session['active_card']
            break
        print('{}. chyba'.format(x + 1))
    else:
        return redirect(url_for('login', toast_message='Chyba&nbsp;přihlášení!'))

    render_data = {
        'page_name': 'Informace o kartě',
        'toast_message': request.args.get('toast_message'),
        'menu_rows': load_drawer_data(),
        'card_info_data': card_info_data,
        'time_tickets': time_tickets,
        'utm_source': request.args.get('utm_source'),
    }
    resp = make_response(render_template('card_info.jinja2', **render_data))
    return resp


@app.route("/time-ticket-order", methods=['GET', 'POST'])
def time_ticket_order():
    if request.method == 'GET':
        render_data = {
            'page_name': 'Objednání časové jízdenky',
            'menu_rows': load_drawer_data(),
            'toast_message': request.args.get('toast_message'),
            'tomorrow': (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'date_from': (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d'),

            'last_tariff': session.get('last_tariff', ''),
            'last_zone': session.get('last_zone', ''),
            'last_check_remind': session.get('last_check_remind', ''),
            'last_days_remind': session.get('last_days_remind', ''),
            'last_email': session.get('last_email', ''),
            'last_agreed': session.get('last_agreed', ''),
        }
        resp = make_response(render_template('time_ticket_order.jinja2', **render_data))
        return resp

    if request.method == 'POST':
        if not request.form.get('check_agree') or \
                not request.form.get('tariff') or \
                not request.form.get('zone') or \
                not request.form.get('date_from') or \
                not request.form.get('email') or \
                not request.form.get('email_reminder_days'):
            render_data = {
                'page_name': 'Objednání časové jízdenky',
                'menu_rows': load_drawer_data(),
                'toast_message': 'Vyplňte&nbsp;všechna&nbsp;pole',
                'tomorrow': (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'date_from': (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d'),

                'last_tariff': session.get('last_tariff', ''),
                'last_zone': session.get('last_zone', ''),
                'last_check_remind': session.get('last_check_remind', ''),
                'last_days_remind': session.get('last_days_remind', ''),
                'last_email': session.get('last_email', ''),
                'last_agreed': session.get('last_agreed', ''),
            }
            resp = make_response(render_template('time_ticket_order.jinja2', **render_data))
            return resp

        active_card = session.get('active_card', None)
        if not active_card:
            return redirect(url_for('login'))
        cookies = active_card['dpmp_cookies']

        tariff = request.form.get('tariff')
        zone = request.form.get('zone')
        date_from = datetime.strptime(request.form.get('date_from'), '%Y-%m-%d')
        date_to = date_from + get_delta_from_tariff(tariff)
        check_remind = 'on' if request.form.get('email_reminder') else ''
        days_remind = request.form.get('email_reminder_days')
        email = request.form.get('email')
        date_from = date_from.strftime('%d.%m.%Y 0:00:00')
        date_to = date_to.strftime('%d.%m.%Y 0:00:00')

        view_state = prepare_time_ticket_order(cookies)
        view_state = set_tariff_time_ticket_order(cookies, view_state, tariff)
        view_state, amount = set_zone_time_ticket_order(cookies, view_state, zone)
        view_state, warning = set_date_from_time_ticket_order(cookies, view_state, date_from)

        view_state, card_no, recap_tariff, recap_zone, recap_date = next_time_ticket_order(cookies, view_state,
                                                                                           email, date_from,
                                                                                           date_to,
                                                                                           check_remind,
                                                                                           days_remind)

        form, url = confirm_time_ticket_order(cookies, view_state, email, date_from, date_to)

        session['last_tariff'] = tariff
        session['last_zone'] = zone
        session['last_check_remind'] = request.form.get('email_reminder')
        session['last_days_remind'] = request.form.get('reminder_days')
        session['last_email'] = email
        session['last_agreed'] = datetime.now().strftime('%Y%m%d%H%M%S')

        render_data = {
            'page_name': 'Objednání časové jízdenky',
            'info_data': [
                ('Č.karty', card_no),
                ('Typ předplatné časové jízdenky', recap_tariff),
                ('Tarifní zóna', recap_zone),
                ('Platnst', recap_date),
                ('Cena', amount),
                ('Email', email)
            ],
            'form_data': form,
            'url': url,
            'back_url': '/time-ticket-order',
            'toast_message': warning,
        }
        resp = make_response(render_template('payment_redirect.jinja2', **render_data))
        return resp


@app.route("/fill-wallet", methods=['GET', 'POST'])
def fill_wallet():
    if request.method == 'GET':
        render_data = {
            'page_name': 'Plnění peněženky',
            'menu_rows': load_drawer_data(),
            'toast_message': request.args.get('toast_message'),

            'last_amount': session.get('last_amount', ''),
            'last_email': session.get('last_email', ''),
            'last_agreed': session.get('last_agreed', ''),
        }
        resp = make_response(render_template('fill_wallet.jinja2', **render_data))
        return resp
    if request.method == 'POST':
        if not request.form.get('check_agree') or \
                not request.form.get('amount') or \
                not request.form.get('email'):
            render_data = {
                'page_name': 'Plnění peněženky',
                'menu_rows': load_drawer_data(),
                'toast_message': 'Vyplňte&nbsp;všechna&nbsp;pole',

                'last_amount': session.get('last_amount', ''),
                'last_email': session.get('last_email', ''),
                'last_agreed': session.get('last_agreed', ''),
            }
            resp = make_response(render_template('fill_wallet.jinja2', **render_data))
            return resp

        active_card = session.get('active_card', None)
        if not active_card:
            return redirect(url_for('login'))
        cookies = active_card['dpmp_cookies']

        amount = request.form.get('amount')
        email = request.form.get('email')

        view_state = prepare_fill_wallet(cookies)
        view_state = next_fill_wallet(cookies, view_state, amount, email)
        form, url = confirm_fill_wallet(cookies, view_state)

        session['last_amount'] = amount
        session['last_email'] = email
        session['last_agreed'] = datetime.now().strftime('%Y%m%d%H%M%S')

        render_data = {
            'page_name': 'Plnění peněženky',
            'info_data': [
                ('č.karty', active_card['card_no']),
                ('částka', request.form.get('amount')),
                ('email', request.form.get('email'))
            ],
            'form_data': form,
            'url': url,
            'back_url': '/fill-wallet',
        }
        resp = make_response(render_template('payment_redirect.jinja2', **render_data))
        return resp


@app.route("/sms-ticket")
def sms_ticket():
    render_data = {
        'page_name': 'SMS Jízdenka',
        'menu_rows': load_drawer_data(),
        'logged_in': bool(session.get('active_card', None)),
        'toast_message': request.args.get('toast_message'),
    }
    if request.args.get('offline'):
        render_data['toast_message'] = '<i class="material-icons">cloud_off</i>&nbsp;Jsi&nbsp;offline'
    resp = make_response(render_template('sms-ticket.jinja2', **render_data))
    return resp


@app.route("/logout")
def logout():
    session.pop('active_card', None)
    resp = make_response(redirect(url_for('index')))
    return resp


@app.route("/about")
def about():
    render_data = {
        'page_name': 'O aplikaci',
        'menu_rows': load_drawer_data(),
        'toast_message': request.args.get('toast_message'),
    }
    resp = make_response(render_template('about.jinja2', **render_data))
    return resp


@app.route("/offline")
def offline():
    render_data = {
        'page_name': 'Offline',
        'menu_rows': load_drawer_data(),
        'toast_message': request.args.get('toast_message'),
    }
    resp = make_response(render_template('offline.jinja2', **render_data))
    return resp


@app.route("/pwabuilder-sw.js")
def service_worker():
    return send_file('static/pwabuilder-sw.js')


@app.route("/loaderio-9340547bc834a90db64286c742b06d24")
@app.route("/loaderio-9340547bc834a90db64286c742b06d24.txt")
@app.route("/loaderio-9340547bc834a90db64286c742b06d24.html")
def loaderio():
    return "loaderio-9340547bc834a90db64286c742b06d24"


def load_drawer_data():
    show = 'logged' if session.get('active_card', None) else 'unlogged'
    drawer_data = []
    with app.open_resource('templates/drawer_data.json', 'r') as f:
        for drawer_data_row in json.load(f):
            if show not in drawer_data_row['show']:
                continue
            if str(request.url_rule) == drawer_data_row['url']:
                drawer_data_row['active'] = True

            drawer_data.append(drawer_data_row)
    return drawer_data


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
