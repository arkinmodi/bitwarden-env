import os
import random
import string
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from bw_env._generate import generate


@patch('bw_env._generate.subprocess.run')
def test_bw_generate(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'''
{
    "id": "BW_ID",
    "fields": [
        {
            "name": "TEST_A",
            "value": "bw_env"
        }
    ]
}
                ''',
            'stderr': None,
        },
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    letters = string.ascii_letters + string.digits
    filename = '.env.' + ''.join(random.choice(letters) for _ in range(10))

    generate('', test_cmd, filename)

    expected_env = 'TEST_A="bwenv://BW_ID/fields/TEST_A"\n'

    with open(filename) as f:
        actual_env = f.read()

    assert expected_env == actual_env
    os.remove(filename)


@patch('bw_env._generate.subprocess.run')
def test_bw_generate_missing_fields(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'{ "id": "BW_ID" }',
            'stderr': None,
        },
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    with pytest.raises(RuntimeError):
        generate('', test_cmd, '')


@patch('bw_env._generate.subprocess.run')
def test_bw_generate_bw_item_not_found(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': None,
            'stderr': b'Not found.',
        },
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    with pytest.raises(RuntimeError):
        generate('', test_cmd, '')


@patch('bw_env._generate.subprocess.run')
def test_bw_generate_multiple_bw_items_found(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': None,
            'stderr': b'''
More than one result was found. Try getting a specific object by `id` instead. The following objects were found:
27a7e219-098f-4342-9475-85c98610a985
7cbb5074-a3c9-4f3f-b3c5-286ae1176e35
''',  # noqa: E501
        },
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    with pytest.raises(RuntimeError):
        generate('', test_cmd, '')
