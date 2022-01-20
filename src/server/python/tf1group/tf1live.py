import sys
sys.path.append("../modules")
URL_VIDEO_STREAM = 'https://mediainfo.tf1.fr/mediainfocombo/%s?context=MYTF1&pver=4008002&platform=web&os=linux&osVersion=unknown&topDomain=www.tf1.fr'

URL_LICENCE_KEY = 'https://drm-wide.tf1.fr/proxy?id=%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=drm-wide.tf1.fr|R{SSM}|'
import urlquick
import webutils
import json
from listitem import Listitem
def get_live_url(item_id, **kwargs):

    video_id = 'L_%s' % item_id.upper()
    url_json = URL_VIDEO_STREAM % video_id
    htlm_json = urlquick.get(url_json,
                             headers={'User-Agent': webutils.get_random_ua()},
                             max_age=-1)
    json_parser = json.loads(htlm_json.text)



    item = Listitem()
    item.path = json_parser['delivery']['url']
    item.property["inputstreamaddon"] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = URL_LICENCE_KEY % video_id

    return item

if __name__=="__main__":
    print(get_live_url(str(sys.argv[1])).path)