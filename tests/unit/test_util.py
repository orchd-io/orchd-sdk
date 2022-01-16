import pytest

import orchd_sdk.errors
from orchd_sdk.util import snake_to_camel_case, is_snake_case


class TestIsSneakCaseFunction:
    @pytest.mark.parametrize('given', [
        'some-not-snake-case1', '#some_not_snake_case2',
        '_some-not-snake', 'some-not-snake', 'SomeNot-snake',
        'ValidCamelCase', '', '_', '-', '_1', '1', '12345',
        '_123_233', '_123_asd'
    ])
    def test_given_not_snake_case_word_return_false(self, given):
        result = is_snake_case(given)
        assert result is False

    @pytest.mark.parametrize('given', [
        '_some_snake_with_heading_underscore', 'some_snake_with_trailing_underscore_',
        '_snake_heading_and_trailing_underscore_', 'a', '_a_', '_some_snake_'
    ])
    def test_given_snake_case_word_return_true(self, given):
        result = is_snake_case(given)
        assert result is True


class TestSnakeCaseToCamelCaseFunction:

    @pytest.mark.parametrize('given, expected', [
        ('some_snake', 'SomeSnake'),
        ('a_longest_snake_case', 'ALongestSnakeCase'),
        ('singleword', 'Singleword'),
        ('snake1', 'Snake1'),
        ('_snake2_1', 'Snake21'),
        ('a', 'A')
    ])
    def test_given_valid_snake_case_transform_it_in_camel_case(self, given, expected):
        result = snake_to_camel_case(given)
        assert result == expected

    @pytest.mark.parametrize('given, expected', [
        ('_some_snake_with_heading_underscore', 'SomeSnakeWithHeadingUnderscore'),
        ('some_snake_with_trailing_underscore_', 'SomeSnakeWithTrailingUnderscore'),
        ('_snake_heading_and_trailing_underscore_', 'SnakeHeadingAndTrailingUnderscore')
    ])
    def test_given_snake_case_with_trailing_underscores_and_or_heading_trim_and_transform_in_camel_case(self, given,
                                                                                                        expected):
        result = snake_to_camel_case(given)
        assert result == expected

    @pytest.mark.parametrize('given', [
        'some-not-snake-case1', '#some_not_snake_case2',
        '_some-not-snake', 'some-not-snake', 'SomeNot-snake',
        'ValidCamelCase', '12345', '_12', '1', '_1', '_'
    ])
    def test_given_not_snake_case_word_throw_exception(self, given):
        with pytest.raises(orchd_sdk.errors.InvalidInputError) as e:
            snake_to_camel_case(given)
