# 📊 Data Quality & EDA Assistant

A powerful yet simple **Streamlit** web application to assist with **data quality assessment**, **exploratory data analysis (EDA)**, and **basic data cleaning** — all without writing a single line of code!

## 🚀 Features

* **Upload Support** for `.csv`, `.xlsx`, `.xls`, and `.json` files
* **Automatic Header Detection** and manual correction if needed
* **Data Preview & Summary** including shape, types, and descriptive statistics
* **Comprehensive Data Quality Report**:

  * Missing values
  * Duplicate rows
  * Constant columns
  * Mixed data types
  * Possible type mismatches
* **Visual Explorer** with:

  * Missing values heatmap
  * Numeric distribution histograms
  * Categorical count bar plots
  * Correlation heatmap
* **Data Cleaning Tools**:

  * Handle missing values (drop or fill with mean/median/mode)
  * Remove duplicates and constant columns
  * Convert object columns to numeric if possible
* **Export Cleaned Dataset** as CSV, Excel, or JSON

## 🛠 Built With

* [Python](https://www.python.org/)
* [Streamlit](https://streamlit.io/)
* [Pandas](https://pandas.pydata.org/)
* [Seaborn](https://seaborn.pydata.org/)
* [Matplotlib](https://matplotlib.org/)

## 📥 How to Use

1. Clone the repo:

   ```bash
   git clone https://github.com/your-username/data-quality-eda-app.git
   cd data-quality-eda-app
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   streamlit run app.py
   ```

4. Open the Streamlit interface in your browser and start analyzing your data!

## 📌 Use Case

Perfect for:

* Data Scientists doing initial data checks
* Analysts performing quick exploratory data analysis
* Anyone needing to inspect and clean tabular data visually
