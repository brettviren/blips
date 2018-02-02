#include <chrono>
#include <valarray>
#include <iostream>
#include <Eigen/Core>

#include "cnpy.h"


typedef Eigen::Array<short, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> ArrayXXs;
typedef Eigen::Array<int, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> ArrayXXi;
typedef Eigen::Array<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> ArrayXXf;

int main(int argc, char* argv[])
{
    if (argc < 4) {
        std::cerr << "usage: chanmap.npz test_nparray numpy-saver.npz outfile.npz\n";
        std::cerr << "file as produced by WCT component NumpySaver\n";
        return 1;
    }
    const char* cmapfn = argv[1];
    const char* infn = argv[2];
    const char* outfn = argv[3];

    cnpy::npz_t npz_cmap = cnpy::npz_load(cmapfn);
    std::cerr << "loaded npz: " << cmapfn << std::endl;
    cnpy::NpyArray np_cclayer = npz_cmap["chip_channel_layer"];
    assert(np_cclayer.data<int>());



    ArrayXXi cclayer = Eigen::Map<ArrayXXi>(np_cclayer.data<int>(),
                                            np_cclayer.shape[0], np_cclayer.shape[1]);
    cnpy::NpyArray np_ccspot = npz_cmap["chip_channel_spot"];
    assert(np_ccspot.data<int>());
    ArrayXXi ccspot = Eigen::Map<ArrayXXi>(np_ccspot.data<int>(),
                                           np_ccspot.shape[0], np_ccspot.shape[1]);

    std::cerr << "numpy channel map shape: (" << np_ccspot.shape[0] << ", " << np_ccspot.shape[1] << ")\n";
    std::cerr << "eigen channel map shape: (rows=" << ccspot.rows() << ", cols=" << ccspot.cols() << ")\n";
    assert(np_ccspot.shape[0] == ccspot.rows());

    // the numpy array is in channel-major order
    for (int iasic=0; iasic<8; ++iasic) {
        for (int ich=0; ich<16; ++ich) {
            int ind = iasic*16 + ich;
            std::cerr << " " << np_ccspot.data<int>()[ind];
        }
        std::cerr << std::endl;        
    }
    std::cerr << std::endl;

    for (int iasic=0; iasic<8; ++iasic) {
        for (int ich=0; ich<16; ++ich) {
            std::cerr << ccspot(iasic,ich) << " ";
        }
        std::cerr << std::endl;
    }

    auto start = std::chrono::high_resolution_clock::now();
    cnpy::npz_t npz = cnpy::npz_load(infn);

    cnpy::NpyArray np_frame = npz["frame__0"];
    std::cerr << "numpy frame shape: (" << np_frame.shape[0] << "," << np_frame.shape[1] << ")\n";
    const int nticks = np_frame.shape[0];

    cnpy::NpyArray np_chans = npz["channels__0"];
    const int nchans = np_chans.shape[0];
    assert(nchans == np_frame.shape[1]);
    std::valarray<int> chans(np_chans.data<int>(), nchans);

    // one row is one tick of nchans channels
    ArrayXXf full_frame = Eigen::Map<ArrayXXf>(np_frame.data<float>(),nticks,nchans);
    std::cerr << "eigen frame shape: (rows=" << full_frame.rows() << ", cols=" << full_frame.cols() << ")\n";
    assert(np_frame.shape[0] == full_frame.rows());


    auto stop = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed_seconds = stop-start;
    std::cerr << "load npz in " << elapsed_seconds.count() << std::endl;

    // dig out collection channels on "front" face
    // channel numbers are in form [wibconnector][wibslot][asicchip][asicchan]
    // where the asichan has 2 digits and all numbers are 1-based counts.
    std::vector<int> chan_plane(chans.size(), 0);
    const int nwireper[3] = {40,40,48};
    const int nwib = 5;

    int nwchans = 0;
    for (int ind=0; ind<chans.size(); ++ind) {
        int hash = chans[ind];
        int conn = hash/10000 - 1;
        int slot = (hash%10000)/1000 - 1;
        int chip = (hash%1000)/100 - 1;
        int chan = (hash%100) - 1;
        int layer = cclayer(chip,chan);
        int spot = ccspot(chip,chan);
        int wire = nwireper[layer]*(conn*nwib+slot) + spot;
        std::cout << ind << "\t" << hash
                  << "\ticonn=" << conn << "\tislot=" << slot
                  << "\tichip=" << chip << "\tichan=" << chan
                  << " \t" << "uvw"[layer]
                  << "\tnspot=" << spot << " \tnwire=" << wire << std::endl;
        chan_plane[ind] = layer;
        if (layer == 2) {
            ++nwchans;
        }
    }

    // from now we just care about first collection plane

    ArrayXXs w_frame = ArrayXXs::Zero(nticks, nwchans);
    start = std::chrono::high_resolution_clock::now();

    size_t iwch = 0;
    for (int ich=0; ich<chans.size(); ++ich) {
        if (chan_plane[ich] < 2) {
            continue;
        }
        if (iwch == nwchans) {
            std::cerr << "Cows fly: " << ich << " " << iwch << " " << nwchans << "\n";
            assert (iwch < nwchans);
        }

        w_frame.col(iwch) = full_frame.col(ich).cast<short>();
        //std::cout << iwch << " " << ich << " " << chans[ich] << std::endl;
        ++iwch;
    }

    stop = std::chrono::high_resolution_clock::now();
    elapsed_seconds = stop-start;
    std::cerr << "copy " << nwchans << " collection channels x "<< nticks <<" ticks in " << elapsed_seconds.count() << std::endl;


    // find baselines and noise widths.
    start = std::chrono::high_resolution_clock::now();

    // Histogram ADC values for each channel.  Note, this supports the
    // full ADC resolution.  One could make a guess that the baseline
    // and noise width are constrained to be in some smaller region.
    // In either case, underflows and overflows are kept in the two
    // extreme ADC bins as we ultimately want percentiles.

    // Note, the baseline and threshold are found and applied to the
    // same data below.  The lowside percentile threshold and the
    // median should not be strongly influenced by signal.  In a real
    // detector these quantities are maybe better maintained over some
    // longer period.  But not too long.  In order to remove influence
    // for the past one strategy might be to maintain chunked "hist"
    // arrays.  For example, maybe maintain N chunks eg each spanning
    // 1ms and subtract the oldest 1ms and add the newest.

    const int adcbits=12;
    const int maxadc = 2<<adcbits;
    ArrayXXi hist = ArrayXXi::Zero(maxadc, nwchans);
    ArrayXXi cumu = ArrayXXi::Zero(maxadc, nwchans);

    for (size_t itick=0; itick<nticks; ++itick) {
        Eigen::ArrayXi tickvec = w_frame.row(itick).cast<int>();
        
        for (int ich = 0; ich < nwchans; ++ich) {
            int adc = tickvec(ich);
            if (adc < 0) adc = 0;
            if (adc >= maxadc) adc = maxadc;
            hist(adc, ich) += 1;
        }
    }

    // Form the cumulative ADC distribution.
    cumu.row(0) = hist.row(0);
    for (int iadc = 1; iadc < maxadc; ++iadc) {
        cumu.row(iadc) = hist.row(iadc) + cumu.row(iadc-1);
    }

    // Find the ADC value of the low-side percentile threshold and
    // median ADC values.
    const int median_sum = nticks*0.50;
    const int thresh_sum = nticks*0.001;
    Eigen::ArrayXi baseline = Eigen::ArrayXi::Zero(nwchans);
    Eigen::ArrayXi threshold = Eigen::ArrayXi::Zero(nwchans);
    for (int ich=0; ich < nwchans; ++ich) {
        int iadc=0;
        for (; iadc<maxadc; ++iadc) {
            if (cumu(iadc, ich) > thresh_sum) {
                threshold(ich) = iadc;
                break;
            }
        }
        for (; iadc<maxadc; ++iadc) {
            if (cumu(iadc, ich) > median_sum) {
                baseline(ich) = iadc;
                break;
            }
        }
    }
    

    stop = std::chrono::high_resolution_clock::now();
    elapsed_seconds = stop-start;
    std::cerr << "find baseline/thresholds in " << elapsed_seconds.count() << std::endl;


    // Finally find times above threshold
    start = std::chrono::high_resolution_clock::now();

    ArrayXXs blipmask = ArrayXXs::Zero(nticks, nwchans);

    struct TAT {
        int ich;
        int tmin, tmax;
        int adcsum;
        TAT(int ich, int tmin, int tmax, int adcsum) : ich(ich), tmin(tmin), tmax(tmax), adcsum(adcsum){}
    };
    std::vector<TAT> primitives;
    for (int ich=0; ich < nwchans; ++ich) {
        const int absthresh = 2*baseline(ich) - threshold(ich);
        //std::cout << ich << " " << threshold(ich) << " " << baseline(ich) << std::endl;
        int adcsum = 0;
        int tmin = 0;
        for (int itick=0; itick < nticks; ++itick) {
            int adc = w_frame(itick,ich);
            if (!adcsum) {      // outside a TAT
                if (adc < absthresh) {
                    continue;   // still outside a TAT
                }
                // just crossed
                adcsum += adc - baseline(ich);
                tmin = itick;
                blipmask(itick, ich) = (short)1;
            }
            else {              // inside a TAT
                if (adc < absthresh) { // went below threshold, flush
                    primitives.push_back(TAT(ich, tmin, itick, adcsum));
                    tmin = adcsum = 0;
                    continue;
                }
                // still inside
                adcsum += adc - baseline(ich);
                blipmask(itick, ich) = (short)1;
            }
        }
    }    
    stop = std::chrono::high_resolution_clock::now();
    elapsed_seconds = stop-start;
    std::cerr << "find "<<primitives.size()<<" primitives in " << elapsed_seconds.count() << std::endl;


    // dump everything for plotting
    stop = std::chrono::high_resolution_clock::now();
    cnpy::npz_save<float>(outfn, "fullframe", np_frame.data<float>(), {(size_t)nticks, (size_t)nchans}, "w");
    cnpy::npz_save<int>(outfn, "channels", np_chans.data<int>(), {(size_t)nchans}, "a");
    cnpy::npz_save<short>(outfn, "colframe", w_frame.data(), {(size_t)nticks, (size_t)nwchans}, "a");
    cnpy::npz_save<int>(outfn, "hist", hist.data(), {(size_t)maxadc, (size_t)nwchans}, "a");
    cnpy::npz_save<int>(outfn, "cumu", cumu.data(), {(size_t)maxadc, (size_t)nwchans}, "a");
    cnpy::npz_save<int>(outfn, "baseline", baseline.data(), {(size_t)nwchans}, "a");
    cnpy::npz_save<int>(outfn, "threshold", threshold.data(), {(size_t)nwchans}, "a");
    cnpy::npz_save<short>(outfn, "blipmask", blipmask.data(), {(size_t)nticks, (size_t)nwchans}, "a");
    stop = std::chrono::high_resolution_clock::now();
    elapsed_seconds = stop-start;
    std::cerr << "dump intermdiates to numpy in " << elapsed_seconds.count() << std::endl;

    return 0;
}
