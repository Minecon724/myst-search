from flask import Flask, render_template, request
from requests import get
from random import choice
from json import load
import string

app = Flask(__name__, static_url_path='', static_folder='public/static', template_folder='public')

icons = {
  "residential": "fa-house-chimney",
  "hosting": "fa-server",
  "business": "fa-house-chimney",
  "education": "fa-school",
  "celluar": "fa-house-chimney",
  "organization": "fa-building-ngo",
  "content_delivery_network": "fa-server",
  "government": "fa-landmark-flag",
  "college": "fa-school",
  "unknown": "fa-block-question"
}

types = ["residential", "hosting", "business", "education", "celluar", "organization", "content_delivery_network", "government", "college", "unknown"]

country_map = {}

avail_countries = get("https://discovery.mysterium.network/api/v3/countries").json()
for i in load(open('slim-2.json')):
  if i['alpha-2'] in avail_countries:
    country_map[i['name'].lower().replace(' ', '')] = i['alpha-2']

def get_ip_icon(type):
  if not type in icons:
    return "fa-block-question"
  return icons[type]

def get_speed_icon(speed):
  if speed < 10:
    return "fa-tractor"
  elif speed < 30:
    return "fa-bus-simple"
  elif speed < 70:
    return "fa-wifi"
  elif speed < 150:
    return "fa-ethernet"
  return "fa-bolt"

def scan_types(query:str):
  allowed = []
  query = query.lower().replace(' ', '')
  if "residential" in query:
    allowed += ["residential", "business", "education", "celluar", "organization", "government", "college"]
  if "hosting" in query or "datacenter" in query:
    allowed += ["hosting", "content_delivery_network"]
  if "school" in query or "college" in query or "education" in query:
    allowed += ["education", "college"]
  for i in types:
    if not i in allowed:
      if i in query:
        allowed.append(i)
  return allowed

def scan_speed(query:str):
  minimum = 0
  query = query.lower().replace(' ', '')
  if "fast" in query:
    minimum = 100
  if "gigabit" in query:
    minimum = 1000
  return minimum

def scan_countries(query:str):
  allowed = []
  query = query.lower().replace(' ', '')
  for i in country_map:
    if i in query:
      allowed.append(country_map[i])
  return allowed

@app.route('/')
def home():
  query = request.args.get('query', default="", type=str)
  req = get(f"https://discovery.mysterium.network/api/v3/proposals").json()
  types_allowed = types.copy()
  speed_minimum = 0
  countries = country_map.values()
  if query != "":
    types_allowed = scan_types(query)
    if len(types_allowed) == 0: types_allowed = types.copy()
    speed_minimum = scan_speed(query)
    countries = scan_countries(query)
    print(countries)
    if len(countries) == 0: countries = country_map.values()
  if req is None: return "Something went wrong"
  nodes = []
  c = 0
  for i in req:
    loc = i['location']
    ip_type = loc['ip_type'] if 'ip_type' in loc else "unknown"
    if not ip_type in types_allowed or i['quality']['bandwidth'] <= speed_minimum:
      continue
    if not ('country' in loc and loc['country'] in countries):
      continue
    nodes.append({
      'id': i['provider_id'],
      'short': i['provider_id'][:6] + '...',
      'type': ip_type.capitalize(),
      'city': loc['city'] if 'city' in loc else "Unknown",
      'country': loc['country'] if 'country' in loc else "Unknown",
      'speed': round(i['quality']['bandwidth'], 2),
    })
    c += 1
    if c > 100: break
  suggestion = "Try searching for: "
  suggestion += choice(["fast", "gigabit"]) + " "
  suggestion += choice(["residential", "hosting", "organization", "government", "school", "college", "celluar"]) + " in "
  suggestion += choice([i for i in country_map if len(i) < 10])
  return render_template("index.html", nodes=nodes, suggestion=suggestion, query=query, empty=(len(nodes) == 0))

@app.route('/info/<id>')
def info(id):
  if not (id.startswith('0x') or all(c in string.hexdigits for c in id)): return "Not a valid ID"
  req = get(f"https://discovery.mysterium.network/api/v3/proposals?provider_id={id}").json()
  if req is None: return "Bad ID"
  node = req[0]
  loc = node['location']
  qua = node['quality']
  ip_type = loc['ip_type'] if 'ip_type' in loc else "unknown"
  details = {
    "type": ip_type.capitalize(),
    "isp": loc['isp'] if 'isp' in loc else "Unknown",
    "city": loc['city'] if 'city' in loc else "Unknown",
    "country": loc['country'] if 'country' in loc else "Unknown",
    "ip_icon": get_ip_icon(ip_type),
    "quality": qua['quality'],
    "bandwidth": qua['bandwidth'],
    "speed_icon": get_speed_icon(qua['bandwidth'])
  }
  return render_template("info.html", id=id, details=details)

if __name__ == "__main__":
  app.run()