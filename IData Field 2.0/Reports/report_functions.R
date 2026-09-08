# report_functions.R
# Reusable functions for IDataField trial reports

library(dplyr)
library(purrr)
library(lubridate)
library(stringr)
library(daymetr)
library(tibble)
library(ggplot2)
library(readr)

theme_nice <- function(font = "Open Sans") {
  theme_minimal(base_family = font) +
    theme(panel.grid.minor = element_blank(),
          plot.title = element_text(family = font, face = "bold"),
          axis.title = element_text(family = font, size = rel(1.4)),
          axis.text = element_text(size = rel(1)),
          strip.text = element_text(family = font, face = "bold",
                                    size = rel(1), hjust = 0),
          legend.position = "top",
          axis.line = element_line(),
          axis.ticks = element_line(size=1),
          #panel.grid = element_blank(),
          plot.background = element_rect(fill = "white", color = "white"),
          
          strip.background = element_rect(fill = "grey80", color = NA)
    )
}

# -------------------------------------------------------------------------
# General helpers
# -------------------------------------------------------------------------

clean_names_simple <- function(x) {
  x |>
    str_to_lower() |>
    str_replace_all("[^a-z0-9]+", "_") |>
    str_replace_all("^_|_$", "")
}

find_daymet_col <- function(data, patterns) {
  nms <- names(data)
  found <- nms[stringr::str_detect(stringr::str_to_lower(nms), stringr::str_c(patterns, collapse = "|"))]
  if (length(found) == 0) return(NA_character_)
  found[1]
}

# -------------------------------------------------------------------------
# Daymet helpers
# -------------------------------------------------------------------------

fill_missing_dec31_leap_years <- function(dat, start_date, end_date) {
  start_date <- as.Date(start_date)
  end_date <- as.Date(end_date)
  
  years_to_check <- seq(lubridate::year(start_date), lubridate::year(end_date), by = 1)
  years_to_check <- years_to_check[lubridate::leap_year(years_to_check)]
  
  added_rows <- purrr::map_dfr(years_to_check, function(yr) {
    dec30 <- as.Date(paste0(yr, "-12-30"))
    dec31 <- as.Date(paste0(yr, "-12-31"))
    
    if (dec31 < start_date || dec31 > end_date) return(tibble())
    if (dec31 %in% dat$Date) return(tibble())
    if (!dec30 %in% dat$Date) return(tibble())
    
    dat |>
      filter(Date == dec30) |>
      slice(1) |>
      mutate(Date = dec31, Year = lubridate::year(Date), Doy = lubridate::yday(Date))
  })
  
  bind_rows(dat, added_rows) |>
    arrange(Date)
}

get_daymet_one_station <- function(stations_df, station_name, force = FALSE) {
  st <- stations_df |>
    filter(station == station_name) |>
    slice(1)
  
  if (nrow(st) == 0) stop("Station not found in stations_df.")
  
  start_year <- lubridate::year(st$start_date)
  end_year <- lubridate::year(st$end_date)
  
  raw_daymet <- daymetr::download_daymet(site = st$station, lat = st$lat, lon = st$lon, start = start_year, end = end_year, internal = TRUE, silent = TRUE, force = force)
  
  if (is.data.frame(raw_daymet)) {
    dat <- tibble::as_tibble(raw_daymet)
  } else if (is.list(raw_daymet) && "data" %in% names(raw_daymet)) {
    dat <- tibble::as_tibble(raw_daymet$data)
  } else {
    stop("Could not find the Daymet data table in the downloaded object.")
  }
  
  names(dat) <- clean_names_simple(names(dat))
  
  year_col <- find_daymet_col(dat, c("^year$"))
  yday_col <- find_daymet_col(dat, c("^yday$", "^doy$", "day_of_year"))
  tmax_col <- find_daymet_col(dat, c("^tmax"))
  tmin_col <- find_daymet_col(dat, c("^tmin"))
  prcp_col <- find_daymet_col(dat, c("^prcp", "precip"))
  srad_col <- find_daymet_col(dat, c("^srad", "solar"))
  dayl_col <- find_daymet_col(dat, c("^dayl", "day_length"))
  
  needed <- c(year_col, yday_col, tmax_col, tmin_col, prcp_col, srad_col, dayl_col)
  
  if (any(is.na(needed))) {
    stop(paste0("Could not identify the needed Daymet columns.\nColumns found after cleaning:\n", paste(names(dat), collapse = ", ")))
  }
  
  out <- dat |>
    transmute(
      station = st$station,
      Date = as.Date(paste(.data[[year_col]], .data[[yday_col]], sep = "-"), format = "%Y-%j"),
      Year = as.integer(.data[[year_col]]),
      Doy = as.integer(.data[[yday_col]]),
      Tmax = as.numeric(.data[[tmax_col]]),
      Tmin = as.numeric(.data[[tmin_col]]),
      Precip = as.numeric(.data[[prcp_col]]),
      Sr = (as.numeric(.data[[srad_col]]) * as.numeric(.data[[dayl_col]])) / 1000000
    )
  
  out |>
    fill_missing_dec31_leap_years(start_date = st$start_date, end_date = st$end_date) |>
    filter(Date >= st$start_date, Date <= st$end_date) |>
    mutate(Year = lubridate::year(Date), Doy = lubridate::yday(Date), across(c(Tmax, Tmin, Precip, Sr), ~ round(.x, 1))) |>
    arrange(Date)
}

get_daymet_many_stations <- function(stations_df, force = FALSE) {
  if (nrow(stations_df) == 0) stop("No stations found.")
  
  out <- purrr::map_dfr(seq_len(nrow(stations_df)), function(i) {
    st_i <- stations_df[i, ]
    message("Downloading ", st_i$station, " (", i, " of ", nrow(stations_df), ")")
    
    tryCatch(
      get_daymet_one_station(stations_df = st_i, station_name = st_i$station, force = force),
      error = function(e) {
        warning("Skipped ", st_i$station, ": ", conditionMessage(e))
        tibble()
      }
    )
  })
  
  if (nrow(out) == 0) stop("The Daymet request ran, but no data were returned.")
  
  out |>
    distinct() |>
    arrange(station, Date)
}

prepare_daymet_stations <- function(site_info, n_years = 25) {
  last_year <- max(lubridate::year(site_info$`Harvest date`), na.rm = TRUE)
  first_year <- last_year - n_years + 1
  
  site_info |>
    distinct(Site, Latitude, Longitude) |>
    transmute(
      station = Site,
      lat = Latitude,
      lon = Longitude,
      start_date = as.Date(paste0(first_year - 1, "-01-01")),
      end_date = as.Date(paste0(last_year, "-12-31"))
    )
}

load_daymet_weather <- function(site_info, cache_file = NULL, n_years = 25, force = FALSE) {
  if (!is.null(cache_file) && file.exists(cache_file) && !force) {
    return(readr::read_csv(cache_file, show_col_types = FALSE) |> mutate(Date = as.Date(Date)))
  }
  
  stations_df <- prepare_daymet_stations(site_info, n_years = n_years)
  
  weather_daily <- get_daymet_many_stations(stations_df = stations_df, force = force) |>
    left_join(site_info |> distinct(Site, Location), by = c("station" = "Site"))
  
  if (!is.null(cache_file)) {
    dir.create(dirname(cache_file), recursive = TRUE, showWarnings = FALSE)
    readr::write_csv(weather_daily, cache_file)
  }
  
  weather_daily
}

# -------------------------------------------------------------------------
# Growing-season weather
# -------------------------------------------------------------------------

prepare_growing_season_windows <- function(site_info, n_years = 25) {
  last_year <- max(lubridate::year(site_info$`Harvest date`), na.rm = TRUE)
  first_year <- last_year - n_years + 1
  
  site_dates <- site_info |>
    group_by(Location, Site) |>
    summarise(
      sow_doy = round(mean(lubridate::yday(`Sowing date`), na.rm = TRUE)),
      harvest_doy = round(mean(lubridate::yday(`Harvest date`), na.rm = TRUE)),
      .groups = "drop"
    ) |>
    mutate(
      sow_md = format(as.Date("2001-01-01") + days(sow_doy - 1), "%m-%d"),
      harvest_md = format(as.Date("2001-01-01") + days(harvest_doy - 1), "%m-%d")
    )
  
  season_windows <- tidyr::crossing(site_dates, Season = first_year:last_year) |>
    mutate(
      Sowing = lubridate::ymd(paste0(Season - 1, "-", sow_md)),
      Harvest = lubridate::ymd(paste0(Season, "-", harvest_md))
    )
  
  actual_dates <- site_info |>
    transmute(
      Site,
      Season = lubridate::year(`Harvest date`),
      Sowing_actual = `Sowing date`,
      Harvest_actual = `Harvest date`
    )
  
  season_windows |>
    left_join(actual_dates, by = c("Site", "Season")) |>
    mutate(Sowing = coalesce(Sowing_actual, Sowing), Harvest = coalesce(Harvest_actual, Harvest)) |>
    select(Location, Site, Season, Sowing, Harvest)
}

prepare_cumulative_rainfall <- function(weather_daily, site_info, n_years = 25) {
  season_windows <- prepare_growing_season_windows(site_info = site_info, n_years = n_years)
  trial_years <- sort(unique(lubridate::year(site_info$`Harvest date`)))
  
  weather_daily |>
    inner_join(season_windows, by = c("Location", "station" = "Site"), relationship = "many-to-many") |>
    filter(Date >= Sowing, Date <= Harvest) |>
    arrange(Location, Season, Date) |>
    group_by(Location, station, Season) |>
    mutate(day = as.integer(Date - Sowing), cumulative_rainfall = cumsum(tidyr::replace_na(Precip, 0))) |>
    ungroup() |>
    mutate(series = if_else(Season %in% trial_years, as.character(Season), "All Years"))
}

plot_cumulative_rainfall <- function(rainfall_data, site_info, ncol = 3) {
  trial_years <- sort(unique(lubridate::year(site_info$`Harvest date`)))
  year_colors <- setNames(scales::hue_pal()(length(trial_years)), as.character(trial_years))
  rainfall_colors <- c("All Years" = "grey75", year_colors)
  
  ggplot() +
    geom_line(
      data = filter(rainfall_data, series == "All Years"),
      aes(x = day, y = cumulative_rainfall, group = interaction(Location, Season), color = series),
      linewidth = 0.4
    ) +
    geom_line(
      data = filter(rainfall_data, series != "All Years"),
      aes(x = day, y = cumulative_rainfall, group = interaction(Location, Season), color = series),
      linewidth = 1.2
    ) +
    facet_wrap(~ Location, ncol = ncol) +
    scale_color_manual(values = rainfall_colors, breaks = c(as.character(trial_years), "All Years")) +
    labs(x = "Days after sowing", y = "Cumulative rainfall (mm)", color = "Growing season") +
    theme_bw(base_size = 13) +
    theme(strip.text = element_text(size = 12), legend.position = "right")
}
