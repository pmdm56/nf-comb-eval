set terminal pdfcairo size 15, 10 enhanced color font 'Helvetica,45' linewidth 2
set output './throughput.pdf'
# Set plot title and labels
set ylabel 'Throughput (Mpps)'

# Set style for error bars
set style data histogram
set style histogram clustered gap 1 title textcolor lt -1
set style fill solid border 0
set boxwidth 1
set style histogram errorbars lw 2

# Define the data file
uniform_data = '../data/throughput_uni.dat'
zipf_data = '../data/throughput_zipf.dat'

# Define custom x-axis labels
set xtics scale 0
#set xtics ('nat_poldown' 1, 'fw_polup' 2, 'fw_poldown' 3, 'nat_polup' 4)

# Define y-axis range and ticks
set yrange [0:20]
set ytics 0,4,20

# Plot the data
plot uniform_data using 2:3:4:xtic(1) w histogram linecolor "#d9d5d4" title 'Uniform', \
     zipf_data using 2:3:4:xtic(1) w histogram linecolor "#b5ceff" title 'Zipf', \