' notify.vbs (GitHub Notifier)
' Usage: cscript //Nologo notify.vbs "Title" "Message"

Set args = WScript.Arguments
If args.Count < 2 Then
    WScript.Quit
End If

title = args(0)
message = args(1)

' Flag 64: Information Icon
' Flag 4096: System Modal (Always on Top)
' Flag 0: OK Button only
MsgBox message, 0 + 64 + 4096, title