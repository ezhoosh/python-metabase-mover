# Metabase Collection Transfer Tool

This script allows you to **transfer a collection from one Metabase instance to another**, including **cards (questions) and dashboards**.

## 🚀 How to Use

1. **Install dependencies**  
   Ensure you have `requests` installed:
   ```sh
   pip install requests
   ```

2. **Run the script**  
   Execute the script and provide the required inputs:
   ```sh
   python metabase-mover.py
   ```

3. **Required Inputs**
   - **Source Metabase URL** (SOURCE_METABASE_URL)
   - **Target Metabase URL** (TARGET_METABASE_URL)
   - **Source Session Token** (SOURCE_SESSION_TOKEN)
   - **Target Session Token** (TARGET_SESSION_TOKEN)
   - **Collection ID to transfer** (COLLECTION_ID)
   - **New collection name in the target Metabase** (NEW_COLLECTION_NAME)

## ⚙️ How the Script Works

### 1️⃣ Fetch Collection Details
The script uses the **Metabase API** to retrieve collection details from the source instance.

### 2️⃣ Create a New Collection in the Target Instance
A new collection is created in the target Metabase instance.

### 3️⃣ Transfer Cards (Questions)
All cards (questions) within the collection are fetched and transferred to the target Metabase.

### 4️⃣ Transfer Dashboards
Dashboards associated with the collection are identified and transferred.

### 5️⃣ Update Dashboard with New Cards
The new dashboards are updated to reference the newly created cards.

### 6️⃣ Transfer Dashboard Filters
All dashboard filters are also transferred to maintain dashboard functionality.

## 🛠 Common Issues and Solutions

- **Session Token Issues:** Ensure that **session tokens** are valid.
- **Cards or Dashboards Not Transferred:** Verify that **the collection contains items** and that you have **sufficient API permissions**.
- **Dashboard Filter Transfer Issues:** Sometimes, Metabase requires that dashboards be created first, and then **filters should be updated separately**.

## 🔗 Resources
- [Metabase API Documentation](https://www.metabase.com/docs/latest/api-documentation.html)
