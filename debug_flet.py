import flet as ft
import inspect

print("Flet version:", ft.version)
try:
    print("Tabs init args:", inspect.getfullargspec(ft.Tabs.__init__).args)
except:
    pass
    
print("Tabs dir:", [d for d in dir(ft.Tabs) if not d.startswith("_")])
