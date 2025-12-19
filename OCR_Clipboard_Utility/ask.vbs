' --- OCR Prompt VBScript ---
' This script displays a modal dialog box using VBScript's MsgBox function.
' It is executed by the Python script to ask the user whether to perform OCR.
'
' Buttons: 4 = VbYesNo (Yes=6, No=7)
' Icon: 32 = VbQuestion (A question mark icon)

Dim result
' Display the prompt. If the user clicks 'Yes', result is 6. If 'No', result is 7.
result = MsgBox("A new image has been copied to the clipboard. Do you want to convert the image to text (OCR)?", 4 + 32, "Clipboard Image Detected")

' Print the result code to the standard output (STDOUT) so Python can capture it.
WScript.Echo result
