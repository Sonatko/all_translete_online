"""
Comprehensive end-to-end runtime debug test for On-Demand MT translation architecture.
Verifies caching checks, translator behavior, and Qt dialog instantiation.
"""

import os
import sys
import unittest

# Ensure offscreen Qt platform for headless terminal execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Add LiveTranslate directory to path
_cur_dir = os.path.dirname(os.path.abspath(__file__))
_lt_dir = os.path.abspath(os.path.join(_cur_dir, "..", "stage_1_audio", "LiveTranslate"))
if _lt_dir not in sys.path:
    sys.path.insert(0, _lt_dir)


class TestMTOnDemandDebug(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_01_engine_cache_status(self):
        """Verify is_cached() functions correctly on local disk without network calls."""
        from nllb_engine import LocalNLLBEngine
        from hymt_engine import LocalHYMTEngine

        # NLLB 600M should be cached on disk
        nllb_cached = LocalNLLBEngine.is_cached("600m")
        print(f"\n[DEBUG] LocalNLLBEngine.is_cached('600m') = {nllb_cached}")
        self.assertTrue(nllb_cached, "NLLB 600M should be cached locally")

        # HY-MT 1.8B should NOT be cached yet
        hymt_cached = LocalHYMTEngine.is_cached()
        print(f"[DEBUG] LocalHYMTEngine.is_cached() = {hymt_cached}")
        self.assertFalse(hymt_cached, "HY-MT 1.8B should NOT be cached initially")

    def test_02_translator_nllb_and_hymt_nonblocking(self):
        """Verify Translator translates with NLLB and safely handles un-cached HY-MT."""
        from translator import Translator

        # Test NLLB
        t_nllb = Translator(api_base="local", api_key="not-needed", model="nllb-200-600m", target_language="ru")
        self.assertTrue(t_nllb._is_local_nllb)
        self.assertFalse(t_nllb._is_local_hymt)

        res_nllb = t_nllb.translate("Hello world", source_language="en")
        print(f"[DEBUG] NLLB translation result: '{res_nllb}'")
        self.assertTrue(len(res_nllb) > 0, "NLLB should produce valid Russian translation")

        # Test HY-MT (not cached yet)
        t_hymt = Translator(api_base="local", api_key="not-needed", model="hy-mt1.5-1.8b-gguf", target_language="ru")
        self.assertTrue(t_hymt._is_local_hymt)
        self.assertFalse(t_hymt._is_local_nllb)

        res_hymt = t_hymt.translate("Hello world", source_language="en")
        print(f"[DEBUG] HY-MT un-cached result: '{res_hymt}'")
        self.assertIn("веса модели не скачаны", res_hymt, "HY-MT should return safe non-blocking notice")

    def test_03_control_panel_model_status_tags(self):
        """Verify ControlPanel correctly tags models as [Готово] or [Скачать]."""
        from control_panel import ControlPanel
        dummy_config = {"asr": {}, "style": {}, "models": [], "active_model": 0}
        panel = ControlPanel(dummy_config)

        test_model_nllb = {"name": "Meta NLLB", "api_base": "local", "model": "nllb-200-600m"}
        test_model_hymt = {"name": "Tencent HY-MT", "api_base": "local", "model": "hy-mt1.5-1.8b-gguf"}

        self.assertTrue(panel._is_mt_model_cached(test_model_nllb))
        self.assertFalse(panel._is_mt_model_cached(test_model_hymt))
        print("[DEBUG] ControlPanel._is_mt_model_cached correctly identifies model presence")

    def test_04_dialogs_instantiation_for_mt(self):
        """Verify ModelDownloadDialog can be instantiated for MT models without errors."""
        from dialogs import ModelDownloadDialog

        missing_info = [
            {"name": "Tencent HY-MT1.5 1.8B", "type": "hy-mt1.5-1.8b-gguf"}
        ]
        # Instantiate dialog (don't exec) to verify UI layout and widget wiring
        dlg = ModelDownloadDialog(missing_info)
        self.assertIsNotNone(dlg)
        self.assertEqual(len(dlg._missing), 1)
        print("[DEBUG] ModelDownloadDialog instantiated cleanly for HY-MT")


if __name__ == "__main__":
    unittest.main()
