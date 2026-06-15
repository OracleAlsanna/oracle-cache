import random
import string

GENERATED_CODES = string.ascii_uppercase + string.digits


def generate_code(is_taken) -> str:
    for _ in range(10000):
        code = "".join(random.choices(GENERATED_CODES, k=4))
        if not is_taken(code):
            return code
    raise RuntimeError("Could not generate a unique code. Delete some links to free up codes.")
