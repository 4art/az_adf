import pandas as pd

if __name__ == '__main__':
    data = {
        "product_id": [101, 102, 103],
        "category": ["Electronics", "Toys", "Furniture"],
        "price": [500, 30, 200]
    }

    df = pd.DataFrame(data)
    df.to_parquet("historical_data.parquet")