from flask import Flask, render_template, request
from requests import get
from random import choice
from json import load
from search import Search
from flask_minify import Minify
import string

app = Flask(__name__, static_url_path='', static_folder='public/static', template_folder='public')
Minify(app=app, html=True, js=True, cssless=True)

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
    country_map[i['alpha-2']] = i['name']#.lower()

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

def simpleNode(data):
  loc = data['location']
  ip_type = loc['ip_type'] if 'ip_type' in loc else "unknown"
  return {
      'id': data['provider_id'],
      'short': data['provider_id'][:8] + '...',
      'type': ip_type.capitalize(),
      'city': loc['city'] if 'city' in loc else "Unknown",
      'country': loc['country'] if 'country' in loc else "Unknown",
      'speed': round(data['quality']['bandwidth'], 2),
    }

@app.route('/')
def home():
  query = request.args.get('query', default="", type=str)
  req = get("https://discovery.mysterium.network/api/v3/proposals").json()
  if req is None: return "Something went wrong"
  criteria = Search(country_map, iso_detect=True).process(query)
  max_display = (max(min(criteria['show'], 1000), 5) if criteria['show'] is not None else 20) - 1
  nodes = []
  c = 0
  match = next((i for i in req if i['provider_id'] in query.strip()), None)
  print(match)
  if match: nodes.append(simpleNode(match))
  for i in req:
    loc = i['location']
    ip_type = loc['ip_type'] if 'ip_type' in loc else "unknown"
    country = loc['country'] if 'country' in loc else "Unknown"
    asn = loc['asn'] if 'asn' in loc else "Unknown"
    if criteria['types'] is not None:
      if not ip_type in criteria['types']: continue
    if criteria['countries'] is not None:
      if not country in criteria['countries']: continue
    if criteria['asn'] is not None:
      if not asn in criteria['asn']: continue
    if i['quality']['bandwidth'] <= criteria['speed']:
      continue
    nodes.append(simpleNode(i))
    c += 1
    if c > max_display: break
  suggestion = "Try searching for: "
  suggestion += choice(["fast", "gigabit"]) + " "
  suggestion += choice(["residential", "hosting", "organization", "government", "school", "college", "celluar"]) + " in "
  suggestion += choice([i for i in country_map.values() if len(i) < 12]).lower()
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
    "country": country_map[loc['country']] if 'country' in loc else "Unknown",
    "country_code": loc['country'] if 'country' in loc else "??",
    "asn": f"AS{loc['asn']}" if 'asn' in loc else "",
    "ip_icon": get_ip_icon(ip_type),
    "quality": format(qua['quality'], '.2f'),
    "bandwidth": format(qua['bandwidth'], '.2f'),
    "speed_icon": get_speed_icon(qua['bandwidth'])
  }
  return render_template("info.html", id=id, details=details)

@app.after_request
def add_header(response):
  response.cache_control.public = True
  response.cache_control.max_age = 3600
  return response

if __name__ == "__main__":
  app.run()