import re

from orchd_sdk.errors import InvalidInputError

SNAKE_CASE_REGEX = re.compile(r'\A([a-z]|(_+[a-z]))[a-z0-9_]*\Z')
KEBAB_CASE_NO_SURROUNDING_DASHES = re.compile(r'\A[a-z]([a-z0-9]|-[a-z0-9])*\Z')


def is_kebab_case(word: str):
    matched_word = KEBAB_CASE_NO_SURROUNDING_DASHES.match(word)
    return matched_word is not None


def is_snake_case(word: str):
    matched_word = SNAKE_CASE_REGEX.match(word)
    return matched_word is not None


def kebab_case_to_snake_case(kebab_cased_word: str):
    if is_kebab_case(kebab_cased_word):
        return kebab_cased_word.replace('-', '_')
    else:
        raise InvalidInputError('Given word is not a Kebab Case!')


def snake_to_camel_case(snake_cased_word: str):
    if is_snake_case(snake_cased_word):
        words = snake_cased_word.split('_')
        return ''.join(w.capitalize() for w in words)
    else:
        raise InvalidInputError('Given word is not Snake Case!')
