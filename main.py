#import requests

#try:

#    response = requests.get('https://api.open-meteo.com/v1/forecast?latitude=55.7522&longitude=37.6156&hourly=temperature_2m,relative_humidity_2m,rain,showers,snowfall,surface_pressure,cloud_cover&timezone=Europe%2FMoscow',
#                        params = {'time','temperature_2m','relative_humidity_2m','rain','showers','snowfall','surface_pressure','cloud_cover'}
#    if response.status_code == 200:
#        data = response.json()

#for x in per:
#    print(x['name'])


import requests


def get_weather(city):

    url = f'https://api.open-meteo.com/v1/forecast?latitude=55.7522&longitude=37.6156&hourly=temperature_2m,relative_humidity_2m,rain,showers,snowfall,surface_pressure,cloud_cover&timezone=Europe%2FMoscow'



    response = requests.get(url)


    if response.status_code == 200:
        data = response.json()


        city_name = data['location']['name']
        country = data['location']['country']
        temperature = data['current']['temperature']
        weather_description = data['current']['weather_descriptions'][0]

        # Выводим информацию о погоде
        print(f"Погода в городе {city_name}, {country}:")
        print(f"Температура: {temperature}°C")
        print(f"Описание: {weather_description}")
    else:
        print(f"Ошибка при запросе данных: {response.status_code}")

# Запрашиваем название города у пользователя
city = input("Введите название города: ")

# Получаем и отображаем погоду
get_weather(city)