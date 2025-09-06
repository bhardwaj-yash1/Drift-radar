import pandas as pd
import numpy as np
import os
import shutil

# --- Project Root & Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "telco_churn.csv")
OUTPUT_BATCHES_DIR = os.path.join(PROJECT_ROOT, "scripts", "data_streams")

def data_clean_and_preprocess(radar: pd.DataFrame):
    if 'Unnamed: 0' in radar.columns:
        radar = radar.drop('Unnamed: 0', axis=1)
    if 'customerID' in radar.columns:
        radar = radar.drop('customerID', axis=1)
    radar['TotalCharges'] = pd.to_numeric(radar['TotalCharges'], errors='coerce')
    radar.dropna(subset=['TotalCharges'], inplace=True)
    if 'Churn' in radar.columns:
        radar['Churn'] = radar['Churn'].map({'Yes': 1, 'No': 0})
    binary_map = {'yes': 1, 'no': 0, 'no internet service': 0, 'no phone service': 0,
                  'true': 1, 'false': 0, '1': 1, '0': 0}
    for col in ['SeniorCitizen', 'Partner', 'Dependents', 'PhoneService',
                'MultipleLines', 'OnlineSecurity', 'OnlineBackup',
                'DeviceProtection', 'TechSupport', 'StreamingTV',
                'StreamingMovies', 'PaperlessBilling']:
        if col in radar.columns:
            radar[col] = radar[col].astype(str).str.lower().map(binary_map)
    return radar

def inject_drift(input_path, output_dir, num_batches=10, batch_size=700):
    print("Starting drift injection...")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    df = pd.read_csv(input_path)
    df = data_clean_and_preprocess(df)
    df.dropna(subset=['Churn'], inplace=True)

    for i in range(1, num_batches + 1):
        batch = df.sample(n=batch_size, replace=True).copy()

        if i > 5:
            batch['MonthlyCharges'] *= (1 + (i - 5) * 0.1)
            print(f"Batch {i}: Injected numerical drift")

        if i > 7 and 'Contract' in batch.columns:
            idx = batch[batch['Contract'] == 'One year'].sample(frac=0.2, replace=False).index
            batch.loc[idx, 'Contract'] = 'Month-to-month'
            print(f"Batch {i}: Injected categorical drift")

        batch.to_csv(os.path.join(output_dir, f"batch_{i}.csv"), index=False)
    print("✅ Drift batches ready.")

if __name__ == "__main__":
    inject_drift(ORIGINAL_DATA_PATH, OUTPUT_BATCHES_DIR)
