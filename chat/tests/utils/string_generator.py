from random import choice
from string import ascii_lowercase


def generate_string():
    string = ''
    for i in range(10):
        string += choice(ascii_lowercase)
    return string
