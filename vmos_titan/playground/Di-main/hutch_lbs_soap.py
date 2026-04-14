#!/usr/bin/env python3
"""Hutch/Etisalat SOAP LBS location query.
Note: lbs-gw.hutch.lk DNS is currently unreachable.
Credentials loaded from config.json if present.
"""
import requests
import sys
import json
import os

API_URL = "https://lbs-gw.hutch.lk/api/lbs/v1/query"
SOAP_ACTION = "http://hutch.lk/lbs/queryLocation"

# Load credentials from config.json
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


def soap_payload(msisdn):
    return f"""<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
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
</soap:Envelope>"""


def query_location(msisdn):
    headers = {"SOAPAction": SOAP_ACTION, "Content-Type": "text/xml; charset=utf-8"}
    try:
        r = requests.post(API_URL, data=soap_payload(msisdn), headers=headers, timeout=15)
        print(f"[+] {r.status_code}: {r.text}")
        return r.text
    except requests.exceptions.ConnectionError as e:
        if "Name or service not known" in str(e) or "nodename" in str(e).lower():
            print("[!] Hutch LBS DNS failed: lbs-gw.hutch.lk is currently unreachable (no DNS record).")
        else:
            print(f"[!] Connection error: {e}")
        return None
    except requests.exceptions.Timeout:
        print("[!] Request timed out.")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hutch_lbs_soap.py 9477xxxxxxx")
        sys.exit(1)
    query_location(sys.argv[1])