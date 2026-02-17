from pulser.register.special_layouts import TriangularLatticeLayout

layout = TriangularLatticeLayout(n_traps=50, spacing=5.0)

print("Methods:", [m for m in dir(layout) if 'register' in m])

try:
    reg = layout.hexagonal_register(rows=3)
    print("hexagonal_register(3) ->", reg)
    print("Has layout?", hasattr(reg, 'layout'))
    print("Layout:", reg.layout)
except Exception as e:
    print("hexagonal_register failed:", e)

try:
    reg = layout.rectangular_register(rows=3, atoms_per_row=3)
    print("rectangular_register(3,3) ->", reg)
    print("Has layout?", hasattr(reg, 'layout'))
except Exception as e:
    print("rectangular_register failed:", e)
    
try:
    # Try creating from trap IDs if possible
    # In newer pulser it's layout.register(ids)
    # In older?
    pass
except:
    pass
