import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import io
import uuid

# Set page config
st.set_page_config(page_title="Data Quality & EDA App", layout="wide")

# Title and instructions
st.title("📊 Data Quality & EDA Assistant")
st.markdown("Upload your dataset to begin exploring and checking its quality.")

# File upload
uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx", "xls", "json"])

# Load dataset based on file type
def load_dataset(file, has_headers):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, header=0 if has_headers else None)
        elif file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            df = pd.read_excel(file, header=0 if has_headers else None)
        elif file.name.endswith('.json'):
            df = pd.read_json(file)
            return df, False  # JSON always has headers
        else:
            return None, False
        return df, not has_headers  # Marked as needing header fix if no headers
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, False

def headers_suspect(df):
    # Case 1: unnamed or numeric headers
    if all(str(col).lower().startswith("unnamed") or str(col).isdigit() for col in df.columns):
        return True
    return False

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
    # Ask user if the dataset has headers
    has_headers = st.radio(
        "Does your dataset include headers in the first row?",
        ["Yes", "No"],
        index=0
    )

    df, needs_header_fix = load_dataset(uploaded_file, has_headers == "Yes")

    if df is not None:
        st.success("✅ File successfully loaded!")
        if needs_header_fix:
            st.warning("🚨 No headers detected. Please provide column headers.")
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
        else:
            # Option to edit headers if they exist
            edit_headers = st.checkbox("Edit column header names?")
            if edit_headers:
                default_headers = df.columns.tolist()
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
            elif headers_suspect(df):
                st.warning("🚨 Headers look suspicious (e.g., unnamed or numeric).")
                update_headers = st.checkbox("Update column headers?")
                if update_headers:
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
            st.dataframe(df.head(df.shape[0))

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
            null_cols = df_clean.columns[df_clean.isnull().any()].tolist()
            if null_cols:
                selected_null_col = st.selectbox("Select a column with missing values:", null_cols)
                missing_action = st.radio(
                    f"Select action for missing values in '{selected_null_col}':",
                    ["Do Nothing", "Drop Rows", "Fill with Mean", "Fill with Median", "Fill with Mode", "Add Values Manually"],
                    key=f"missing_action_{selected_null_col}"
                )

                if missing_action == "Drop Rows":
                    df_clean = df_clean.dropna(subset=[selected_null_col])
                elif missing_action == "Fill with Mean" and pd.api.types.is_numeric_dtype(df_clean[selected_null_col]):
                    df_clean[selected_null_col] = df_clean[selected_null_col].fillna(df_clean[selected_null_col].mean())
                elif missing_action == "Fill with Median" and pd.api.types.is_numeric_dtype(df_clean[selected_null_col]):
                    df_clean[selected_null_col] = df_clean[selected_null_col].fillna(df_clean[selected_null_col].median())
                elif missing_action == "Fill with Mode":
                    df_clean[selected_null_col] = df_clean[selected_null_col].fillna(df_clean[selected_null_col].mode()[0])
                elif missing_action == "Add Values Manually":
                    manual_value = st.text_input(f"Enter a value to fill missing entries in '{selected_null_col}':", key=f"manual_{selected_null_col}")
                    if manual_value:
                        try:
                            # Try to convert to numeric if the column is numeric
                            if pd.api.types.is_numeric_dtype(df_clean[selected_null_col]):
                                manual_value = float(manual_value)
                            df_clean[selected_null_col] = df_clean[selected_null_col].fillna(manual_value)
                        except ValueError:
                            st.error("❌ Invalid value for the column type.")
            else:
                st.info("No columns with missing values found.")

            # Duplicate Rows
            st.markdown("### 2. 🧬 Remove Duplicate Rows")
            if df_clean.duplicated().sum() > 0:
                dup_cols = st.multiselect(
                    "Select columns to check for duplicates (all columns if none selected):",
                    df_clean.columns.tolist(),
                    key="dup_cols"
                )
                if st.button("Drop duplicate rows", key="drop_duplicates"):
                    if dup_cols:
                        df_clean = df_clean.drop_duplicates(subset=dup_cols)
                    else:
                        df_clean = df_clean.drop_duplicates()
            else:
                st.info("No duplicate rows found.")

            # Constant Columns
            st.markdown("### 3. 🧱 Remove Constant Columns")
            st.markdown("Removes columns with only one unique value (including NaN), as they provide no variability for analysis.")
            constant_cols = [col for col in df_clean.columns if df_clean[col].nunique(dropna=False) <= 1]
            if constant_cols:
                selected_const_cols = st.multiselect(
                    "Select constant columns to remove:",
                    constant_cols,
                    key="const_cols"
                )
                if st.button("Drop selected constant columns", key="drop_constant"):
                    df_clean = df_clean.drop(columns=selected_const_cols)
            else:
                st.info("No constant columns found.")

            # Object to Numeric Conversion
            st.markdown("### 4. 🔁 Convert Object Columns to Numeric (if possible)")
            st.markdown("Converts string columns that contain numeric values (e.g., '123', '456.7') to numeric types for analysis.")
            object_cols = df_clean.select_dtypes(include='object').columns.tolist()
            convertible_cols = []
            for col in object_cols:
                try:
                    pd.to_numeric(df_clean[col])
                    convertible_cols.append(col)
                except:
                    pass
            if object_cols:
                st.write("Object columns (convertible to numeric are marked with *):")
                display_cols = [f"{col}*" if col in convertible_cols else col for col in object_cols]
                selected_obj_cols = st.multiselect(
                    "Select object columns to convert to numeric:",
                    display_cols,
                    key="obj_cols"
                )
                # Strip the * for actual column names
                selected_obj_cols = [col.rstrip('*') for col in selected_obj_cols]
                if st.button("Convert selected columns to numeric", key="convert_numeric"):
                    for col in selected_obj_cols:
                        try:
                            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                        except:
                            pass
            else:
                st.info("No object columns found.")

            # Change Data Types
            st.markdown("### 5. 🔄 Change Column Data Types")
            st.markdown("View and modify the data type of each column. Preview shows the first few values.")
            for col in df_clean.columns:
                st.markdown(f"**Column: {col}**")
                st.write(f"Current dtype: {df_clean[col].dtype}")
                st.write("Preview:", df_clean[col].head().to_list())
                new_dtype = st.selectbox(
                    f"Select new dtype for '{col}':",
                    ["No Change", "int", "float", "string", "boolean", "datetime", "category"],
                    key=f"dtype_{col}"
                )
                if new_dtype != "No Change":
                    try:
                        if new_dtype == "int":
                            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').astype('Int64')  # Nullable integer
                        elif new_dtype == "float":
                            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                        elif new_dtype == "string":
                            df_clean[col] = df_clean[col].astype(str)
                        elif new_dtype == "boolean":
                            df_clean[col] = df_clean[col].map({'True': True, 'False': False, True: True, False: False, 1: True, 0: False}).astype('boolean')
                        elif new_dtype == "datetime":
                            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                        elif new_dtype == "category":
                            df_clean[col] = df_clean[col].astype('category')
                    except Exception as e:
                        st.error(f"❌ Failed to convert '{col}' to {new_dtype}: {e}")

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
    st.info("📎 Please upload a dataset file to proceed.")
