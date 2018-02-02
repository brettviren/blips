def options(opt):
    #opt.load('boost', tooldir="waftools")
    opt.load('compiler_cxx')

def configure(conf):
    #conf.load('boost', tooldir="waftools")
    conf.load('compiler_cxx')
    conf.env.CXXFLAGS += ["-O3", "-std=c++14"]
    #conf.env.CXXFLAGS += ["-g", "-std=c++14"]
    #conf.check_boost(lib='timer system')
    conf.check_cfg(package='eigen3',  uselib_store='EIGEN', args='--cflags --libs')


def build(bld):
    bld.program(source='test/test_primitives.cxx src/cnpy.cxx', 
                target='test_primitives',
                includes="inc",
                lib = ["z"],
                use='EIGEN'
    )    
