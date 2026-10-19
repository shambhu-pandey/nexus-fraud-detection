# Installation Guide

## Requirements

- Python 3.10 to 3.12 recommended
- pip
- 4 GB RAM minimum; more memory is useful for model training
- Internet access only for the initial PaySim/CICIDS2017 dataset download and dependency installation

## Set up the environment (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run `python -m pip` using `.venv\Scripts\python.exe` directly.

## Prepare data

The repository includes PaySim data and generated BankSim/IEEE demo files. CICIDS2017 is downloaded and prepared with:

```powershell
python .\download_datasets.py
```

The script checks the archive before replacing the local file, then combines its eight CSV members into `data/cicids.csv` with one header. To regenerate the synthetic BankSim and IEEE demo files:

```powershell
python .\generate_datasets.py
```

Those generated files are for demonstrations and are not the original BankSim or IEEE-CIS benchmark datasets. See [data/DATA_SOURCES.md](data/DATA_SOURCES.md) for sources and citation notes.

## Run the dashboard

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`.

## Train models offline

```powershell
python .\offline_trainer.py
```

Training CICIDS2017 and PaySim can take several minutes. The data loader uses bounded stratified samples based on the configured per-dataset limits.

## Troubleshooting

- **Dataset not found:** Run `python .\download_datasets.py` and confirm the CSV files exist under `data/`.
- **CICIDS archive error:** Remove or replace only `data/MachineLearningCSV.zip` and rerun the downloader; it validates the archive before extraction.
- **Missing Python package:** Activate the environment and run `pip install -r requirements.txt` again.
- **Port 8501 is in use:** Run `streamlit run app.py --server.port 8502`.
- **Out of memory during model training:** Lower the dataset sample sizes in `config.py` and restart Streamlit.
