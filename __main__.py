import pulumi
import pulumi_azure_native as azure_native

# ======== 1. RESOURCE GROUP ========
resource_group = azure_native.resources.ResourceGroup("rg-adf-etl")

# ======== 2. STORAGE ACCOUNT ========
storage_account = azure_native.storage.StorageAccount(
    "storageaccount",
    resource_group_name=resource_group.name,
    sku=azure_native.storage.SkuArgs(name="Standard_LRS"),
    kind="StorageV2",
)

# Create Blob Containers
raw_data_container = azure_native.storage.BlobContainer(
    "raw-data",
    account_name=storage_account.name,
    resource_group_name=resource_group.name,
    public_access="None",
)

processed_data_container = azure_native.storage.BlobContainer(
    "processed-data",
    account_name=storage_account.name,
    resource_group_name=resource_group.name,
    public_access="None",
)

# ======== 3. SQL DATABASE ========
sql_server = azure_native.sql.Server(
    "sqlserver",
    resource_group_name=resource_group.name,
    administrator_login="adminuser",
    administrator_login_password="SecurePass123!",
    version="12.0",
)

sql_database = azure_native.sql.Database(
    "sqldatabase",
    resource_group_name=resource_group.name,
    server_name=sql_server.name,
    sku=azure_native.sql.SkuArgs(name="Basic"),
)

# ======== 4. DATA FACTORY ========
data_factory = azure_native.datafactory.Factory(
    "datafactory",
    resource_group_name=resource_group.name,
    location=resource_group.location,
)

# ======== 5. LINKED SERVICES ========
# Blob Storage Linked Service
blob_linked_service = azure_native.datafactory.LinkedService(
    "blob-linked-service",
    resource_group_name=resource_group.name,
    factory_name=data_factory.name,
    properties={
        "type": "AzureBlobStorage",
        "typeProperties": {
            "connectionString": pulumi.Output.all(resource_group.name, storage_account.name).apply(
                lambda args: azure_native.storage.list_storage_account_keys(
                    resource_group_name=args[0],
                    account_name=args[1]
                )
            ).apply(
                lambda keys: f"DefaultEndpointsProtocol=https;AccountName={storage_account.name};AccountKey={keys.keys[0].value};EndpointSuffix=core.windows.net"
            )
        }
    },
)


# SQL Database Linked Service
sql_linked_service = azure_native.datafactory.LinkedService(
    "sql-linked-service",
    resource_group_name=resource_group.name,
    factory_name=data_factory.name,
    properties={
        "type": "AzureSqlDatabase",
        "typeProperties": {
            "connectionString": pulumi.Output.all(sql_server.name, sql_database.name).apply(
                lambda args: f"Server=tcp:{args[0]}.database.windows.net,1433;"
                             f"Database={args[1]};User ID=adminuser;Password=SecurePass123!;"
                             "Trusted_Connection=False;Encrypt=True;"
            )
        },
    },
)


# ======== 6. DATASETS ========
raw_data_dataset = azure_native.datafactory.Dataset(
    "raw-data-dataset",
    resource_group_name=resource_group.name,
    factory_name=data_factory.name,
    properties={
        "type": "Binary",
        "linkedServiceName": {
            "referenceName": blob_linked_service.name,
            "type": "LinkedServiceReference",
        },
        "typeProperties": {
            "location": {
                "type": "AzureBlobStorageLocation",
                "container": raw_data_container.name,
            }
        }
    }
)

processed_data_dataset = azure_native.datafactory.Dataset(
    "processed-data-dataset",
    resource_group_name=resource_group.name,
    factory_name=data_factory.name,
    properties={
        "type": "Binary",
        "linkedServiceName": {
            "referenceName": blob_linked_service.name,
            "type": "LinkedServiceReference",
        },
        "typeProperties": {
            "location": {
                "type": "AzureBlobStorageLocation",
                "container": processed_data_container.name,
            }
        }
    }
)

# ======== 7. PIPELINE ========
pipeline = azure_native.datafactory.Pipeline(
    "etl-pipeline",
    resource_group_name=resource_group.name,
    factory_name=data_factory.name,
    activities=[
        {
            "name": "CopyCSVToBlob",
            "type": "Copy",
            "inputs": [{"referenceName": raw_data_dataset.name, "type": "DatasetReference"}],
            "outputs": [{"referenceName": processed_data_dataset.name, "type": "DatasetReference"}],
            "typeProperties": {
                "source": {"type": "BinarySource", "storeSettings": {"type": "AzureBlobStorageReadSettings"}},
                "sink": {"type": "BinarySink", "storeSettings": {"type": "AzureBlobStorageWriteSettings"}},
            },
        }
    ],
)
