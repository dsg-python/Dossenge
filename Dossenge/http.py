# Copyright (c) 2026 Dossenge
# Released under the MIT License (see LICENSE file for details)

import requests

def header_request(url,**headers):
    try:
        response = requests.get(url,headers=headers)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        raise Exception('Connection Error')

