from core import Core

core = Core('slats1999@gmail.com', '$Logan1992')
core.fillUpgrades()

while(True):
    core.upgradeSbc()
    for i in range(20):
        core.bronzeMethod()
    