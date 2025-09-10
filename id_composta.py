import pandas as pd
from to_parquet import make_data_paths

y = input("Ano dos microdados:")
t = input("Trimestre desejado:")

_, q1 = make_data_paths(y, t)
_, q5 = make_data_paths(2025, 1)

q1 = pd.read_parquet(q1)
q5 = pd.read_parquet(q5)


for df in (q1, q5):
    df["person_id"] = (
        df["UF"].astype(str).str.zfill(2) +
        df["UPA"].astype(str).str.zfill(9) +
        df["V1008"].astype(str).str.zfill(2) +
        df["V1014"].astype(str).str.zfill(2) +
        df["V2003"].astype(str).str.zfill(2)
    )

keep = ["person_id", "Ano", "Trimestre", "VD4002", "VD4020", "VD4035"]
q1 = q1[keep]
q5 = q5[keep]

q1 = q1.rename(columns={
    "VD4002": "VD4002_t", "VD4020": "income_t", "VD4035": "hours_t"
})
q5 = q5.rename(columns={
    "VD4002": "VD4002_t4", "VD4020": "income_t4", "VD4035": "hours_t4"
})


merged = q1.merge(q5, on="person_id", suffixes=("_t", "_t4"))
print(f"Matched {len(merged)} individuals")
