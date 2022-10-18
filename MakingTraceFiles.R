library(readr)
library(plyr)

#change the year of the trace files you want to collapse into one data set 
year = 2009
resource = "PV"
direction = "West"

#set directory to the folder with all the traces in it 
setwd("/Users/elonarey-costa/Documents/phdCode/NEMO/data/PVTraceWestRN")

#collect all the files with the same year and puts them into a list 
files = list.files(pattern = paste(resource, ".*", year, ".*", direction, "\\.csv", sep = ""), full.names = TRUE)

#Make a new df with the first file, but only keep the time column 
df <- read.csv(files[1], skip = 3)
df <- df[-2]

i = 0
for (data in files){
  i = i+1
  temp <- read.csv(data, skip = 3)
  trace <- temp$electricity
  df <- cbind(df, trace)
  names(df)[names(df) == "trace"] <- i 
}

#export dataframe as csv into that same directory
write.csv(df, file = paste(year, resource, direction, ".csv", sep = ""), row.names = FALSE)

