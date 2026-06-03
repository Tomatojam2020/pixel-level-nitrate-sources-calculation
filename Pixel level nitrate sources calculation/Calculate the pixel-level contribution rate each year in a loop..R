library(siar)
library(foreach)
library(doParallel)
library(doSNOW) 

# Set working path
setwd("E:/project/SIAR/")

# import file（Stores csv files for each year.）
input_dir <- "annual_tables"
# export file
output_dir <- "annual_results"
if (!dir.exists(output_dir)) dir.create(output_dir, recursive = TRUE)

# Reading background data of potential nitrate source isotopes
sources <- read.csv("source.csv", header = TRUE)

# Get a list of files for all years
files <- list.files(input_dir, pattern = "^delta_[0-9]{4}\\.csv$", full.names = TRUE)

# Register a parallel backend (register globally once to improve efficiency).
cl <- makeCluster(16) 
registerDoSNOW(cl)

# Processing in cycles every year
for (file in files) {
  # Extraction Year
  year <- gsub("^.*delta_([0-9]{4})\\.csv$", "\\1", basename(file))
  cat("Processing year:", year, "\n")
  
  # read data
  data_1 <- read.csv(file, header = TRUE)
  # Ensure column order and names: group, delta15N, delta18O
  names(data_1) <- c("group", "delta15N", "delta18O")
  
  n_row_1 <- nrow(data_1)
  if (n_row_1 == 0) {
    cat("  No data for year", year, "\n")
    next
  }
  
  # Progress bar settings
  pb <- txtProgressBar(max = n_row_1, style = 3)
  progress <- function(n) setTxtProgressBar(pb, n)
  opts <- list(progress = progress)
  
  # Parallel computation of the source contribution for each sample
  result <- foreach::foreach(i = 1:n_row_1, .combine = rbind, 
                             .packages = c('siar'), 
                             .options.snow = opts) %dopar% {
                               row_data <- data_1[i, c("group", "delta15N", "delta18O")]
                               model1 <- siarsolomcmcv4(row_data, sources)
                               colMeans(model1$output[, 1:4])  # Return the mean of the four sources
                             }
  
  close(pb)
  
  # Convert to a data frame and add column names
  mat1 <- as.data.frame(result)
  names(mat1) <- c("IF", "MS", "SN", "AD")
  
  # Save results
  out_file <- file.path(output_dir, paste0("siar model results_", year, ".csv"))
  write.csv(mat1, out_file, row.names = FALSE)
  cat("  Saved:", out_file, "\n")
}

# Stop the cluster
stopCluster(cl)
cat("All years processed.\n")
