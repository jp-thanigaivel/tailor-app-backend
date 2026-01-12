# RMC Project Setup

## Prerequisites

- Python 3.12+ installed on your machine.
- Poetry (for managing dependencies).

---

## Step 1: Create a Virtual Environment

Run the following command to create a new virtual environment:

```bash
python3 -m venv my-project-env
```

## Step 2: Activate Virtual Environment
```bash
source my-project-env/bin/activate
```

## Step 3: Install Dependency in Virtual Environment
```bash
poetry install --no-root
```

## Step 4: Start Application
```bash
uvicorn app.main:app
```

## Step 5: Database Initialization

To initialize the sequences for the first time, run the following commands in your MongoDB shell:

```javascript
db.app_sequence_user.insertOne({
  _id: "user_id_seq",
  current_sequence: 0,
  next_sequence: 1,
  increament_by: 1,
  last_updated: 1683449664
})

db.app_sequence_customer.insertOne({
  _id: "customer_id_seq",
  current_sequence: 0,
  next_sequence: 1,
  increament_by: 1,
  last_updated: 1683449664
})

db.app_sequence_profile.insertOne({
  _id: "profile_id_seq",
  current_sequence: 0,
  next_sequence: 1,
  increament_by: 1,
  last_updated: 1683449664
})

db.app_sequence_order.insertOne({
  _id: "order_id_seq",
  current_sequence: 0,
  next_sequence: 1,
  increament_by: 1,
  last_updated: 1683449664
})

db.app_sequence_order_item.insertOne({
  _id: "order_item_id_seq",
  current_sequence: 0,
  next_sequence: 1,
  increament_by: 1,
  last_updated: 1683449664
})

db.app_sequence_payment.insertOne({
  _id: "payment_id_seq",
  current_sequence: 0,
  next_sequence: 1,
  increament_by: 1,
  last_updated: 1683449664
})
```

### App Secret Initialization

To initialize the application secrets, run this command in your MongoDB shell (inside the `qa_tailor` database):

```javascript
db.app_secret.insertOne({
  "internal_api_credential": {
     "user_name": "internal-process-execution",
    "password": "app-secret-word"
  },
  "auth_config": {
    "access_secret_key": "3e8a3f31aab886f8793176988f8298c9265f84b8388c9fef93635b08951f379b",
    "refresh_secret_key": "3c83e919193d06cb51e46a7855c48b3291e31e52e5c3a0735298322854772051",
    "algorithm": "HS256",
    "access_token_expire_minutes": 120,
    "refresh_token_expire_minutes": 125,
    "access_token_type": "Bearer"
  },
  "otp_expiry_seconds": 300
})
```
