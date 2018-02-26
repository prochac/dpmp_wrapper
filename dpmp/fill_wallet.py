import requests
from bs4 import BeautifulSoup

SERVER = 'https://ifc.emlines.com'
DPMP = '/dpmp/'
GPWEBPAY = 'https://3dsecure.gpwebpay.com/pgw/order.do'


def prepare_fill_wallet(cookies):
    res = requests.get(SERVER + DPMP + 'FillWallet.aspx', cookies=cookies)
    bs = BeautifulSoup(res.text, 'html.parser')
    view_state = bs.find(id='__VIEWSTATE')['value']
    return view_state


def next_fill_wallet(cookies, view_state, amount, email):
    data = {
        '__VIEWSTATE': view_state,
        '__VIEWSTATEENCRYPTED': '',
        'ctl01$uxMainContentPlaceHolder$AmountTextBox': amount,
        'ctl01$uxMainContentPlaceHolder$uxEmailTxt': email,
        'kindRadio': '2',
        'ctl01$uxMainContentPlaceHolder$PaymentKindChooser$BrandTypeHiddenField': '0',
        'ctl01$uxMainContentPlaceHolder$chckAgree': 'on',
        'ctl01$uxMainContentPlaceHolder$uxFirstStepNextBtn': 'Dále',
    }
    res = requests.post(SERVER + DPMP + 'FillWallet.aspx', cookies=cookies, data=data)
    bs = BeautifulSoup(res.text, 'html.parser')
    view_state = bs.find(id='__VIEWSTATE')['value']
    table = bs.find(id='ctl01_uxMainContentPlaceHolder_responseTable')
    if table:
        return view_state
    else:
        return None


def confirm_fill_wallet(cookies, view_state):
    data = {
        '__VIEWSTATE': view_state,
        '__VIEWSTATEENCRYPTED': '',
        'ctl01$uxMainContentPlaceHolder$BtnConfirm': 'Potvrdit',
        'ctl01$uxMainContentPlaceHolder$uxSelectedPaymentHdf': '2',
    }
    res = requests.post(SERVER + DPMP + 'FillWallet.aspx', cookies=cookies, data=data)
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
