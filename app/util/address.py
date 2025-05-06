from dadata import Dadata
from geopy.geocoders import Nominatim

from ..settings import settings


dadata_ = Dadata(settings.DADATA_TOKEN, settings.DADATA_SECRET)
geolocator = Nominatim(user_agent='rent_analyze_get_address')

def get_address_info_from_dadata(address: str) -> dict:
    return dadata_.clean('address', address)

def get_address_short_info(address: str) -> tuple[str, str, float, float] | None:
    addr_info = get_address_info_from_dadata(address)
    if addr_info is None or addr_info['qc_geo'] != 0:
        return None
    district = addr_info['settlement']
    if district is None:
        address_nominatim = ', '.join(s.replace(' д ', ' ') for s in address.split(', '))
        nominatim_addr = geolocator.geocode(address_nominatim, addressdetails=True)
        raw_addr = nominatim_addr.raw['address']
        district = raw_addr['city_district'].replace('округ', '').strip() if 'city_district' in raw_addr else None
    city = addr_info.get('city') or addr_info.get('region')
    return city, district or addr_info['city_district'], float(addr_info['geo_lat']), float(addr_info['geo_lon'])

def get_address_suggestions(query: str) -> list[str]:
    result = dadata_.suggest("address", query)
    return sorted(list(set([s['value'].split(' стр ')[0] for s in result])))
