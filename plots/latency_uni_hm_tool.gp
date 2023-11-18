set terminal pdf size 15, 15 enhanced color font 'Helvetica,30' linewidth 2
set output './../graphs/latency-tool-compare-uni.pdf'

set key top left
set xlabel "Latency ({/Symbol m}s)"

set ylabel "CDF"
set ytics 0.5 nomirror
set xtics nomirror
set yrange [ 0 : 1 ] noreverse writeback

set grid ytics lt 0 lw 1 lc rgb "#bbbbbb"
set grid xtics lt 0 lw 1 lc rgb "#bbbbbb"

set linetype 1 linecolor rgb "#332288" lw 3
set linetype 2 linecolor rgb "#CC6677" lw 3
set linetype 3 linecolor rgb "#88CCEE" lw 3

set multiplot layout 4,1 rowsfirst

# First graph
set title "fw+polup"
plot '../data/tool_fw_polup_latency_uni.dat' with lines lc rgb "#d9d5d4" title "Proposed Tool", \
     '../data/hm_fw_polup_latency_uni.dat' with lines lc rgb "#b5ceff" title "Handmade"

# Second graph
set title "fw+poldown"
plot '../data/tool_fw_poldown_latency_uni.dat' with lines lc rgb "#d9d5d4" title "Proposed Tool", \
     '../data/hm_fw_poldown_latency_uni.dat' with lines lc rgb "#b5ceff" title "Handmade"

# Third graph
set title "nat+polup"
plot '../data/tool_nat_polup_latency_uni.dat' with lines lc rgb "#d9d5d4" title "Proposed Tool", \
     '../data/hm_nat_polup_latency_uni.dat' with lines lc rgb "#b5ceff" title "Handmade"

# Fourth graph
set title "nat+poldown"
plot '../data/tool_nat_poldown_latency_uni.dat' with lines lc rgb "#d9d5d4" title "Proposed Tool", \
     '../data/hm_nat_poldown_latency_uni.dat' with lines lc rgb "#b5ceff" title "Handmade"

unset multiplot