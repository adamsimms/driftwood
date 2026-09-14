import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from runtime import (  # noqa: E402
    clear_stop_flag,
    reboot_pi,
    setup_logging,
    should_stop,
    write_stop_flag,
)
from motor_utils import net_wave_diff  # noqa: E402


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        clear_stop_flag()

    def tearDown(self):
        clear_stop_flag()

    def test_reboot_skips_when_not_pi(self):
        log = mock.Mock()
        with mock.patch("runtime.is_raspberry_pi", return_value=False):
            with mock.patch("runtime.subprocess.run") as run:
                with self.assertRaises(SystemExit) as raised:
                    reboot_pi(log)
        self.assertEqual(raised.exception.code, 1)
        run.assert_not_called()
        log.warning.assert_called()

    def test_reboot_calls_sudo_on_pi(self):
        log = mock.Mock()
        failed = mock.Mock(returncode=1, stdout="", stderr="need password")
        with mock.patch("runtime.is_raspberry_pi", return_value=True):
            with mock.patch("runtime.subprocess.run", return_value=failed) as run:
                with self.assertRaises(SystemExit):
                    reboot_pi(log)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][:3], ["sudo", "-n", "/sbin/reboot"])

    def test_stop_flag(self):
        self.assertFalse(should_stop())
        write_stop_flag()
        self.assertTrue(should_stop())
        clear_stop_flag()
        self.assertFalse(should_stop())

    def test_setup_logging_writes_file(self):
        logger = setup_logging("live_data_stream")
        logger.info("test log line for issue 11")
        for handler in logger.handlers:
            handler.flush()
        log_file = ROOT / "logs" / "live_data_stream.log"
        self.assertTrue(log_file.exists())
        self.assertIn("test log line for issue 11", log_file.read_text())


class BlankWaveTests(unittest.TestCase):
    def test_holding_wave_has_zero_net_diff(self):
        self.assertEqual(net_wave_diff(0, 20), 0)
        self.assertEqual(net_wave_diff(0, -16), 0)

    def test_tide_wave_keeps_planned_diff(self):
        self.assertEqual(net_wave_diff(40, 20), 20)
        self.assertEqual(net_wave_diff(-10, -4), -4)


if __name__ == "__main__":
    unittest.main()
