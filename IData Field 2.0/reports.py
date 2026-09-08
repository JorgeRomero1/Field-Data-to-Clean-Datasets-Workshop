import shutil
import subprocess
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "Reports"


def app():

    st.title("Reports")

    if not REPORTS_DIR.is_dir():
        st.error("Reports folder was not found.")
        return

    report_files = sorted(REPORTS_DIR.glob("*.qmd"))

    if not report_files:
        st.info("No Quarto report files were found in the Reports folder.")
        return

    report_options = {file.stem: file for file in report_files}

    TRIAL = st.selectbox("Trial", list(report_options.keys()))

    report_file = report_options[TRIAL]

    st.caption(f"Report template: {report_file.name}")

    if st.button("Generate Report", type="primary"):

        quarto_path = shutil.which("quarto")

        if quarto_path is None:
            st.error("Quarto was not found. Make sure Quarto is installed and available in your system PATH.")
            return

        try:

            with st.spinner(f"Generating {TRIAL} report..."):

                subprocess.run(
                    [quarto_path, "render", report_file.name, "--to", "html"],
                    cwd=REPORTS_DIR,
                    check=True,
                    capture_output=True,
                    text=True
                )

            html_file = report_file.with_suffix(".html")

            if not html_file.is_file():
                st.error("The report was rendered but the HTML file could not be found.")
                return

            st.success(f"{TRIAL} report generated successfully.")

            with open(html_file, "rb") as file:
                st.download_button("Download Report", data=file, file_name=html_file.name, mime="text/html")

        except subprocess.CalledProcessError as error:

            st.error("The Quarto report could not be generated.")

            if error.stderr:
                st.code(error.stderr)