from pyspark.sql import SparkSession

# Initialize Spark
spark = SparkSession.builder.appName("Pulumi-Spark-ETL").getOrCreate()

# Load data
sales_data = spark.read.csv("raw-data/sales_data.csv", header=True, inferSchema=True)
ratings_data = spark.read.json("raw-data/ratings.json")
historical_data = spark.read.parquet("raw-data/historical_data.parquet")

# Transform
joined_data = sales_data.join(ratings_data, "product_id").join(historical_data, "product_id")
cleaned_data = joined_data.filter(joined_data.sales_amount.isNotNull())

# Save
cleaned_data.write.parquet("processed-data/aggregated_data.parquet")