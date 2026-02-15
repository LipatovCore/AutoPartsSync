import os
import requests

from django.shortcuts import render
from django.conf import settings

def search_article(article, brand):
    results = {}

    abcp_url = os.getenv("ABCP_URL")
    abcp_user = os.getenv("ABCP_USER")
    abcp_pass = os.getenv("ABCP_PASS")

    url = f"https://{abcp_url}/search/articles/"
    params = {
        "userlogin": abcp_user,
        "userpsw": abcp_pass,
        "number": article,
        "brand": brand,
        "useOnlineStocks": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # print(data)

        for item in data:
            if not item['number'] in results:
                results[item['number']] = {"brand": item['brand']}

    except requests.RequestException as e:
        print(f"ABCP request error: {e}")

    return results


def ms_assort(data):
    token = os.getenv("MS_TOKEN")
    url = "https://api.moysklad.ru/api/remap/1.2/entity/assortment?filter="
    headers = {
        'Authorization': f'Bearer {token}' 
    }
    
    for article in list(data):
        url += "article=" + article + ";"
        
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        
        # Вызов raise_for_status() выбросит исключение для кодов 4xx/5xx
        response.raise_for_status()
        
        for item in response.json()["rows"]:
            if 'article' in item and 'code' in item:
                if item['article'] == item['code']:
                    data[item['article']]['id'] = item['id']
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении GET-запроса: {e}")
    
    return data

def search_ms(data):
        token = os.getenv("MS_TOKEN")
        data = ms_assort(data)

        url = "https://api.moysklad.ru/api/remap/1.2/report/stock/all/current?filter=storeId=17cfc07f-d1be-11e7-7a34-5acf00029692&filter=assortmentId="
        headers = {
            'Authorization': f'Bearer {token}' 
        }
        
        
        for elem in list(data):
            if 'id' in data[elem]:
                url += data[elem]['id'] + ","
                         
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )
            
            # Вызов raise_for_status() выбросит исключение для кодов 4xx/5xx
            response.raise_for_status()
            
            for item in list(data):
                if 'id' in data[item]:
                    for count in response.json():
                        if data[item]['id'] == count['assortmentId']:
                            data[item]['stock'] = count['stock']
                            break
                    if not 'stock' in data[item]:
                        data[item]['stock'] = 0
                else:
                    data[item]['stock'] = '-'
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении GET-запроса: {e}")
        
        return data


def search(request):
    results = []
    query = ""

    if request.method == "GET":
        query = request.GET.get("search", "").strip()

        if query:
            abcp_url = os.getenv("ABCP_URL")
            abcp_user = os.getenv("ABCP_USER")
            abcp_pass = os.getenv("ABCP_PASS")

            url = f"https://{abcp_url}/search/brands/"
            params = {
                "userlogin": abcp_user,
                "userpsw": abcp_pass,
                "number": query,
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                if len(list(data.keys())) == 1:
                    results = search_article(query, data[list(data.keys())[0]]["brand"])
                    results = search_ms(results)
                # results.append(data[list(data.keys())[0]]["brand"])
                # for key in data.keys():
                #     if "brand" in item:
                #         results.append(item["brand"])

            except requests.RequestException as e:
                print(f"ABCP request error: {e}")

    context = {
        "query": query,
        "results": results,
    }

    return render(request, "search.html", context)
