#!/usr/bin/env python3
'''
GeGeDe builders for blips.

Blips assumes a trivial detector so these builders are nothing fancy.
'''

import gegede.builder
from gegede import Quantity as Q

class Box(gegede.builder.Builder):
    'A trivial "detector"'

    def configure(self, dx="1m", dy="1m", dz="1m"):
        self.size=(dx,dy,dz)

    def construct(self, geom):
        lar = geom.matter.Amalgam("LAr", z=18, a="39.95*g/mole",
                                  density="1.390*g/cc")

        shape = geom.shapes.Box(self.name + '_shape', *self.size)
        lv = geom.structure.Volume(self.name+'_volume',
                                   material = lar, shape=shape)
        self.add_volume(lv)
