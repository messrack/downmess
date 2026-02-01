import flet as ft
import inspect

print("Flet version:", ft.version)
try:
    print("FilePicker init args:", inspect.getfullargspec(ft.FilePicker.__init__).args)
except:
    print("Could not get args")
    
print("FilePicker dir:", [d for d in dir(ft.FilePicker) if "on_" in d])
