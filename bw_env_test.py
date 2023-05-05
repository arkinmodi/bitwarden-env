import os
import pytest
import random
import string
import sys

from unittest.mock import MagicMock
from unittest.mock import patch

from bw_env import _generate
from bw_env import _is_bw_unlocked
from bw_env import _run


@patch('bw_env.subprocess.run')
def test_bw_is_locked(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'{"status":"locked"}'
        }
    )

    mock_run.return_value = mock_stdout
    assert not _is_bw_unlocked('')


@patch('bw_env.subprocess.run')
def test_bw_is_unlocked(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'{"status":"unlocked"}'
        }
    )

    mock_run.return_value = mock_stdout
    assert _is_bw_unlocked('')


@pytest.mark.skipif(
    sys.platform == 'win32',
    reason='Windows does not implement execvpe correctly'
)
@patch('bw_env.dotenv_values')
@patch('bw_env.execvpe')
@patch('bw_env.subprocess.run')
def test_bw_run(mock_run, mock_execvpe, mock_dotenv_values):
    mock_dotenv_values.return_value = {
        'TEST_A': 'bwenv://test_bw_id/fields/TEST_BW_A',
        'TEST_B': 'non_bw_env',
    }

    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'''
{
    "fields": [
        {
            "name": "TEST_BW_A",
            "value": "bw_env"
        }
    ]
}
                ''',
            'stderr': None,
        }
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    _run('', test_cmd, '')

    execvpe_cmd = mock_execvpe.call_args.args[1]
    execvpe_env = mock_execvpe.call_args.args[2]

    assert execvpe_cmd == test_cmd
    assert 'TEST_A' in execvpe_env
    assert execvpe_env['TEST_A'] == 'bw_env'
    assert 'TEST_B' not in execvpe_env


@patch('bw_env.dotenv_values')
@patch('bw_env.execvpe')
@patch('bw_env.subprocess.run')
def test_bw_run_empty_env_file(mock_run, mock_execvpe, mock_dotenv_values):
    mock_dotenv_values.return_value = {}

    test_cmd = ['test', 'command']
    _run('', test_cmd, '')

    execvpe_cmd = mock_execvpe.call_args.args[1]
    assert execvpe_cmd == test_cmd
    assert mock_run.call_count == 0


@patch('bw_env.dotenv_values')
@patch('bw_env.execvpe')
@patch('bw_env.subprocess.run')
def test_bw_run_bw_item_not_found(mock_run, mock_execvpe, mock_dotenv_values):
    mock_dotenv_values.return_value = {
        'TEST_A': 'bwenv://test_bw_id/fields/TEST_BW_A',
    }

    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': None,
            'stderr': b'Not found.',
        }
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    with pytest.raises(RuntimeError):
        _run('', test_cmd, '')


@patch('bw_env.dotenv_values')
@patch('bw_env.execvpe')
@patch('bw_env.subprocess.run')
def test_bw_run_bw_name_not_found_in_bw_item(
        mock_run,
        mock_execvpe,
        mock_dotenv_values
):
    mock_dotenv_values.return_value = {
        'TEST_A': 'bwenv://test_bw_id/fields/TEST_BW_A',
    }

    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'{ "fields": [] }',
            'stderr': None,
        }
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    _run('', test_cmd, '')

    execvpe_env = mock_execvpe.call_args.args[2]

    assert 'TEST_A' not in execvpe_env


@patch('bw_env.dotenv_values')
@patch('bw_env.execvpe')
@patch('bw_env.subprocess.run')
def test_bw_run_malformed_secret_reference_string(
        mock_run,
        mock_execvpe,
        mock_dotenv_values
):
    mock_dotenv_values.return_value = {
        'TEST_A': 'bwenv:///fields/TEST_BW_A',
        'TEST_B': 'bwenv:// /fields/TEST_BW_A',
    }

    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'{ "fields": [] }',
            'stderr': None,
        }
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    _run('', test_cmd, '')

    execvpe_env = mock_execvpe.call_args.args[2]

    assert 'TEST_A' not in execvpe_env
    assert 'TEST_B' not in execvpe_env
    assert mock_run.call_count == 0


@patch('bw_env.subprocess.run')
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
        }
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    letters = string.ascii_letters + string.digits
    filename = '.env.' + ''.join(random.choice(letters) for _ in range(10))

    _generate('', test_cmd, filename)

    expected_env = 'TEST_A="bwenv://BW_ID/fields/TEST_A"\n'

    with open(filename, 'r') as f:
        actual_env = f.read()

    assert expected_env == actual_env
    os.remove(filename)


@patch('bw_env.subprocess.run')
def test_bw_generate_missing_fields(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'{ "id": "BW_ID" }',
            'stderr': None,
        }
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    with pytest.raises(RuntimeError):
        _generate('', test_cmd, '')


@patch('bw_env.subprocess.run')
def test_bw_generate_bw_item_not_found(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': None,
            'stderr': b'Not found.',
        }
    )
    mock_run.return_value = mock_stdout

    test_cmd = ['test', 'command']

    with pytest.raises(RuntimeError):
        _generate('', test_cmd, '')
