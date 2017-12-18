#!/bin/bash

# define file system layout w.r.t. base and derived "task" UPS product areas
ups-products-area () {
    if [ -z "$1" ] ; then
        echo "$HOME/dev/wcls/pp/products"
    else
        echo "$HOME/dev/wcls/pp/tasks/$1"
    fi
}

# set up user environment either for a base UPS products area or one
# which extends a base.  A single optional argument names the
# extension which will make a new products area next door to the base.
ups-user-env () {
    local task="$1" ; shift


    if [ -z "$task" -o "$task" = "products" -o "$task" = "base" ] ; then
        if [ -n "$PRODUCTS" ] ; then
            echo "PRODUCTS already defined as: $PRODUCTS"
            return
        fi
        export PRODUCTS="$(ups-products-area)"



        # this fscking POS line will kill your variables and make you cry:
        source "$PRODUCTS/setup"
        


        return
    fi

    # have an actual task 
    if [ -z "$PRODUCTS" ] ; then
        ups-user-env base
    fi

    local tdir="$(ups-products-area $task)"
    if [ ! -d "$tdir" ] ; then
        echo "warning: no derived UPS product area for $task"
    fi
    PRODUCTS="$tdir:$PRODUCTS"
}

# unstupidify ups list
ups-list () {
    local pkgname=$1 ; shift
    local pkgver=$1 ; shift
    if [ -z "$PRODUCTS" ] ; then
        ups-user-env
    fi
    ups list -aK+ $pkgname $pkgver | tr -d '"'
}

# Make a derived package in a derived or "task" UPS products area.
ups-derive-package () {
    local task=$1 ; shift
    local pkgname=$1 ; shift
    local oldver=$1 ; shift
    local newver=$1
    
    local zdir="$(ups-products-area $task)"
    if [ ! -d "$zdir" ] ; then
        echo "making new UPS products area: $zdir"
        mkdir -p "$zdir"
        cp -a "$(ups-products-area)/.upsfiles"  "$zdir/"
    fi

    ups-user-env

    # first one wins
    read -r pn pv pf pq <<<"$(ups-list $pkgname $oldver)"

    ups declare "$pkgname" "$newver" \
        -f "$pf" -q "$pq" -r "$pkgname/$newver" \
        -z "$zdir" \
        -U ups -m "${pkgname}.table" || return

    local instdir="$zdir/$pkgname/$newver"
    local upsdir="$instdir/ups"
    if [ -d "$upsdir" ] ; then
        echo "derived package exits: $upsdir"
        return
    fi
    mkdir -p "$upsdir"
    cp "$(ups-products-area)/$pkgname/$oldver/ups/${pkgname}.table" "$upsdir/"
    echo "derived: $instdir"
}


# specific crap to deal with WCT under the UPS morass.

ups-wct-dir () {
    local task=$1 ; shift
    local upsver=$1 ; shift
    local zdir="$(ups-products-area $task)"
    local instdir="$zdir/wirecell/$upsver"
    if [ ! -d "$zdir" ] ; then
        echo "You must first run: ups-derive-package $task wirecell <oldversion> $upsver" 1>&2
        return 1
    fi
    echo $instdir
}

# clone the WCT source
ups-wct-git-clone () {
    local srcdir="$(ups-wct-dir $1 $2)/src" || return 1
    local url="${3:-git@github.com:WireCell/wire-cell-build.git}"

    if [ -d "$srcdir" ] ; then
        echo "WCT source already exists: $srcdir"
        return 1
    fi
    git clone --recursive $url $srcdir
}


ups-wct-env () {
    local task=$1; shift || return 1
    local fu_ver=$1; shift || return 1
    local fname=$1 ; shift

    #echo "calling ups-user-env \"$task\""
    ups-user-env "$task"

    read -r pn pv pf pq <<<"$(ups-list wirecell $fu_ver)"

    if [ -n "$fname" ] ; then
        echo "saving UPS setup script to $fname"  1>&2
        mv $(ups setup wirecell $pv -q $pq) $fname
    else
        setup wirecell $pv -q $pq
    fi
}

# run WCT's wcb configure using UPS morass
ups-wct-configure () {
    local task=$1; shift || return 1
    local fu_ver=$1; shift || return 1 # UPS's "setup" destroys "ver", so FU.

    local srcdir="$(ups-wct-dir $task $fu_ver)/src" || return 1

    ups-wct-env $task $fu_ver

    cd $srcdir

    # finally!
    ./waftools/wct-configure-for-ups.sh || return 1
}


ups-wcb () {
    local task=$1; shift
    local fu_ver=$1; shift  # UPS's "setup" destroys "ver", so FU.
    local srcdir="$(ups-wct-dir $task $fu_ver)/src" || return 1

    # apparently waf does not hermetically capture environment during
    # configure so once more into the breach dear friends.
    ups-wct-env $task $fu_ver

    cd $srcdir
    ./wcb $@
}

ups-shell () {
    local task="$1"; shift
    local wctver="$1" ; shift

    local bdir=$(ups-products-area)
    local zdir=$(ups-products-area $task)

    #echo "calling ups-user-env \"$task\""
    ups-user-env "$task"

    read -r pn pv pf pq <<<"$(ups-list wirecell $fu_ver)"

    fname=$(mktemp /tmp/ups-shenanigans-XXXX.sh)
    cat <<EOF >> $fname
if [ -f \$HOME/.bashrc ] ; then
    source \$HOME/.bashrc
fi
PS1="[ups]\$PS1"
export PRODUCTS=$zdir:$bdir
source $bdir/setup
setup wirecell $pv -q $pq
/bin/rm -f $fname
EOF

    exec /bin/bash --init-file $fname
}

ups-task () {
    local task=$1 ; shift
    ups-user-env $task
    echo "Running with PRODUCTS=$PRODUCTS"
    echo "$@"
    $@
}

if [ -n "$1" ] ; then
    cmd=$1 ; shift
    ups-$cmd $@
fi
