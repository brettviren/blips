local wc = import "wirecell.jsonnet";
local ar39 = import "ar39.jsonnet";

// special wire-cell command line configuratino
local cmdline = {
    type: "wire-cell",
    data: {
        plugins: ["WireCellGen", "WireCellSio"],
        apps: ["FourDee"]
    }
};

local random = {
    type: "Random",
    data: {
        generator: "default",
        seeds: [0,1,2,3,4],
    }
};

local params = {
    lar : {
        DL :  7.2 * wc.cm2/wc.s,
        DT : 12.0 * wc.cm2/wc.s,
        lifetime : 8*wc.ms,
        drift_speed : 1.114*wc.mm/wc.us, // microboone
        density: 1.389*wc.g/wc.centimeter3,
        ar39activity: 1*wc.Bq/wc.kg,
    },
    detector : {
        active_height: 2.325*wc.m,
        active_width: 10.368*wc.m,
        drift_distance: 2.5604*wc.m,
        drift_time: self.drift_distance/params.lar.drift_speed,
        drift_volume: self.drift_distance * self.active_height * self.active_width,
        drift_mass: params.lar.density * self.drift_volume,
    },
    daq : {
        readout_time: 5*wc.ms, // note, it's really ~9600*0.5us
        nreadouts: 1,
        start_time: 0.0*wc.s,
        stop_time: self.start_time + self.nreadouts*self.readout_time,
        tick: 0.5*wc.us,        // digitization time period
        sample_period: 0.5*wc.us, // sample time for any spectral data - usually same as tick
        first_frame_number: 100,
        ticks_per_readout: self.readout_time/self.tick,
    },
    adc : {
        gain: 1.0,
        baselines: [900*wc.millivolt,900*wc.millivolt,200*wc.millivolt],
        resolution: 12,
        fullscale: [0*wc.volt, 2.0*wc.volt],
    },
    elec : {
        gain : 14.0*wc.mV/wc.fC,
        shaping : 2.0*wc.us,
        postgain: -1.2,
    },
    sim : {
        fluctuate: true,
        digitize: true,
        noise: true,
    },
    files : {
        wires:"microboone-celltree-wires-v2.1.json.bz2",
        fields:"ub-10-half.json.bz2",
    }
};

// microboone wires are apparently not centered but are all with Z>0
local bigbox = {
    tail: { x:     0*wc.m,
	    y:-0.5*params.detector.active_height,
	    z:     0*wc.m},
    head: { x:     params.detector.drift_distance,
	    y:+0.5*params.detector.active_height,
	    z:+1.0*params.detector.active_width },
};
local lilbox = {
    tail: { x:   30*wc.cm,
	    y: -0.5*wc.cm,
	    z: -0.5*wc.cm+0.5*params.detector.active_width},
    head: { x:   31*wc.cm,
	    y: +0.5*wc.cm,
	    z: +0.5*wc.cm+0.5*params.detector.active_width}
};

local ar39blips = { 
    type: "BlipSource",
    name: "fullrate",
    data: {
	charge: ar39,
	time: {
	    type: "decay",
	    start: params.daq.start_time,
            stop: params.daq.stop_time,
	    activity: params.lar.ar39activity * params.detector.drift_mass,
	},
	position: {
	    type:"box",
            extent: bigbox,
	}
    }
};
local debugblips = { 
    type: "BlipSource",
    name: "lowrate",
    data: {
        charge: { type: "mono", value: 10000 },
	time: {
	    type: "decay",
	    start: params.daq.start_time,
            stop: params.daq.stop_time,
            activity: 1.0/(1*wc.ms), // low rate
	},
	position: {
	    type:"box",
	    extent: lilbox,     // localized
	}
    }
};
//local blips = ar39blips;
local blips = debugblips;


// One Anode for each universe
local anode_nominal = {
    type : "AnodePlane",
    name : "nominal",
    data : params.elec + params.daq + params.files {
        ident : 0,
    }
};
local anode_uvground = anode_nominal {
    name: "uvground",
    data : super.data {
        fields: "ub-10-uv-ground-half.json.bz2",
    }
};
local anode_vyground = anode_nominal {
    name: "vyground",
    data : super.data {
        fields: "ub-10-vy-ground-half.json.bz2",
    }
};
    


local drifter = {
    type : "Drifter",
    data : params.lar + params.sim  {
        anode: wc.tn(anode_nominal),
    }
};
local noise_model = {
    type: "EmpiricalNoiseModel",
    data: {
        // fixme: replace this with various models for DUNE, for now,
        // just pretend to be microboone.
        anode: wc.tn(anode_nominal),
        spectra_file: "microboone-noise-spectra-v2.json.bz2",
        chanstat: "StaticChannelStatus",
        nsamples: params.daq.ticks_per_readout,
    }
};
local noise_source = {
    type: "NoiseSource",
    data: params.daq {
        model: wc.tn(noise_model),
	anode: wc.tn(anode_nominal),
        start_time: params.daq.start_time,
        stop_time: params.daq.stop_time,
        readout_time: params.daq.readout_time,
    }
};

// One ductor for each universe, all identical except for a coresponding anode.
local ductor_nominal = {
    type : 'Ductor',
    name : 'nominal',
    data : params.daq + params.lar + params.sim {
        nsigma : 3,
	anode: wc.tn(anode_nominal),
    }
};
local ductor_uvground = ductor_nominal {
    name : 'uvground',
    data : super.data {
        anode: wc.tn(anode_uvground),
    }
};
local ductor_vyground = ductor_nominal {
    name : 'vyground',
    data : super.data {
        anode: wc.tn(anode_vyground),
    }
};

// One multiductor to rull them all.
local multi_ductor = {
    type: "MultiDuctor",
    data : {
        anode: wc.tn(anode_nominal),
        chains : [
            [
                {           // select based on transverse location
                    ductor: wc.tn(ductor_uvground),
                    rule: "wirebounds",    // select based on wire bounds.
                    args: [ // If depo is in one of the regions then this ductor is applied.
                        // Each region is specified as a range in u, v and w wire index ranges.
                        // Remember wire index starts counting with 0 at edge/corners at negative-most Z.
                        // Endpoints are considered part of the index range.
                        // Total region is the logical AND of all specified wire index ranges.
                        [
                            { plane: 0, min:100, max:200 },
                            { plane: 1, min:300, max:400 },
                        ],
                        [ // All regions in the list or logically ORed together.
                            { plane: 0, min:500, max:600 }, // just in U
                        ],
                    ],
                },

                {           // select based on transverse location
                    ductor: wc.tn(ductor_vyground),
                    rule: "wirebounds",    // select based on wire bounds.
                    args: [             // If depo is in one of the regions then this ductor is applied.
                        // Each region is specified as a range in u, v and w wire index ranges.
                        // Remember wire index starts counting with 0 at edge/corners at negative-most Z.
                        // Endpoints are considered part of the index range.
                        [ // Total region is the logical AND of all specified wire index ranges.
                            { plane: 1, min:800, max:800 },
                            { plane: 2, min:600, max:700 },
                        ],
                    ],
                },

                {   // if nothing above matches, then use this one
                    ductor: wc.tn(ductor_nominal),
                    rule: "bool",
                    args: true,
                }

            ],
        ],
    }
};
local digitizer = {
    type: "Digitizer",
    data : params.adc {
        anode: wc.tn(anode_nominal),
    }
};

local numpy_saver = {
    type: "NumpySaver",
    data: params.daq {
        //filename: "uboone-wctsim.npz",
        filename: "uboone-wctsim-%(src)s-%(digi)s-%(noise)s.npz" % {
            src: blips.name,
            digi: if params.sim.digitize then "adc" else "volts",
            noise: if params.sim.noise then "noise" else "signal",
        },
        frame_tags: [""],       // untagged.
        scale: if params.sim.digitize then 1.0 else wc.uV,
    }
};

local fourdee = {
    type: 'FourDee',
    data : {
        DepoSource: wc.tn(blips),
        DepoFilter: wc.tn(numpy_saver),
        Drifter: wc.tn(drifter),
        Ductor: wc.tn(multi_ductor),
        Dissonance: if params.sim.noise then wc.tn(noise_source),
        Digitizer: if params.sim.digitize then wc.tn(digitizer) else "",
        Filter: wc.tn(numpy_saver),
        FrameSink: ""
    }
};


// the final configuration sequence.
[
    cmdline,
    random,
    blips,
    anode_nominal,
    anode_uvground,
    anode_vyground,
    drifter,
    if params.sim.noise then noise_model,
    if params.sim.noise then noise_source,
    ductor_nominal,
    ductor_uvground,
    ductor_vyground,
    multi_ductor,
    if params.sim.digitize then digitizer,
    fourdee,
    numpy_saver,
]
