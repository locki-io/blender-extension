# preliminary pip install bignumber.py
from bignumber import BigNumber
import requests


def number_to_padded_hex(value: str) -> str:
    hex_value = BigNumber(value).hex()
    return zero_pad_string_if_odd_length(hex_value)

def zero_pad_string_if_odd_length(s: str) -> str:
    return s if len(s) % 2 == 0 else '0' + s

# Test
# value = "12345"
# print(number_to_padded_hex(value))

class ErrFetch(Exception):
    def __init__(self, status, status_text):
        super().__init__(f"Error {status}: {status_text}")
        self.status = status
        self.status_text = status_text

def check_status(response: requests.Response):
    if not (200 <= response.status_code <= 299):
        raise ErrFetch(response.status_code, response.reason)
