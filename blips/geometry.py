#!/usr/bin/env python3
'''
GeGeDe builders for blips.

Blips assumes a trivial detector so these builders are nothing fancy.
'''

import gegede.builder
from gegede import Quantity as Q

class Materials(gegede.builder.Builder):
    def construct(self, geom):
        geom.matter.Element("Hydrogen","H",1,"1.01g/mole")
        geom.matter.Element("Nitrogen", "N", 7, "14.01*g/mole")
        geom.matter.Element("Oxygen", "O", 8, "16.0g/mole")
        geom.matter.Molecule("Water", density="1.0kg/l",
                             elements=(("Oxygen",1),("Hydrogen",2)))
        geom.matter.Mixture("Air", density = "1.290*mg/cc", 
                            components = (("Nitrogen", 0.7), ("Oxygen",0.3)))
        geom.matter.Amalgam("LAr", z=18, a="39.95*g/mole",
                            density="1.390*g/cc")

class Box(gegede.builder.Builder):
    'A trivial "detector"'

    def configure(self, dx="1m", dy="1m", dz="1m", material="LAr"):
        self.size=(dx,dy,dz)
        self.material=material

    def construct(self, geom):

        shape = geom.shapes.Box(self.name + '_box', *self.size)
        lv = geom.structure.Volume(self.name,
                                   material = self.material,
                                   shape=shape)
        self.add_volume(lv)
        if not self.builders:
            return
        sn, sb = self.builders.items()[0]
        child_name, child_lv = sb.volumes.items()[0]
        pv = geom.structure.Placement('%s_in_%s' % (sb.name, self.name),
                                      volume = child_lv)
        lv.placements.append(pv.name)

        
