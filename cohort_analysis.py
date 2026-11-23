import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from db import engine

query = """
SELECT
    c.customer_unique_id,
    DATE_TRUNC('month', o.order_purchase_timestamp)::date AS order_month
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
"""

orders = pd.read_sql(query, engine)
orders["order_month"] = pd.to_datetime(orders["order_month"])
orders["cohort_month"] = orders.groupby("customer_unique_id")["order_month"].transform("min")
orders["period"] = (
    (orders["order_month"].dt.year - orders["cohort_month"].dt.year) * 12
    + (orders["order_month"].dt.month - orders["cohort_month"].dt.month)
)

cohort = orders.groupby(["cohort_month", "period"])["customer_unique_id"].nunique().reset_index()
cohort_table = cohort.pivot(index="cohort_month", columns="period", values="customer_unique_id")

retention = cohort_table.divide(cohort_table[0], axis=0) * 100
retention = retention.loc["2017-01":"2018-02", 1:6]
retention.index = retention.index.strftime("%Y-%m")

print(retention.round(2))
print()
print(retention.mean().round(2))

plt.figure(figsize=(9, 7))
sns.heatmap(retention, annot=True, fmt=".2f", cmap="YlOrBr", cbar_kws={"label": "Retention %"})
plt.title("Monthly cohort retention (%)")
plt.xlabel("Months since first purchase")
plt.ylabel("First purchase month")
plt.tight_layout()
plt.savefig("cohort_retention.png", dpi=150)
plt.show()
