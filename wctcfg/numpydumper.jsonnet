// final config sequence
local wc = import "wirecell.jsonnet";

local source = {
    type: "wclsRawFrameSource",
    data: {
        // used to locate the input raw::RawDigit in the art::Event
        source_label: "daq",
        // names the output frame tags and likely must match the next
        // IFrameFilter (eg, that for the NF)
        frame_tags: ["daq"],
        nticks: 9595
    },
};



local numpy_saver = {
    type: "NumpySaver",
    data: {
        filename: "numpy-saver.npz",
        frame_tags: ["daq"],       // untagged.
        digitize: true,
    }
};



[
    source,
    numpy_saver,
    
    {
        type: "Omnibus",
        data: {
            source: wc.tn(source),
            filters: [wc.tn(numpy_saver)],
        }
    }
]
