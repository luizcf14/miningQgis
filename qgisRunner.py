import urllib.request
urllib.request.urlretrieve('https://raw.githubusercontent.com/luizcf14/miningQgis/main/MB7_mineracao.py', "mb7_temp.py")

exec(open("mb7_temp.py".encode('utf-8')).read())