import string
from secrets import choice


def generate_trash_string(length: int):
    ans = ''
    ALPHABET = string.digits + string.ascii_letters
    for _ in range(length):
        ans += choice(ALPHABET)
    return ans
