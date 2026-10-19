# Dataset sources and status

- **PaySim:** 6,362,620-row synthetic mobile-money benchmark mirror. The simulator-generated transactions are not observed bank transactions. Full source is stored in `paysim_full.csv.gz`.
- **BankSim:** published 594,643-row BankSim payment simulator data (`bs140513_032310.csv`), mirrored from [the public BankSim repository](https://github.com/niravdedhiya/Fraud-Detection-BankSim) and originally distributed as [BankSim on Kaggle](https://www.kaggle.com/datasets/ealaxi/banksim1). BankSim is synthetic research data by design. Full source is `banksim_full.csv.gz`.
- **CICIDS2017:** mirrored original MachineLearningCSV archive from [bencorn/CICIDS2017](https://huggingface.co/datasets/bencorn/CICIDS2017), identifying the University of New Brunswick Canadian Institute for Cybersecurity as source. Cite the [official CIC-IDS2017 page](https://www.unb.ca/cic/datasets/ids-2017.html) and associated paper. Full source is `cicids_full.csv.gz`.
- **IEEE-CIS:** full labeled 590,540-row IEEE-CIS/Vesta training split mirrored on [OpenML dataset 46858](https://www.openml.org/d/46858), from the [official Kaggle competition](https://www.kaggle.com/competitions/ieee-fraud-detection/data). Kaggle's competition access terms apply. The project keeps 98 configured transaction, behavioral, and anonymous Vesta features plus target in `ieee_full.csv.gz`; the downloaded OpenML parquet is retained as `ieee_openml.parquet`.
- `banksim_demo.csv` and `ieee_demo.csv`, if generated, are small synthetic examples only and are not used by the app.

## Local files and training

`paysim.csv`, `cicids.csv`, `banksim.csv`, and `ieee.csv` are 5,000-row inspection previews. The app reads the compressed full sources for training. BankSim and IEEE-CIS training use all available rows (594,643 and 590,540); validation holds out later transactions by time. Run `python download_datasets.py` to rebuild downloads and previews. The IEEE conversion requires `pyarrow`.
