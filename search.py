import string

class Search:
  country_map = {}
  all_types = [
    "residential",
    "hosting",
    "business",
    "education",
    "celluar",
    "organization",
    "content_delivery_network",
    "government",
    "college"
  ]
  type_aliases = {
    "residential": ["residential", "bypass", "home"],
    "hosting": ["hosting", "datacenter"],
    "business": ["residential", "bypass"],
    "education": ["residential", "bypass", "school", "college"],
    "celluar": ["residential", "bypass", "home"],
    "organization": ["residential", "bypass"],
    "content_delivery_network": ["hosting", "datacenter"],
    "government": ["residential", "bypass"],
    "college": ["residential", "bypass", "school", "education"]
  }
  speed_aliases = {
    "fast": 100,
    "gigabit": 1000
  }
  exact_match = False
  single_type_allowed = True
  iso_detect = False
  show_max = 100
  show_min = 5

  def __init__(self, country_map:dict, all_types:list=None, type_aliases:dict=None, speed_aliases:dict=None, exact_match:bool=False, single_type_allowed:bool=True, iso_detect:bool=False):
    self.country_map = country_map
    if all_types is not None: self.all_types = all_types
    if type_aliases is not None: self.type_aliases = type_aliases
    if speed_aliases is not None: self.speed_aliases = speed_aliases
    self.exact_match = exact_match
    self.single_type_allowed = single_type_allowed
    self.iso_detect = iso_detect

  def _format_query(self, query:str):
    query = ''.join(filter(str.isalnum, query.lower().replace(' ', '')))
    return query

  def process(self, query:str):
    query_raw = query
    query_list = query.split(' ')
    query = self._format_query(query_raw)
    countries = []
    types = []
    speed = 0
    asn = []
    show = None
    for i in query_list:
      if i.lower().startswith('as'):
        num = i[2:]
        if num.isdigit(): asn.append(int(num))
    for i in self.country_map:
      if self.country_map[i].lower() in query + query_raw:
        if not i in countries: countries.append(i)
      elif self.iso_detect and i in query_list:
        if not i in countries: countries.append(i)
    for i in self.type_aliases:
      for j in self.type_aliases[i]:
        if not i in types and j in query:
          types.append(i)
    if self.single_type_allowed:
      for i in self.all_types:
        if not i in types and i in query:
          types.append(i)
    for i in self.speed_aliases:
      speed += self.speed_aliases[i] * query.count(i)
    try:
      index = query_list.index('show')
      if query_list[index+1].isdigit():
        show = int(query_list[index+1])
    except ValueError:
      pass
    response = {
      "countries": (countries if len(countries) > 0 else None),
      "types": (types if len(types) > 0 else None),
      "speed": speed,
      "asn": (asn if len(asn) > 0 else None),
      "show": show
    }
    return response 