"""Data collection progress for a trial.

How complete is each measurement, per location?

The denominator comes from the experimental design in metadata/Labels.csv
(TRT x REPS), not from the data files. A data file only contains plots that
someone already measured, so using it as the total would make the denominator
shrink along with the progress and every bar would read as finished. The design
is fixed regardless of how much work has been done, which is what a progress
tracker needs.

The numerator is the count of non-empty values in the trial's merged file.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import theme

BASE_DIR = Path(__file__).resolve().parent
LABELS_FILE = BASE_DIR / "metadata" / "Labels.csv"
SEASONS_DIR = BASE_DIR.parent

INTRO = """
Track data collection progress across trials, seasons, and locations to identify missing records for each activity.
"""

TRAITS_NOTE = "Click a trait to view detailed progress and the IDs of plots with missing records."

# Measurements grouped the way the work is actually done in the field, so a
# group can be collapsed to one line and opened to see its parts.
GROUPS = {
    "Partitioning": {
        "Head Number": "Head_No",
        "Head Weight": "HeadWeight_g",
        "Stover Weight": "StoverWeight_g",
        "Whole Plant Weight": "WholePlantWeight_g",
    },
    "Thousand Kernel Weight(TKW)": {
        "Thousand Kernel Weight": "ThousandKernelWeight_g",
    },
    "Protein": {
        "Grain Protein": "GrainProtein_%",
    },
    "Plant Height": {
        "Reading 1": "PlantHeight1_cm",
        "Reading 2": "PlantHeight2_cm",
        "Reading 3": "PlantHeight3_cm",
        "Reading 4": "PlantHeight4_cm",
        "Reading 5": "PlantHeight5_cm",
    },
}

GREEN = "#2E7D53"

ALL_LOCATIONS = "All locations"


def _season_folder(year):
    """Year 25 -> 'SEASON 2024-25'."""
    return f"SEASON {2000 + int(year) - 1}-{int(year)}"


def _trial_dir(year, trial):
    return SEASONS_DIR / _season_folder(year) / "01-Data" / trial


def _inject_css():
    st.markdown(
        f"""
        <style>
        .idf-prog-row {{
            display: flex;
            align-items: center;
            gap: 0.9rem;
            margin: 0.5rem 0;
        }}
        .idf-prog-label {{
            flex: 0 0 11rem;
            color: {theme.COLORS["navy"]};
            font-weight: 600;
            font-size: 0.92rem;
        }}
        .idf-prog-track {{
            flex: 1 1 auto;
            height: 20px;
            border-radius: 6px;
            background: {theme.COLORS["sky_soft"]};
            border: 1px solid {theme.COLORS["gray_line"]};
            overflow: hidden;
        }}
        .idf-prog-fill {{
            height: 100%;
            background: {theme.COLORS["navy"]};
        }}
        .idf-prog-fill.done {{
            background: {GREEN};
        }}
        .idf-prog-count {{
            flex: 0 0 10.5rem;
            text-align: right;
            font-variant-numeric: tabular-nums;
            color: {theme.COLORS["navy"]};
            font-weight: 600;
            font-size: 0.92rem;
        }}
        .idf-prog-mark {{
            flex: 0 0 1.6rem;
            font-size: 1.05rem;
            text-align: center;
        }}
        .idf-prog-idle {{
            color: {theme.COLORS["gray_text"]};
            font-style: italic;
            font-size: 0.88rem;
            margin: 0.5rem 0 0.5rem 11.9rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _pct(done, total):
    return (done / total * 100) if total else 0.0


def _progress_row(label, done, total):
    pct = _pct(done, total)
    complete = total > 0 and done >= total
    st.markdown(
        f"""
        <div class="idf-prog-row">
            <div class="idf-prog-label">{label}</div>
            <div class="idf-prog-track">
                <div class="idf-prog-fill{' done' if complete else ''}"
                     style="width:{pct:.1f}%"></div>
            </div>
            <div class="idf-prog-count">{done} / {total} ({pct:.1f}%)</div>
            <div class="idf-prog-mark">{'&#10004;' if complete else ''}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _idle_row(label):
    st.markdown(
        f'<div class="idf-prog-idle">{label} &mdash; not measured this season</div>',
        unsafe_allow_html=True,
    )


def _expected_by_location(labels, trial, year):
    """Plots the design calls for: TRT x REPS per location."""
    rows = labels[(labels.TRIAL_SHORT == trial) & (labels.YEAR == year)]

    return (rows.TRT * rows.REPS).groupby(rows.LOC_SHORT).sum()


def _plot_roster(year, trial):
    """Known plot numbers per location, used to name the missing samples.

    The design gives a count, not plot numbers, so pull the numbers from the
    field file when it is there. Plots the roster cannot account for are
    reported as a count instead of being silently dropped.
    """
    field_file = _trial_dir(year, trial) / f"{trial}_field.csv"

    if not field_file.is_file():
        return None

    field = pd.read_csv(field_file)

    return set(zip(field.LOC_SHORT, field.Plot))


def _missing_by_site(data, columns, roster, scope):
    """Plots still owed for a group, as {site: [plot, ...]}.

    Reported per group rather than per measurement because the measurements in
    a group are taken from the same sample: a plot that is missing one is
    almost always missing the rest, so four identical lists would be noise. A
    plot counts as owed when any measurement in the group is absent, which is
    the same rule the group's bar uses.
    """
    incomplete = data.loc[~data[columns].notna().all(axis=1), ["Site", "Plot"]]

    owed = set(zip(incomplete.Site, incomplete.Plot))

    # Plots the design expects that never made it into the file at all.
    if roster is not None:
        present = set(zip(data.Site, data.Plot))
        owed |= {p for p in roster if p[0] in scope and p not in present}

    by_site = {}

    for site, plot in sorted(owed):
        by_site.setdefault(site, []).append(plot)

    return by_site


def app():
    st.title("Data Collection Progress")

    theme.intro(INTRO)

    if not LABELS_FILE.is_file():
        st.error("Labels.csv was not found in the metadata folder.")
        return

    labels = pd.read_csv(LABELS_FILE)

    _inject_css()

    # Selection
    col1, col2, col3 = st.columns(3)

    with col1:
        trial = st.selectbox("Trial", sorted(labels.TRIAL_SHORT.dropna().unique()))

    with col2:
        years = sorted(labels.loc[labels.TRIAL_SHORT == trial, "YEAR"].dropna().unique())
        year = st.selectbox("Season (harvest year)", years)

    expected = _expected_by_location(labels, trial, year)

    with col3:
        location = st.selectbox("Location", [ALL_LOCATIONS] + list(expected.index), help='Select a specific field site or choose "All Locations" to view aggregated progress.')

    merged_file = _trial_dir(year, trial) / f"{trial}_merged.csv"

    if not merged_file.is_file():
        st.warning(
            f"No merged file yet for {trial} {_season_folder(year)}. "
            f"Expected it at: {merged_file}"
        )
        return

    merged = pd.read_csv(merged_file)

    # Scope to the chosen location
    if location == ALL_LOCATIONS:
        data = merged
        total = int(expected.sum())
        scope = list(expected.index)
    else:
        data = merged[merged.Site == location]
        total = int(expected.get(location, 0))
        scope = [location]

    st.caption(
        f"{total} plots expected from the experimental design "
        f"({'all locations' if location == ALL_LOCATIONS else location})."
    )

    st.subheader("Activities progress", help=TRAITS_NOTE)

    roster = _plot_roster(year, trial)

    for group, measurements in GROUPS.items():
        # A column absent from the file, or empty across the whole season, is
        # something this season did not measure -- not work left to do. Judged
        # on the full trial so filtering to one location cannot mislabel it.
        present = {
            label: col for label, col in measurements.items() if col in merged.columns
        }
        active = {
            label: col for label, col in present.items() if merged[col].notna().any()
        }
        idle = [label for label in present if label not in active]

        if not present:
            continue

        if not active:
            st.markdown(f"**{group}** &mdash; not measured this season")
            continue

        # A plot counts toward the group only once every active measurement in
        # it is on file, which is what "this plot's partitioning is done" means.
        group_done = int(data[list(active.values())].notna().all(axis=1).sum())
        group_pct = _pct(group_done, total)
        group_complete = total > 0 and group_done >= total

        header = f"{group} — {group_done} / {total} ({group_pct:.1f}%)"

        with st.expander(f"{header}  ✅" if group_complete else header):
            for label, column in active.items():
                _progress_row(label, int(data[column].notna().sum()), total)

            for label in idle:
                _idle_row(label)

            if group_complete:
                continue

            st.divider()

            gap = total - group_done

            if not st.checkbox(f"Show missing ({gap})", key=f"miss_{group}"):
                continue

            by_site = _missing_by_site(data, list(active.values()), roster, scope)
            named = sum(len(plots) for plots in by_site.values())

            lines = ["**Missing:**", ""]

            for site, plots in by_site.items():
                listed = ", ".join(str(p) for p in plots)
                lines.append(f"- **{site}** ({len(plots)}): [{listed}]")

            st.markdown("\n".join(lines))

            if gap - named > 0:
                st.info(
                    f"{gap - named} more plot(s) are expected by the design but have "
                    "no record in either the merged or the field file, so their "
                    "plot numbers cannot be listed."
                )
