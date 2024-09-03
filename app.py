import pandas as pd
import streamlit as st

def load_data(file):
    """
    Reads the uploaded CSV file and returns a pandas DataFrame.
    """
    try:
        df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return None

def reset_filters():
    """
    Function to reset all filter selections by clearing session state.
    """
    for key in st.session_state.keys():
        if key.startswith("filter_"):
            del st.session_state[key]

def main():
    """
    Main function to run the Streamlit dashboard application.
    """
    st.title("Crunchbase Insight Dashboard")

    # File uploader for multiple CSV files
    uploaded_files = st.file_uploader("Choose CSV files", type="csv", accept_multiple_files=True)

    if uploaded_files:
        # Create a sidebar dropdown to select which file to analyze
        file_options = [file.name for file in uploaded_files]
        selected_file = st.sidebar.selectbox("Select a CSV file to analyze", file_options)

        # Find the file object for the selected file
        file_to_load = next(file for file in uploaded_files if file.name == selected_file)

        # Load the selected data
        df = load_data(file_to_load)

        if df is not None:
            st.write("### Data Preview")
            st.write(df.head())

            # Fill empty numeric columns with 0
            numeric_columns = df.select_dtypes(include=['number']).columns
            df[numeric_columns] = df[numeric_columns].fillna(0)

            # Sidebar filter options
            st.sidebar.header("Filters")

            # Clear filters button
            if st.sidebar.button("Clear Filters"):
                reset_filters()

            # Initialize session state for filters
            if 'filter_initialized' not in st.session_state:
                for column in df.columns:
                    if pd.api.types.is_numeric_dtype(df[column]):
                        st.session_state[f"filter_{column}"] = (float(df[column].min()), float(df[column].max()))
                    elif pd.api.types.is_datetime64_any_dtype(df[column]):
                        df[column] = pd.to_datetime(df[column], errors='coerce')  # Ensure column is datetime
                        st.session_state[f"filter_{column}"] = (df[column].min(), df[column].max())
                    else:
                        st.session_state[f"filter_{column}"] = []
                st.session_state['filter_initialized'] = True

            # Collect filter inputs from user
            filter_columns = list(df.columns)
            filters = {}

            for column in filter_columns:
                if pd.api.types.is_numeric_dtype(df[column]):
                    filters[column] = st.sidebar.slider(
                        f"Select range for {column}",
                        min_value=float(df[column].min()),
                        max_value=float(df[column].max()),
                        value=st.session_state[f"filter_{column}"]
                    )
                    st.session_state[f"filter_{column}"] = filters[column]
                elif pd.api.types.is_datetime64_any_dtype(df[column]):
                    min_date = df[column].min().date()
                    max_date = df[column].max().date()
                    filters[column] = st.sidebar.date_input(
                        f"Select date range for {column}",
                        value=st.session_state[f"filter_{column}"]
                    )
                    st.session_state[f"filter_{column}"] = filters[column]
                else:
                    unique_values = df[column].dropna().unique()
                    filters[column] = st.sidebar.multiselect(
                        f"Select {column}",
                        options=unique_values,
                        default=st.session_state[f"filter_{column}"]
                    )
                    st.session_state[f"filter_{column}"] = filters[column]

            # Apply filters
            filtered_data = df.copy()

            for column, filter_value in filters.items():
                if pd.api.types.is_numeric_dtype(df[column]):
                    filtered_data = filtered_data[
                        (filtered_data[column] >= filter_value[0]) &
                        (filtered_data[column] <= filter_value[1])
                    ]
                elif pd.api.types.is_datetime64_any_dtype(df[column]):
                    start_date, end_date = filter_value
                    filtered_data = filtered_data[
                        (filtered_data[column] >= pd.to_datetime(start_date)) &
                        (filtered_data[column] <= pd.to_datetime(end_date))
                    ]
                else:
                    if filter_value:
                        filtered_data = filtered_data[filtered_data[column].isin(filter_value)]

            st.write(f"### Filtered Data ({len(filtered_data)} rows)")
            st.write(filtered_data)

            # Provide an option to download filtered data
            csv = filtered_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download filtered data as CSV",
                data=csv,
                file_name='filtered_data.csv',
                mime='text/csv',
            )

if __name__ == "__main__":
    main()
