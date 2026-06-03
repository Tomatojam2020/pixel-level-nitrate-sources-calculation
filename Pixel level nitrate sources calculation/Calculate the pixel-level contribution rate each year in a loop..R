library(siar)
library(foreach)
library(doParallel)
library(doSNOW) 

# 设置工作路径
setwd("E:/博后/中国沿海硝酸盐同位素/SIAR")

# 输入目录（存放每年 delta_1990.csv 等文件）
input_dir <- "annual_tables"
# 输出目录
output_dir <- "annual_results"
if (!dir.exists(output_dir)) dir.create(output_dir, recursive = TRUE)

# 读取源数据（固定）
sources <- read.csv("source.csv", header = TRUE)

# 获取所有年份文件列表
files <- list.files(input_dir, pattern = "^delta_[0-9]{4}\\.csv$", full.names = TRUE)

# 注册并行后端（全局注册一次，提高效率）
cl <- makeCluster(16) 
registerDoSNOW(cl)

# 循环处理每一年
for (file in files) {
  # 提取年份
  year <- gsub("^.*delta_([0-9]{4})\\.csv$", "\\1", basename(file))
  cat("Processing year:", year, "\n")
  
  # 读取数据
  data_1 <- read.csv(file, header = TRUE)
  # 确保列顺序和名称：group, delta15N, delta18O
  names(data_1) <- c("group", "delta15N", "delta18O")
  
  n_row_1 <- nrow(data_1)
  if (n_row_1 == 0) {
    cat("  No data for year", year, "\n")
    next
  }
  
  # 进度条设置
  pb <- txtProgressBar(max = n_row_1, style = 3)
  progress <- function(n) setTxtProgressBar(pb, n)
  opts <- list(progress = progress)
  
  # 并行计算每个样本的源贡献
  result <- foreach::foreach(i = 1:n_row_1, .combine = rbind, 
                             .packages = c('siar'), 
                             .options.snow = opts) %dopar% {
                               row_data <- data_1[i, c("group", "delta15N", "delta18O")]
                               model1 <- siarsolomcmcv4(row_data, sources)
                               colMeans(model1$output[, 1:4])  # 返回四个源的均值
                             }
  
  close(pb)
  
  # 转换为数据框并添加列名
  mat1 <- as.data.frame(result)
  names(mat1) <- c("IF", "MS", "SN", "AD")
  
  # 保存结果
  out_file <- file.path(output_dir, paste0("singlepoint_", year, ".csv"))
  write.csv(mat1, out_file, row.names = FALSE)
  cat("  Saved:", out_file, "\n")
}

# 停止集群
stopCluster(cl)
cat("All years processed.\n")