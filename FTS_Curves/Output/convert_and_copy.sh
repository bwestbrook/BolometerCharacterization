#!/bin/bash

# Get some names of new files
basename_len=`ls $1 | wc -c`
basename_len=`expr $basename_len - 4`
base_name=`echo $1 | head -c$basename_len`
png_append='png'
eps_append='eps'
png_name='./high_quality_images/'$base_name$png_append
# Create the image file from the pdf, trying preserve 300 dpi quality for printing
convert -density 300 $1 -quality 100 -border 5x5 $png_name
# Copy to Dropbox
cp $1 ~/Dropbox/LTD-16/Poster/Figures
cp $png_name ~/Dropbox/LTD-16/Poster/Figures
# Copy to Dropbox
cp $1 ~/Desktop/Travel/LTD-16/Figures
cp $png_name ~/Desktop/Travel/LTD-16/Figures
