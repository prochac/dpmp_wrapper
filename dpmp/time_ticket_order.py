import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

SERVER = 'https://ifc.emlines.com'
DPMP = '/dpmp/'
GPWEBPAY = 'https://3dsecure.gpwebpay.com/pgw/order.do'


def get_delta_from_tariff(tariff):
    return {
        # DPMP
        "509000009": relativedelta(days=+6),
        "509000010": relativedelta(days=+13),
        "509000011": relativedelta(days=+29),
        "509000012": relativedelta(days=+89),
        "509000132": relativedelta(days=+179),
        "509000014": relativedelta(days=+364),
        # DPMHK
        "508000042": relativedelta(days=+6),
        "508000044": relativedelta(months=+1, days=-1),
        "508000045": relativedelta(months=+3, days=-1),
        "508000038": relativedelta(months=+6, days=-1),
        "508000037": relativedelta(years=+1, days=-1),
    }[tariff]


def prepare_time_ticket_order(cookies):
    res = requests.get(SERVER + DPMP + 'TimeTicketOrder.aspx', cookies=cookies)
    bs = BeautifulSoup(res.text, 'html.parser')
    view_state = bs.find(id='__VIEWSTATE')['value']
    return view_state


def set_tariff_time_ticket_order(cookies, view_state, tariff):
    data_ = {
        'ctl01$ToolkitScriptManager1': 'ctl01$uxMainContentPlaceHolder$UppTimeTicketOrder|ctl01$uxMainContentPlaceHolder$DdlTarifs',
        '__VIEWSTATE': view_state,
        '__VIEWSTATEENCRYPTED': '',
        'ctl01$uxMainContentPlaceHolder$DdlTarifs': tariff,
    }
    res = requests.post(SERVER + DPMP + 'TimeTicketOrder.aspx', cookies=cookies, data=data_)
    bs = BeautifulSoup(res.text, 'html.parser')

    view_state = bs.find(id='__VIEWSTATE')['value']
    return view_state


def set_zone_time_ticket_order(cookies, view_state, zone):
    data_ = {
        'ctl01$ToolkitScriptManager1': 'ctl01$uxMainContentPlaceHolder$UppTimeTicketOrder|ctl01$uxMainContentPlaceHolder$DdlTarifs',
        '__VIEWSTATE': view_state,
        '__VIEWSTATEENCRYPTED': '',
        'ctl01$uxMainContentPlaceHolder$DdlZones': zone,
    }
    res = requests.post(SERVER + DPMP + 'TimeTicketOrder.aspx', cookies=cookies, data=data_)
    bs = BeautifulSoup(res.text, 'html.parser')

    view_state = bs.find(id='__VIEWSTATE')['value']
    value = bs.find(id='ctl01_uxMainContentPlaceHolder_PriceTextBox')['value']

    return view_state, value


def set_date_from_time_ticket_order(cookies, view_state, date_from):
    data_ = {
        'ctl01$ToolkitScriptManager1': 'ctl01$uxMainContentPlaceHolder$UppTimeTicketOrder|ctl01$uxMainContentPlaceHolder$TxtFrom',
        '__VIEWSTATE': view_state,
        '__VIEWSTATEENCRYPTED': '',
        'ctl01$uxMainContentPlaceHolder$TxtFrom': date_from,
    }
    res = requests.post(SERVER + DPMP + 'TimeTicketOrder.aspx', cookies=cookies, data=data_)
    bs = BeautifulSoup(res.text, 'html.parser')

    view_state = bs.find(id='__VIEWSTATE')['value']
    value = None
    if bs.find(id='ctl01_uxMainContentPlaceHolder_AnotherPCLWarningLbl'):
        value = bs.find(id='ctl01_uxMainContentPlaceHolder_AnotherPCLWarningLbl').text

    return view_state, value


def next_time_ticket_order(cookies, view_state, email, date_from, date_to, check_remind, days_remind='3'):
    data = {
        'ctl01$ToolkitScriptManager1': 'ctl01$uxMainContentPlaceHolder$UppTimeTicketOrder|ctl01$uxMainContentPlaceHolder$BtnNext',
        'ctl01$uxMainContentPlaceHolder$TxtEmail': email,
        'ctl01$uxMainContentPlaceHolder$EmailReminderCheckBox': 'on' if check_remind else '',
        'ctl01$uxMainContentPlaceHolder$EmailReminderTextBox': days_remind,
        'kindRadio': '2',
        'ctl01$uxMainContentPlaceHolder$PaymentKindChooser$BrandTypeHiddenField': '0',
        'ctl01$uxMainContentPlaceHolder$chckAgree': 'on',
        'ctl01$uxMainContentPlaceHolder$ValidFromHiddenField': date_from,
        'ctl01$uxMainContentPlaceHolder$ValidToHiddenField': date_to,
        '__VIEWSTATE': view_state,
        '__VIEWSTATEENCRYPTED': '',
        'ctl01$uxMainContentPlaceHolder$BtnNext': 'Dále',
    }
    res = requests.post(SERVER + DPMP + 'TimeTicketOrder.aspx', cookies=cookies, data=data)
    bs = BeautifulSoup(res.text, 'html.parser')

    view_state = bs.find(id='__VIEWSTATE')['value']
    card_no = bs.find(id='ctl01_uxMainContentPlaceHolder_responseTable').caption.strong.text
    recap_tariff = bs.find(id='ctl01_uxMainContentPlaceHolder_rProductName').find_all('td')[1].text
    recap_zone = bs.find(id='ctl01_uxMainContentPlaceHolder_rZone').find_all('td')[1].text
    recap_date = bs.find(id='ctl01_uxMainContentPlaceHolder_rValidity').find_all('td')[1].text

    return view_state, card_no, recap_tariff, recap_zone, recap_date


def confirm_time_ticket_order(cookies, view_state, email, date_from, date_to):
    data = {
        'ctl01$ToolkitScriptManager1': 'ctl01$uxMainContentPlaceHolder$UppTimeTicketOrder|ctl01$uxMainContentPlaceHolder$BtnConfirm',
        'ctl01$uxMainContentPlaceHolder$TxtEmail': email,
        'ctl01$uxMainContentPlaceHolder$PaymentValidatorPlace': '',
        'kindRadio': '2',
        'ctl01$uxMainContentPlaceHolder$chckAgree': 'on',
        'ctl01$uxMainContentPlaceHolder$ValidFromHiddenField': date_from,
        'ctl01$uxMainContentPlaceHolder$ValidToHiddenField': date_to,
        '__VIEWSTATE': view_state,
        '__VIEWSTATEENCRYPTED': '',
        'ctl01$uxMainContentPlaceHolder$BtnConfirm': 'Potvrdit',
    }

    res = requests.post(SERVER + DPMP + 'TimeTicketOrder.aspx', cookies=cookies, data=data)
    bs = BeautifulSoup(res.text, 'html.parser')
    url = GPWEBPAY
    form = [
        ('MERCHANTNUMBER', bs.find(id='MERCHANTNUMBER')['value']),
        ('OPERATION', bs.find(id='OPERATION')['value']),
        ('ORDERNUMBER', bs.find(id='ORDERNUMBER')['value']),
        ('AMOUNT', bs.find(id='AMOUNT')['value']),
        ('CURRENCY', bs.find(id='CURRENCY')['value']),
        ('DEPOSITFLAG', bs.find(id='DEPOSITFLAG')['value']),
        ('URL', bs.find(id='URL')['value']),
        ('DESCRIPTION', bs.find(id='DESCRIPTION')['value']),
        ('DIGEST', bs.find(id='DIGEST')['value']),
    ]
    return form, url
