set terminal pdfcairo size 15, 10 enhanced color font 'Helvetica,45' linewidth 2
set output '../graphs/loc.pdf'
# Set plot title and labels
set ylabel 'Lines of code'

# Set style for error bars
set style data histogram
set style histogram clustered gap 1 title textcolor lt -1
set style fill solid border 0
set boxwidth 1

# Define the data file
locs_hm = '../data/loc_hm.dat'
locs_tool = '../data/loc_tool.dat'

# Define custom x-axis labels
set xtics scale 0

# Define y-axis range and ticks
set yrange [0:3000]
set ytics 0,500,3000

# Plot the data
plot locs_hm using 2:xtic(1) w histogram linecolor "#d9d5d4" title 'Handmade', \
     locs_tool using 2:xtic(1) w histogram linecolor "#b5ceff" title 'Proposed Tool', \

