from unittest.mock import MagicMock
from unittest.mock import patch

from bw_env._utils import is_bw_unlocked


@patch('bw_env._utils.subprocess.run')
def test_bw_is_locked(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'{"status":"locked"}',
        },
    )

    mock_run.return_value = mock_stdout
    assert not is_bw_unlocked('')


@patch('bw_env._utils.subprocess.run')
def test_bw_is_unlocked(mock_run):
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            'stdout': b'{"status":"unlocked"}',
        },
    )

    mock_run.return_value = mock_stdout
    assert is_bw_unlocked('')
