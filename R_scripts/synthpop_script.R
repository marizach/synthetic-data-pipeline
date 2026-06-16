rm(list = ls())
cat("Starting\n")

suppressPackageStartupMessages(library(synthpop))
library(jsonlite)

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 4) stop("Use: Rscript script.R <train_csv> <out_csv>")

train_loc <- args[1]
synth_loc <- args[2]
zip_code_column <- args[3]
r_config <- fromJSON(args[4])


cat(train_loc, "\n")
cat(synth_loc, "\n")

# Normalizes path and filenames
train_loc <- normalizePath(train_loc, winslash = "/", mustWork = TRUE)
if (!grepl("\\.csv$", synth_loc, ignore.case = TRUE)) {
  synth_loc <- paste0(synth_loc, ".csv")
}
out_dir <- dirname(synth_loc)
if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
}

# Read data
df_fix <- read.csv(train_loc, check.names = TRUE)

# Force zip-like columns to factor (categorical)
zip_cols <- zip_code_column
for (z in zip_cols) df_fix[[z]] <- as.factor(df_fix[[z]])

# orders by number of missing values per variable, decreasing.
# Can be changed dependig on real case. For that, uncomment the rows below and in the calling function syn().
# na_counts <- colSums(is.na(df_fix))
# visit_seq <- names(df_fix)[order(na_counts, decreasing = FALSE)]

method_vec <- setNames(unlist(r_config$methods), names(r_config$methods))
visit_seq <- r_config$visit_sequence

mysyn_emp_last <- syn(
  df_fix,
  method = method_vec,
  minnumlevels = r_config$minnumlevels,
  maxfaclevels = r_config$maxfaclevels,
  visit.sequence = visit_seq,
  print.flag = TRUE
)

# saves as CSV:
tryCatch(
  {
    utils::write.csv(mysyn_emp_last$syn, file = synth_loc, row.names = FALSE)
    cat("Arquivo salvo em:", synth_loc, "\n")
  },
  error = function(e) {
    message("Erro ao salvar CSV em: ", synth_loc)
    message(conditionMessage(e))
    q(status = 1)
  }
)
