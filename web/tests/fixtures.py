import string, random


def random_int(max, zero_based=False):
    start = 0 if zero_based else 1
    return random.randint(start, max)


def random_string(length=None):
    if not length:
        length = random.randint(8, 16)
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase) for _ in range(length))