import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

SERVER = 'https://ifc.emlines.com'
DPMP = '/dpmp/'

CARD_NO = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_uxSnrValueLbl'
CREDIT_AMOUNT = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_CardBalanceValueLabel'
CREDIT_TO_DATE = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_CardBalanceTitleLabel'
EXPIRE = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_CardValidityValueLabel'
DISCOUNT_DATE = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_DiscountValidityValueLabel'
CARD_TYPE = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_CardTypeValueLabel'
WAITING_OPERATIONS = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_WaitingOperationsValueLabel'

TIME_TICKET_PANEL = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_ucValidTimeTicket_ValidTimeTicketPanel'
NO_TIME_TICKET = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_ucValidTimeTicket_uxNoValidTimeTicketLbl'
TIME_TICKET_ZONA = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_ucValidTimeTicket_uxValidTimeTicketRpt_ctl{:02}_ZoneLabel'
TIME_TICKET_FROM = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_ucValidTimeTicket_uxValidTimeTicketRpt_ctl{:02}_Label3'
TIME_TICKET_TO = 'ctl01_uxMainContentPlaceHolder_ucCardInfo_ucValidTimeTicket_uxValidTimeTicketRpt_ctl{:02}_Label4'


def prepare_login():
    res = requests.get(SERVER + DPMP + 'TimeTicketOrder.aspx')
    bs = BeautifulSoup(res.text, 'html.parser')

    captcha = {
        'img_url': SERVER + DPMP + bs.find(id='ctl01_uxMainContentPlaceHolder_uxCheckCardUc_ucHumanFilter_ImageCode')[
            'src']
    }
    captcha['img_number'] = parse_qs(urlparse(captcha['img_url']).query)['Code'][0]

    cookies = res.cookies.get_dict()

    view_state = bs.find(id='__VIEWSTATE')['value']

    return cookies, view_state, captcha


def get_card_info(cookies, view_state, card_no, captcha_code):
    data = {
        '__VIEWSTATE': view_state,
        '__VIEWSTATEENCRYPTED': '',
        'ctl01$uxMainContentPlaceHolder$uxCheckCardUc$uxCardSNRTxt': card_no,
        'ctl01$uxMainContentPlaceHolder$uxCheckCardUc$ucHumanFilter$TextBoxCode': captcha_code,
        'ctl01$uxMainContentPlaceHolder$uxCheckCardUc$uxCheckBtn': 'Zkontrolovat kartu',
    }
    res = requests.post(SERVER + DPMP + 'TimeTicketOrder.aspx', cookies=cookies, data=data)
    bs = BeautifulSoup(res.text, 'html.parser')
    try:
        time_tickets = []
        if not bs.find(id=NO_TIME_TICKET):
            for i, table in enumerate(bs.find(id=TIME_TICKET_PANEL).find_all(class_='validTicketTable')):
                time_tickets.append([
                    table.find('tr').find_all('th')[1].text.strip(),  # name
                    bs.find(id=TIME_TICKET_ZONA.format(i)).text.strip(),  # zone
                    bs.find(id=TIME_TICKET_FROM.format(i)).text.strip(),  # from
                    bs.find(id=TIME_TICKET_TO.format(i)).text.strip(),  # to
                    (datetime.strptime(
                        bs.find(id=TIME_TICKET_FROM.format(i)).b.next_sibling.strip(),
                        "%d.%m.%Y") < datetime.now() and datetime.strptime(
                        bs.find(id=TIME_TICKET_TO.format(i)).b.next_sibling.strip(),
                        "%d.%m.%Y") > datetime.now()),  # valid
                ])
        card_info = [
            (
                'Číslo karty',
                bs.find(id=CARD_NO).text,
                False
            ),
            (
                'Zůstatek',
                bs.find(id=CREDIT_AMOUNT).text,
                float(bs.find(id=CREDIT_AMOUNT).text.strip(' Kč').replace(',', '.')) <= 0
            ),
            (
                'Zůstatek na kartě ke dni',
                bs.find(id=CREDIT_TO_DATE).span.text,
                False
            )]
        if bs.find(id=WAITING_OPERATIONS).text:
            card_info.extend([
                (
                    'Čekající operace',
                    bs.find(id=WAITING_OPERATIONS).text,
                    False
                )
            ])
        card_info.extend([
            (
                'Platná do',
                bs.find(id=EXPIRE).text,
                datetime.strptime(bs.find(id=EXPIRE).text, "%d.%m.%Y") < (datetime.now() - timedelta(days=10))
            ),
            (
                'Typ karty',
                bs.find(id=CARD_TYPE).text,
                False
            ),
        ])
        if bs.find(id=DISCOUNT_DATE):
            card_info.extend([
                (
                    'Sleva na kartě platná do',
                    bs.find(id=DISCOUNT_DATE).text,
                    datetime.strptime(bs.find(id=DISCOUNT_DATE).text, "%d.%m.%Y") < datetime.now()
                )
            ])
        return card_info, time_tickets
    except AttributeError:
        return None, None
