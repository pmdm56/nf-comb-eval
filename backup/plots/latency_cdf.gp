set terminal pdf size 15, 15 enhanced color font 'Helvetica,30' linewidth 2
set output './../graphs/latency-tool.pdf'


unset key
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
plot '../data/fw_polup_latency.dat' with lines

# Second graph
set title "fw+poldown"
plot '../data/fw_poldown_latency.dat' with lines

# Third graph
set title "nat+polup"
plot '../data/nat_polup_latency.dat' with lines

# Fourth graph
set title "nat+poldown"
plot '../data/nat_poldown_latency.dat' with lines

unset multiplot