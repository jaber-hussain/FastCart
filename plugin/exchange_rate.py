from decimal import Decimal
import requests

def fetch_exchange_rates():
    response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
    data = response.json()
    return {
        'INR': Decimal(data['rates']['INR']),
        'NGN': Decimal(data['rates']['NGN']),
        'PKR': Decimal(data['rates'].get('PKR', 0))
    }

exchange_rates = fetch_exchange_rates()

def get_usd_to_inr_rate():
    return exchange_rates['INR']

def get_usd_to_ngn_rate():
    return exchange_rates['NGN']

def get_usd_to_pkr_rate():
    return exchange_rates['PKR']

def convert_usd_to_inr(usd_amount):
    inr_rate = get_usd_to_inr_rate()
    return usd_amount * inr_rate

def convert_usd_to_kobo(usd_amount):
    ngn_rate = get_usd_to_ngn_rate()
    ngn_amount = usd_amount * ngn_rate
    return int(ngn_amount * 100)  # Convert NGN to Kobo

def convert_usd_to_ngn(usd_amount):
    ngn_rate = get_usd_to_ngn_rate()
    return usd_amount * ngn_rate

def convert_usd_to_pkr(usd_amount):
    pkr_rate = get_usd_to_pkr_rate()
    return usd_amount * pkr_rate