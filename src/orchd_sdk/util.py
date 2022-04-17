# The MIT License (MIT)
# Copyright © 2022 <Mathias Santos de Brito>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

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
