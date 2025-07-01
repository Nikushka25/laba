import requests

params = {
    'page':1,
    'per_page':3
}

response = requests.get('https://api.github.com/repos/Nikushka25/laba/tags', params = params)
if response.status_code == 200:
    per = response.json()

for x in per:
    print(x['name'])