import sys
sys.path.append("../modules")
sys.path.append("../../")

URL_GET_JS_ID_API_KEY = 'https://www.6play.fr/connexion'
URL_API_KEY = 'https://www.6play.fr/client-%s.bundle.js'
URL_COMPTE_LOGIN = 'https://login.6play.fr/accounts.login'
URL_TOKEN_DRM = 'https://6play-users.6play.fr/v2/platforms/chromecast/services/6play/users/%s/videos/%s/upfront-token'
URL_LIVE_JSON = 'https://chromecast.middleware.6play.fr/6play/v2/platforms/chromecast/services/6play/live?channel=%s&with=service_display_images,nextdiffusion,extra_data'
URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&x-dt-auth-token=%s|R{SSM}|JBlicense'
DRM_SERVER = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/'

from Livyconf import *

import urlquick
import webutils
import json
import re
from listitem import Listitem

def get_live_url( item_id, **kwargs):


    resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY)
    js_id = re.compile(r'client\-(.*?)\.bundle\.js').findall(
        resp_js_id.text)[0]
    resp = urlquick.get(URL_API_KEY % js_id)

    # Hack to force encoding of the response
    resp.encoding = 'utf-8'

    api_key = re.compile(r'\"eu1.gigya.com\"\,key\:\"(.*?)\"').findall(
        resp.text)[0]

    # Build PAYLOAD
    payload = {
        "loginID": m6playlogin["login"],
        "password": m6playlogin["password"],
        "apiKey": api_key,
        "format": "jsonp",
        "callback": "jsonp_3bbusffr388pem4"
    }
    # LOGIN
    resp2 = urlquick.post(
        URL_COMPTE_LOGIN,
        data=payload,
        headers={
            'User-Agent': webutils.get_random_ua(),
            'referer': 'https://www.6play.fr/connexion'})
    json_parser = json.loads(
        resp2.text.replace('jsonp_3bbusffr388pem4(', '').replace(');', ''))

    if "UID" not in json_parser:
        return False
    account_id = json_parser["UID"]
    account_timestamp = json_parser["signatureTimestamp"]
    account_signature = json_parser["UIDSignature"]


    # Build PAYLOAD headers
    payload_headers = {
        'x-auth-gigya-signature': account_signature,
        'x-auth-gigya-signature-timestamp': account_timestamp,
        'x-auth-gigya-uid': account_id,
        'x-customer-name': 'm6web'
    }

    if item_id == '6ter':
        token_json = urlquick.get(
            URL_TOKEN_DRM % (account_id, 'dashcenc_%s' % '6T'),
            headers=payload_headers,
            max_age=-1)
    elif item_id == 'fun_radio' or \
            item_id == 'rtl2' or \
            item_id == 'gulli':
        token_json = urlquick.get(
            URL_TOKEN_DRM % (account_id, 'dashcenc_%s' % item_id),
            headers=payload_headers,
            max_age=-1)
    else:
        token_json = urlquick.get(
            URL_TOKEN_DRM % (account_id, 'dashcenc_%s' % item_id.upper()),
            headers=payload_headers,
            max_age=-1)
    token_jsonparser = json.loads(token_json.text)
    token = token_jsonparser["token"]

    if item_id == '6ter':
        video_json = urlquick.get(
            URL_LIVE_JSON % '6T',
            headers={'User-Agent': webutils.get_random_ua()},
            max_age=-1)
        json_parser = json.loads(video_json.text)
        video_assets = json_parser['6T'][0]['live']['assets'][::-1]
    elif item_id == 'fun_radio' or \
            item_id == 'rtl2' or \
            item_id == 'gulli':
        video_json = urlquick.get(
            URL_LIVE_JSON % (item_id),
            headers={'User-Agent': webutils.get_random_ua()},
            max_age=-1)
        json_parser = json.loads(video_json.text)
        video_assets = json_parser[item_id][0]['live']['assets'][::-1]
    else:
        video_json = urlquick.get(
            URL_LIVE_JSON % (item_id.upper()),
            headers={'User-Agent': webutils.get_random_ua()},
            max_age=-1)
        json_parser = json.loads(video_json.text)
        video_assets = json_parser[item_id.upper()][0]['live']['assets'][::-1]

    if not video_assets:
        plugin.notify('INFO', plugin.localize(30716))
        return False

    subtitle_url = ''
    if False:
        for asset in video_assets:
            if 'subtitle_vtt' in asset["type"]:
                subtitle_url = asset['full_physical_path']

    for asset in video_assets:
        if 'delta_dashcenc_h264' in asset["type"]:
            item = Listitem()
            item.path = asset['full_physical_path']
            if 'http' in subtitle_url:
                item.subtitles.append(subtitle_url)
            item.token=token
            item.property["inputstreamaddon"] = 'inputstream.adaptive'
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.property[
                'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property[
                'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % token

            # item.label = get_selected_item_label()
            # item.art.update(get_selected_item_art())
            # item.info.update(get_selected_item_info())

            return item
    return False