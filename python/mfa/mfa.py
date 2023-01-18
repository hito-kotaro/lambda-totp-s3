import pyotp
import json

def fetch_code(secret):
  return {
    'statusCode': 200,
    'code':  pyotp.TOTP(secret).now()
    }
