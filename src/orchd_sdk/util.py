import re

from orchd_sdk.errors import InvalidInputError

SNAKE_CASE_REGEX = re.compile(r'^([a-z]|(_+[a-z]))[a-z0-9_]*\Z')


def is_snake_case(word: str):
    matched_word = SNAKE_CASE_REGEX.match(word)
    if matched_word and matched_word.end() == len(word):
        return True
    return False


def snake_to_camel_case(snake_cased_word: str):
    """Transforms a given snake cased name in camel case."""
    if is_snake_case(snake_cased_word):
        words = snake_cased_word.split('_')
        return ''.join(w.capitalize() for w in words)
    else:
        raise InvalidInputError('Name is not snake case!')
