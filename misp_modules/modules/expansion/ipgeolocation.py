import json
import traceback

import requests
from pymisp import MISPAttribute, MISPEvent, MISPObject

mispattributes = {
    'input': ['ip-dst', 'ip-src'],
    'format': 'misp_standard'
}
moduleinfo = {
    'version': '1', 'author': 'IpGeolocation',
    'description': 'Querry Using IpGeolocation.io',
    'module-type': ['expansion', 'hover']
}
moduleconfig = ['apiKey']

_IPGEO_MAPPING ={
    'isp':'ISP',
    'asn':'asn',
    'city':'city',
    'country_name':'country',
    'country_code2':'country-code',
    'latitude':'latitude',
    'longitude':'longitude',
    'organization':'organization',
    'continent_name':'region',
    'continent_code':'region-code',
    'state_prov':'state',
    'zipcode':'zipcode',
    'ip':'ip-src'
}


def handler(q=False):
    # Input checks
    if q is False:
        return False
    request = json.loads(q)
    if not request.get('config'):
        return {'error' : 'IpGeolocation Configuration is missing'}
    if not request['config'].get('apiKey'):
        return {'error' : 'IpGeolocation apiKey is missing'}
    
    if request['attribute']['type'] not in mispattributes['input']:
        return {'error': 'Unsupported attribute type.'}
            
    attribute = request['attribute']
    ip = request['attribute']['value']
    apiKey = request['config']['apiKey']
    query = requests.get(f"https://api.ipgeolocation.io/ipgeo?apiKey={apiKey}&ip={ip}")
    if query.status_code != 200:
        return {'error': f'Error while querying ipGeolocation.io - {query.status_code}: {query.reason}'}
    query = query.json()
    # Check if the IP address is not reserved for special use
    if query.get('message'):
        if 'bogon' in query['message']:
            return {'error': 'The IP address(bogon IP) is reserved for special use'}
        else:
            return {'error': 'Error Occurred during IP data Extraction from Message'}
    misp_event = MISPEvent()
    input_attribute = MISPAttribute()
    input_attribute.from_dict(**attribute)
    misp_event.add_attribute(**input_attribute)

    ipObject = MISPObject('ip-api-address')
    # Correct
    for field, relation in _IPGEO_MAPPING.items():
        ipObject.add_attribute(relation, query[field])
    ipObject.add_reference(input_attribute.uuid, 'locates')
    misp_event.add_object(ipObject)
    # Return the results in MISP format
    event = json.loads(misp_event.to_json())
    return {
        'results': {key: event[key] for key in ('Attribute', 'Object')}
    }

def introspection():
    return mispattributes


def version():
    moduleinfo['config'] = moduleconfig
    return moduleinfo



