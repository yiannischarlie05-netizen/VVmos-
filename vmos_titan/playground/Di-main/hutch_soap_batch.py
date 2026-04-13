#!/usr/bin/env python3
"""Hutch SOAP LBS batch location query.
Note: lbs-gw.hutch.lk is currently DNS unreachable.
Credentials loaded from config.json if present.
"""
import requests
import time
import json
import os
import sys

API_URL = "https://lbs-gw.hutch.lk/api/lbs/v1/query"
SOAP_ACTION = "http://hutch.lk/lbs/queryLocation"

_config_path = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(_config_path) as _f:
        _cfg = json.load(_f)
    USERNAME = _cfg.get("hutch_username", "lbs_operator")
    PASSWORD = _cfg.get("hutch_password", "")
    API_KEY = _cfg.get("hutch_api_key", "")
except Exception:
    USERNAME = "lbs_operator"
    PASSWORD = ""
    API_KEY = ""

targets = sys.argv[1:] if len(sys.argv) > 1 else ["94771234567", "94772345678"]

def soap_payload(msisdn):
    return f"""
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <wsse:UsernameToken>
        <wsse:Username>{USERNAME}</wsse:Username>
        <wsse:Password>{PASSWORD}</wsse:Password>
      </wsse:UsernameToken>
    </wsse:Security>
  </soap:Header>
  <soap:Body>
    <ns1:queryLocationRequest xmlns:ns1="http://hutch.lk/lbs">
      <msisdn>{msisdn}</msisdn>
      <accuracy>high</accuracy>
      <apiKey>{API_KEY}</apiKey>
    </ns1:queryLocationRequest>
  </soap:Body>
</soap:Envelope>
"""
headers = {"SOAPAction": SOAP_ACTION, "Content-Type": "text/xml; charset=utf-8"}


def query_batch(target_list):
    for n in target_list:
        try:
            resp = requests.post(API_URL, data=soap_payload(n), headers=headers, timeout=15)
            print(f"[{n}] {resp.status_code}: {resp.text[:500]}")
        except requests.exceptions.ConnectionError as e:
            if "Name or service not known" in str(e) or "nodename" in str(e).lower():
                print(f"[{n}] DNS fail: lbs-gw.hutch.lk is currently unreachable.")
            else:
                print(f"[{n}] Connection error: {e}")
        except requests.exceptions.Timeout:
            print(f"[{n}] Timeout.")
        time.sleep(1)


if __name__ == "__main__":
    query_batch(targets)