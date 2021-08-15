import requests
payload = {
    "token": "sk_9f6274ec2b0140d2837fd35581a96f64"
}
stock = 'aapl'
info = requests.get(f'https://cloud.iexapis.com/stable/stock/{stock}/company', params=payload)
print(info.json())