"""Test suite for System Tray integration in Universal Hub and Stage 3 Voice Studio.
Verifies QSystemTrayIcon creation, minimize-to-tray, restore, context menus,
and guaranteed cleanup without phantom icons.
"""
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

# Ensure headless offscreen platform for automated test runs
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"


class TestSystemTrayIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.app.setQuitOnLastWindowClosed(False)

    def test_hub_system_tray(self):
        """Verify Universal Hub system tray lifecycle and minimize-to-tray."""
        from launcher.hub import EcosystemHub

        hub = EcosystemHub()
        self.assertIsNotNone(hub.tray_icon, "Universal Hub tray_icon should be initialized")
        self.assertIsNotNone(hub.btn_tray, "Universal Hub btn_tray should exist")
        self.assertIn("трей", hub.btn_tray.text().lower())

        # Test context menu actions
        menu = hub.tray_icon.contextMenu()
        self.assertIsNotNone(menu, "Tray context menu should exist")
        action_texts = [a.text() for a in menu.actions() if a.text()]
        self.assertTrue(any("развернуть" in t.lower() for t in action_texts), "Menu should have restore action")
        self.assertTrue(any("выход" in t.lower() for t in action_texts), "Menu should have quit action")

        # Test minimize to tray
        hub.show()
        self.assertTrue(hub.isVisible(), "Hub should be visible initially")
        hub._minimize_to_tray()
        self.assertTrue(hub.isHidden(), "Hub should be hidden after minimize to tray")

        # Test restore from tray
        hub._restore_from_tray()
        self.assertTrue(hub.isVisible(), "Hub should be visible after restore from tray")

        # Test clean cleanup
        hub._cleanup_tray()
        self.assertIsNone(hub.tray_icon, "Tray icon must be None after cleanup")
        hub.close()

    def test_stage3_system_tray(self):
        """Verify Stage 3 Voice Studio system tray lifecycle and minimize-to-tray."""
        from stage_3_voice.studio.audio_engine import AudioEngine
        from stage_3_voice.studio.config import load_settings
        from stage_3_voice.studio.model_manager import ModelManager
        from stage_3_voice.studio.gui import StudioWindow

        cfg = load_settings()
        mm = ModelManager()
        engine = AudioEngine(mm, cfg)
        win = StudioWindow(engine, mm)

        self.assertIsNotNone(win.tray_icon, "Voice Studio tray_icon should be initialized")
        self.assertIsNotNone(win.btn_tray, "Voice Studio btn_tray should exist")
        self.assertEqual(win.btn_tray.text(), "📥 В трей")

        # Test context menu actions
        menu = win.tray_icon.contextMenu()
        self.assertIsNotNone(menu, "Tray context menu should exist")
        action_texts = [a.text() for a in menu.actions() if a.text()]
        self.assertTrue(any("развернуть" in t.lower() for t in action_texts), "Menu should have restore action")
        self.assertTrue(any("закрыть" in t.lower() or "выход" in t.lower() for t in action_texts), "Menu should have quit action")

        # Test minimize to tray
        win.show()
        self.assertTrue(win.isVisible(), "Voice Studio should be visible initially")
        win._minimize_to_tray()
        self.assertTrue(win.isHidden(), "Voice Studio should be hidden after minimize to tray")

        # Test restore from tray
        win._restore_from_tray()
        self.assertTrue(win.isVisible(), "Voice Studio should be visible after restore from tray")

        # Test clean cleanup
        win._cleanup_tray()
        self.assertIsNone(win.tray_icon, "Tray icon must be None after cleanup")
        win.close()


if __name__ == "__main__":
    unittest.main()
