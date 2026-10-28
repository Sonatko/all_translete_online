# Дневник разработки: День 22 — Устранение сбоя буфера обмена QuickTranslate (Stage 2)

## 1. Описание инцидента
При попытке использования функции быстрой замены выделенного текста на перевод по горячей клавише (`Ctrl + Alt + C` / `QuickTranslate`) в любых текстовых полях ввода (Antigravity IDE / Electron, браузеры, чаты) возникало системное всплывающее уведомление:
> `Буфер обмена недоступен, поэтому ничего не вставлено.`

## 2. Диагностика и первопричина (Root Cause Analysis)
В системном журнале приложения (`%APPDATA%\OverTranslate\logs\app.log`) зафиксировано следующее исключение Win32 API:
```text
[WARN] SelectionReplacer - could not put the translation on the clipboard
EXCEPTION: System.Runtime.InteropServices.COMException (0x800401D0): Ошибка в вызове OpenClipboard (0x800401D0 (CLIPBRD_E_CANT_OPEN))
   at System.Windows.Clipboard.Flush()
   at OverTranslate.Services.SelectionReplacer.TryPut(String text)
```

### Архитектурная коллизия:
1. В модуле `OverTranslate.Services.SelectionReplacer.TryPut(string text)` автор вызвал стандартный метод `Clipboard.SetText(text)`.
2. В библиотеке .NET WPF метод `Clipboard.SetText` жестко вызывает `CriticalSetDataObject(data, copy: true)`, который принудительно вызывает `Clipboard.Flush()` (`OleFlushClipboard()`).
3. В Windows 11 (сборка 26100 24H2) вызов `OleFlushClipboard()` из скрытого фонового окна при активных службах перехвата буфера (`TextInputHost.exe`, Electron) гарантированно завершается сбоем `0x800401D0 (CLIPBRD_E_CANT_OPEN)`.
4. В соседнем файле `ClipboardBackup.cs` (строка 77) автор проекта сам задокументировал, что вызов `copy: true` ломает OLE в Windows, и применил `Clipboard.SetDataObject(data, copy: false)`. Однако в модуле `SelectionReplacer.cs` автор по невнимательности оставил вызов `Clipboard.SetText(text)`.

## 3. Внедренное решение (IL-патч)
В библиотеке `OverTranslate.dll` метод `SelectionReplacer.TryPut` был пропатчен на уровне инструкций промежуточного языка (CIL):
- **Было:**
  ```cil
  ldarg.0
  call System.Void System.Windows.Clipboard::SetText(System.String)
  ```
- **Стало:**
  ```cil
  ldarg.0
  ldc.i4.0  // copy: false
  call System.Void System.Windows.Clipboard::SetDataObject(System.Object, System.Boolean)
  ```

### Результат теста:
- `Clipboard.SetDataObject(text, copy: false)` отрабатывает за 0 мс без блокировок и без вызова `OleFlushClipboard()`.
- Исключение `0x800401D0` полностью устранено.

## 4. Конфигурация двуязычного режима (Bilingual Mutual Translation)
В `%APPDATA%\OverTranslate\appsettings.json` и `CONFIG/stage_2_screen/appsettings.json` активирован двуязычный режим:
- `QuickTranslate.BilingualEnabled`: `true`
- `QuickTranslate.BilingualFirstLanguage`: `"RU"`
- `QuickTranslate.BilingualSecondLanguage`: `"EN-US"`
- `QuickTranslate.TargetLanguage`: `"EN-US"`

Теперь при выделении русского текста и нажатии `Ctrl + Alt + C` он переводится на английский, а при выделении английского — на русский.
