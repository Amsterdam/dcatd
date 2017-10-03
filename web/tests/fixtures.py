import string, random


def random_string(length=None):
    if not length:
        length = random.randint(8, 16)
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase) for _ in range(length))