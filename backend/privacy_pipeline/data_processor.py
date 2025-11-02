import pandas as pd

# --- NEW ANONYMIZATION FUNCTIONS ---

def pseudonymize_departments(df):
    """
    Replaces unique department names with generic tokens (e.g., DEPT_001).
    This is a form of pseudonymization.
    """
    # Find unique department names
    departments = df['Department'].unique()
    
    # Create a mapping from department name to a generic token
    mapping = {dept: f'DEPT_{i+1:03d}' for i, dept in enumerate(departments)}
    
    print("\n--- Applying Pseudonymization ---")
    print(f"Department mapping: {mapping}")
    
    # Replace the original names with the tokens
    df['Department'] = df['Department'].map(mapping)
    return df

def generalize_age(df):
    """
    Replaces specific ages with a general age range (e.g., 28 -> '20-30').
    This is a form of generalization.
    """
    # Define the age bins and their corresponding labels
    bins = [20, 30, 40, 50, 60, 70]
    labels = ['20-30', '31-40', '41-50', '51-60', '61-70']
    
    print("\n--- Applying Generalization ---")
    print("Grouping ages into ranges.")
    
    # Apply the generalization
    df['Age'] = pd.cut(df['Age'], bins=bins, labels=labels, right=True, include_lowest=True)
    return df


# --- EXISTING MINIMIZATION FUNCTION ---

def minimize_data(df, essential_columns):
    """
    Filters a DataFrame to keep only the essential columns.
    """
    print(f"Original columns: {df.columns.tolist()}")
    minimized_df = df[essential_columns]
    print(f"Minimized columns: {minimized_df.columns.tolist()}")
    
    original_cols = len(df.columns)
    minimized_cols = len(minimized_df.columns)
    reduction_ratio = (original_cols - minimized_cols) / original_cols
    print(f"Data Reduction Ratio (columns): {reduction_ratio:.2%}")
    
    return minimized_df


if __name__ == "__main__":
    ESSENTIAL_COLUMNS = ['Department', 'Age', 'Salary', 'Experience']
    
    try:
        # 1. Data Collection
        original_dataframe = pd.read_csv('employee_data.csv')
        print("--- Data Collection: Successfully loaded employee_data.csv ---")
        
        # 2. Data Minimization
        print("\n--- Applying Data Minimization ---")
        minimized_dataframe = minimize_data(original_dataframe, ESSENTIAL_COLUMNS)
        
        # --- 3. Data Anonymization ---
        # Apply the new anonymization functions to the minimized data
        anonymized_df = pseudonymize_departments(minimized_dataframe.copy())
        anonymized_df = generalize_age(anonymized_df)

        print("\n--- Final Anonymized and Minimized Dataset ---")
        print(anonymized_df)
        
    except FileNotFoundError:
        print("Error: 'employee_data.csv' not found. Make sure the file is in the same directory.")