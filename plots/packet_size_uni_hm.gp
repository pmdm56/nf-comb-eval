set terminal pdfcairo size 35, 10 enhanced color font 'Helvetica,45' linewidth 2
set output './../graphs/packet_size_uni_hm.pdf'
# Set plot title and labels

# Set style for error bars
set style data histogram
set style histogram clustered gap 1 title textcolor lt -1
set style fill solid border 0
set boxwidth 1
set style histogram errorbars lw 2

# Define the data file
fpu = './../data-psize-uni-mpps/hm_fw_polup_psize.dat'
fpd = './../data-psize-uni-mpps/hm_fw_poldown_psize.dat'
npu = './../data-psize-uni-mpps/hm_nat_polup_psize.dat'
npd = './../data-psize-uni-mpps/hm_nat_poldown_psize.dat'

# Define the data file gbps
fpu1 = './../data-psize-uni-gbps/hm_fw_polup_psize.dat'
fpd1 = './../data-psize-uni-gbps/hm_fw_poldown_psize.dat'
npu1 = './../data-psize-uni-gbps/hm_nat_polup_psize.dat'
npd1 = './../data-psize-uni-gbps/hm_nat_poldown_psize.dat'

# Define custom x-axis labels
set xtics scale 0

# Define y-axis range and ticks
set yrange [0:15]
set ytics 0,5,15

set multiplot layout 1,2 rowsfirst

set ylabel 'Throughput (Mpps)'
set xlabel 'Packet size (Bytes)'

# Plot the data
plot fpu using 2:3:4:xtic(1) w histogram linecolor "#d9d5d4" title 'fw+polup', \
     fpd using 2:3:4:xtic(1) w histogram linecolor "#b5ceff" title 'fw+poldown', \
     npu using 2:3:4:xtic(1) w histogram linecolor "#f2fb7f" title 'nat+polup', \
     npd using 2:3:4:xtic(1) w histogram linecolor "#b0e57d" title 'nat+poldown'

set ylabel 'Throughput (Gbps)'
set yrange [0:100]
set ytics 0,10,100
set key top left

# Plot the data
plot fpu1 using 2:3:4:xtic(1) w histogram linecolor "#d9d5d4" title 'fw+polup', \
     fpd1 using 2:3:4:xtic(1) w histogram linecolor "#b5ceff" title 'fw+poldown', \
     npu1 using 2:3:4:xtic(1) w histogram linecolor "#f2fb7f" title 'nat+polup', \
     npd1 using 2:3:4:xtic(1) w histogram linecolor "#b0e57d" title 'nat+poldown'