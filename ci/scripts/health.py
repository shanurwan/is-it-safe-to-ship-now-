import requests, sys
r = requests.get('http://localhost:9090/api/v1/query', params={'query':'job:http_5xx_rate'})
print(r.json())
