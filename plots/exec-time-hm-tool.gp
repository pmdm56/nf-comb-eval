# Set the terminal and output file
set terminal pdfcairo size 15, 10 enhanced color font 'Helvetica,45' linewidth 2
set output './../graphs/exec_time_compare.pdf'

# Set title and labels
set ylabel "Merge time (Minutes)"
set tics nomirror
set yrange [0:150]

# Define bar widths
set boxwidth 0.3

# Define colors for hand-made and nf-comb times
set style fill solid
set style data histograms
set style histogram cluster gap 1
set style fill solid border rgb "black"
set boxwidth 1
set bmargin 5

set style line 1 lt rgb "#d9d5d4" # Grey
set style line 2 lt rgb "#b5ceff" # Blue

# Plot the data
plot '../data/exec_time_hand.dat' using 3:xticlabel(1) title 'Handmade' ls 1, \
     '../data/exec_time_tool.dat' using 2 title 'Proposed tool' ls 2

