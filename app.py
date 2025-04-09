import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import io


# Set page config
st.set_page_config(page_title="Data Quality & EDA App", layout="wide")

# Title and instructions
st.title("📊 Data Quality & EDA Assistant")
st.markdown("Upload your dataset to begin exploring and checking its quality.")

# File upload
uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx", "xls", "json"])

# Load dataset based on file type
def load_dataset(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, header=None)  # Force no header for now
        elif file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            df = pd.read_excel(file, header=None)
        elif file.name.endswith('.json'):
            df = pd.read_json(file)
            return df, False  # JSON always has headers
        else:
            return None, False
        return df, True  # Marked as potentially needing header fix
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, False

def headers_suspect(df):
    # Case 1: unnamed or numeric headers
    if all(str(col).lower().startswith("unnamed") or str(col).isdigit() for col in df.columns):
        return True
    return False

# Add this function after `load_dataset()`
def check_data_quality(df):
    report = []

    # Unnamed headers
    unnamed = [col for col in df.columns if "unnamed" in str(col).lower()]
    if unnamed:
        report.append({
            "Issue": "Missing/Unnamed headers",
            "Column": ", ".join(unnamed),
            "Details": f"{len(unnamed)} unnamed columns"
        })

    # Missing values
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    for col, count in nulls.items():
        pct = (count / len(df)) * 100
        report.append({
            "Issue": "Missing values",
            "Column": col,
            "Details": f"{count} missing ({pct:.2f}%)"
        })

    # Duplicate rows
    dupes = df.duplicated().sum()
    if dupes > 0:
        report.append({
            "Issue": "Duplicate rows",
            "Column": "-",
            "Details": f"{dupes} duplicate rows"
        })

    # Constant columns
    const_cols = [col for col in df.columns if df[col].nunique(dropna=False) <= 1]
    for col in const_cols:
        report.append({
            "Issue": "Constant column",
            "Column": col,
            "Details": "Only one unique value"
        })

    # Mixed data types
    for col in df.columns:
        types = df[col].map(type).nunique()
        if types > 1:
            report.append({
                "Issue": "Mixed data types",
                "Column": col,
                "Details": "Contains multiple data types"
            })

    # Object columns that could be numeric
    for col in df.select_dtypes(include='object'):
        try:
            pd.to_numeric(df[col])
            report.append({
                "Issue": "Possible numeric column as object",
                "Column": col,
                "Details": "Can be converted to numeric"
            })
        except:
            pass

    return pd.DataFrame(report)


# Main App Logic
if uploaded_file:
    df, needs_header_fix = load_dataset(uploaded_file)

    if df is not None:
        st.success("✅ File successfully loaded!")
        if needs_header_fix and headers_suspect(df):
            st.warning("🚨 No headers detected or headers look incorrect.")

            default_headers = [f"Column_{i}" for i in range(df.shape[1])]
            header_input = st.text_input(
                f"Enter comma-separated headers for {df.shape[1]} columns:",
                value=",".join(default_headers)
            )

            if header_input:
                headers = [h.strip() for h in header_input.split(",")]
                if len(headers) == df.shape[1]:
                    df.columns = headers
                else:
                    st.error("❌ Number of headers does not match number of columns!")

        # Tabs: Preview | Quality Check (To be added later)
        # Tabs for various views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📁 Preview Dataset",
            "📋 Summary Stats",
            "🧹 Data Quality",
            "📊 Visual Explorer",
            "🧼 Clean & Export"
        ])

        with tab1:
            st.subheader("🔍 Dataset Preview")
            st.write(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            st.dataframe(df.head())

        with tab2:
            st.subheader("📈 Descriptive Statistics")
            st.write(df.describe(include='all').T)

        with tab3:
            st.subheader("🧹 Data Quality Report")
            quality_df = check_data_quality(df)

            if not quality_df.empty:
                st.dataframe(quality_df)
            else:
                st.success("🎉 No major issues found in your dataset!")

        with tab4:
            st.subheader("📊 Visual Explorer")

            st.markdown("### 1. 🔥 Missing Values Heatmap")
            if df.isnull().sum().sum() > 0:
                fig, ax = plt.subplots(figsize=(12, 4))
                sns.heatmap(df.isnull(), cbar=False, cmap="YlOrRd", yticklabels=False, ax=ax)
                st.pyplot(fig)
            else:
                st.info("No missing values to display.")

            st.markdown("### 2. 📉 Numeric Distributions")
            num_cols = df.select_dtypes(include='number').columns.tolist()
            if num_cols:
                selected_num_col = st.selectbox("Choose a numeric column", num_cols)
                fig, ax = plt.subplots()
                sns.histplot(df[selected_num_col].dropna(), kde=True, ax=ax)
                st.pyplot(fig)
            else:
                st.warning("No numeric columns found.")

            st.markdown("### 3. 📊 Categorical Counts")
            cat_cols = df.select_dtypes(include='object').columns.tolist()
            if cat_cols:
                selected_cat_col = st.selectbox("Choose a categorical column", cat_cols)
                fig, ax = plt.subplots()
                df[selected_cat_col].value_counts().plot(kind='bar', ax=ax, color='skyblue')
                st.pyplot(fig)
            else:
                st.warning("No categorical columns found.")

            st.markdown("### 4. 🤝 Correlation Heatmap")
            if len(num_cols) >= 2:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.heatmap(df[num_cols].corr(), annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
                st.pyplot(fig)
            else:
                st.info("Need at least 2 numeric columns for correlation heatmap.")

        with tab5:
            st.subheader("🧼 Clean & Export Your Dataset")

            df_clean = df.copy()

            # Missing Values Handling
            st.markdown("### 1. 🕳 Handle Missing Values")
            missing_action = st.radio("Select action for missing values:", 
                                    ["Do Nothing", "Drop Rows", "Fill with Mean", "Fill with Median", "Fill with Mode"])

            if missing_action == "Drop Rows":
                df_clean = df_clean.dropna()
            elif missing_action == "Fill with Mean":
                df_clean = df_clean.fillna(df_clean.mean(numeric_only=True))
            elif missing_action == "Fill with Median":
                df_clean = df_clean.fillna(df_clean.median(numeric_only=True))
            elif missing_action == "Fill with Mode":
                for col in df_clean.columns:
                    if df_clean[col].isnull().sum() > 0:
                        df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0])

            # Duplicate Rows
            st.markdown("### 2. 🧬 Remove Duplicate Rows")
            if st.checkbox("Drop duplicate rows"):
                df_clean = df_clean.drop_duplicates()

            # Constant Columns
            st.markdown("### 3. 🧱 Remove Constant Columns")
            if st.checkbox("Drop constant columns (only one unique value)"):
                constant_cols = [col for col in df_clean.columns if df_clean[col].nunique() <= 1]
                df_clean = df_clean.drop(columns=constant_cols)

            # Object to Numeric Conversion
            st.markdown("### 4. 🔁 Convert Object Columns to Numeric (if possible)")
            if st.checkbox("Convert eligible object columns to numeric"):
                for col in df_clean.select_dtypes(include='object').columns:
                    try:
                        df_clean[col] = pd.to_numeric(df_clean[col])
                    except:
                        pass

            # Preview Cleaned Data
            st.markdown("### ✅ Cleaned Dataset Preview")
            st.dataframe(df_clean.head())

            # Download Cleaned Dataset
            st.markdown("### 💾 Download Cleaned Dataset")
            file_type = st.selectbox("Select download format", ["CSV", "Excel", "JSON"])

            if file_type == "CSV":
                cleaned_data = df_clean.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", cleaned_data, "cleaned_data.csv", "text/csv")
            elif file_type == "Excel":
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_clean.to_excel(writer, index=False)
                st.download_button("Download Excel", output.getvalue(), "cleaned_data.xlsx")
            elif file_type == "JSON":
                cleaned_data = df_clean.to_json(orient="records").encode("utf-8")
                st.download_button("Download JSON", cleaned_data, "cleaned_data.json", "application/json")

        
    else:
        st.error("❌ Failed to load dataset.")

else:
    st.info("📎 Please upload a dataset file to proceed.")
