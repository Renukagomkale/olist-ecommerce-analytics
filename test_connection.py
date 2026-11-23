import pandas as pd
from db import engine

df = pd.read_sql("SELECT segment, COUNT(*) AS customers FROM rfm_customers GROUP BY segment ORDER BY customers DESC", engine)
print(df)
