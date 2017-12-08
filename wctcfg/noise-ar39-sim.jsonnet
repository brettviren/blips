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
        drift_speed : 1.6*wc.mm/wc.us,
    },
    detector : {
        active_height: 5.9*wc.m,
        active_width: 2.2944*wc.m,
        drift_distance: 3.594*wc.m,
        drift_time: self.drift_distance/params.lar.drift_speed,
        drift_volume: self.drift_distance * self.active_height * self.active_width,
        drift_mass: self.density * self.drift_volume,
        density: 1.389*wc.g/wc.centimeter3,
        ar39activity: 1*wc.Bq/wc.kg,
    },
    daq : {
        readout_time: 1*wc.ms,
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
        postgain: 1.0,
    },
    sim : {
        fluctuate: true,
        digitize: false,
    },
    files : {
        wires:"dune-apa-wires.json.bz2",
        fields:"garfield-1d-3planes-21wires-6impacts-dune-v1.json.bz2",
    }
};
local bigbox = {
    tail: { x:     0*wc.m,
	    y:-0.5*params.detector.active_height,
	    z:-0.5*params.detector.active_width },
    head: { x:     params.detector.drift_distance,
	    y:+0.5*params.detector.active_height,
	    z:+0.5*params.detector.active_width },
};

local lilbox = {
    tail: { x:   30*wc.cm,
	    y: -0.5*wc.cm,
	    z: -0.5*wc.cm},
    head: { x:   31*wc.cm,
	    y: +0.5*wc.cm,
	    z: +0.5*wc.cm}
};

local blips = { 
    type: "BlipSource",
    data: {
	//charge: ar39,
        charge: { type: "mono", value: 50000 }, // whopper
	time: {
	    type: "decay",
	    start: params.daq.start_time,
            stop: params.daq.stop_time,
	    //activity: params.detector.ar39activity * params.detector.drift_mass,
            activity: 1.0/(100*wc.us),
	},
	position: {
	    type:"box",
	    extent: lilbox,
	}
    }
};
local anode = {
    type : "AnodePlane",
    data : params.elec + params.daq + params.files {
        ident : 0,
    }
};
local drifter = {
    type : "Drifter",
    data : params.lar + params.sim  {
        anode: wc.tn(anode),
    }
};
local noise_model = {
    type: "EmpiricalNoiseModel",
    data: {
        // fixme: replace this with various models for DUNE, for now,
        // just pretend to be microboone.
        spectra_file: "microboone-noise-spectra-v2.json.bz2",
        chanstat: "",	// no per-channel deviation
        nsamples: params.daq.ticks_per_readout,
    }
};
local noise_source = {
    type: "NoiseSource",
    data: params.daq {
        model: wc.tn(noise_model),
	anode: wc.tn(anode),
        start_time: params.daq.start_time,
        stop_time: params.daq.stop_time,
        readout_time: params.daq.readout_time,
    }
};
local ductor = {
    type : 'Ductor',
    data : params.daq + params.lar + params.sim {
        nsigma : 3,
	anode: wc.tn(anode),
    }
};
local digitizer = {
    type: "Digitizer",
    data : params.adc {
        anode: wc.tn(anode),
    }
};

local numpy_saver = {
    type: "NumpySaver",
    data: params.daq {
        filename: "wirecellsim.npz",
        frame_tags: [""],       // untagged.
        scale: if params.sim.digitize then 1.0 else wc.uV,
    }
};

local fourdee = {
    type: 'FourDee',
    data : {
        DepoSource: wc.tn(blips),
        Drifter: wc.tn(drifter),
        Ductor: wc.tn(ductor),
        Dissonance: wc.tn(noise_source),
        //Dissonance: "",
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
    anode,
    drifter,
    noise_model,
    noise_source,
    ductor,
    if params.sim.digitize then digitizer,
    fourdee,
    numpy_saver,
]
