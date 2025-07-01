# Budget Management System

A Django + Celery backend system for managing ad campaign budgets per brand. It tracks daily/monthly spend, enforces budget limits, handles dayparting (active hours), and automatically resets spend counters.

## 🧠 Pseudo-code (High-Level Overview)

### 📦 Data Models

#### Brand
Represents an advertiser with set budget limits.
```
Brand:
  - name: String
  - daily_budget: Decimal
  - monthly_budget: Decimal
```

#### Campaign
Belongs to a brand, and is subject to its budgets.
```
Campaign:
  - brand: ForeignKey to Brand
  - name: String
  - is_active: Boolean
  - current_daily_spend: Decimal
  - current_monthly_spend: Decimal
```

#### SpendLog
Tracks individual spending events for campaigns.
```
SpendLog:
  - campaign: ForeignKey to Campaign
  - timestamp: DateTime
  - amount: Decimal
```

#### DaypartingSchedule
Defines allowed hours for campaign operation.
```
DaypartingSchedule:
  - campaign: OneToOne to Campaign
  - start_hour: Integer (0–23)
  - end_hour: Integer (0–23)
```

---

### 🔁 Tracking Spend
```
When spend event occurs:
  Create SpendLog(campaign, amount, timestamp)
  campaign.current_daily_spend += amount
  campaign.current_monthly_spend += amount
  Save campaign
```

### 🚫 Budget Enforcement
```
Periodically (e.g. every 5 minutes):
  For each campaign:
    If current_daily_spend >= brand.daily_budget OR
       current_monthly_spend >= brand.monthly_budget:
       campaign.is_active = False
    Else:
       campaign.is_active = True (if within dayparting window)
    Save campaign
```

### ⏰ Dayparting Checks
```
Periodically:
  now_hour = current hour (0-23)

  For each campaign with a DaypartingSchedule:
    If now_hour NOT between start_hour and end_hour:
      campaign.is_active = False
    Else if within budget:
      campaign.is_active = True
    Save campaign
```

### 🔄 Daily Reset (Midnight)
```
At 00:00 daily:
  For each campaign:
    campaign.current_daily_spend = 0
    If within budget AND current time is within dayparting window:
      campaign.is_active = True
    Save campaign
```

### 🔁 Monthly Reset (1st Day of Month)
```
On the 1st of each month:
  For each campaign:
    campaign.current_monthly_spend = 0
    Save campaign
```

---

## 🔧 Features
- **Brand & Campaign Models**: Each brand has multiple campaigns, each with its own spend.
- **Daily/Monthly Spend Tracking**: Spend is logged and compared against brand limits.
- **Automatic Budget Enforcement**: Campaigns pause when they exceed limits.
- **Dayparting**: Campaigns only run during specified time windows.
- **Celery Tasks**:
  - Enforce budget and dayparting every few minutes
  - Reset daily spend at midnight
  - Reset monthly spend on the 1st

---

## 🏗️ Project Structure
```
+ ├──  + budget_management
   + ├──  + asgi.py
   + ├──  + celery.py
   + ├──  + settings.py
   + ├──  + urls.py
   + ├──  + wsgi.py
   + ├──  + __init__.py
 + ├──  + campaigns
   + ├──  + management
     + ├──  + commands
   + ├──  + migrations
     + ├──  + 0001_initial.py
     + ├──  + 0002_alter_daypartingschedule_campaign.py
     + ├──  + __init__.py
   + ├──  + admin.py
   + ├──  + admin.pyi
   + ├──  + apps.py
   + ├──  + models.py
   + ├──  + services.py
   + ├──  + tasks.py
   + ├──  + test_services.py
   + ├──  + test_tasks.py
   + ├──  + views.py
   + ├──  + __init__.py
 + ├──  + celerybeat-schedule
 + ├──  + db.sqlite3
 + ├──  + docker-compose.yml
 + ├──  + Dockerfile
 + ├──  + manage.py
 + ├──  + mypy.ini
 + ├──  + pytest.ini
 + ├──  + README.md
 + ├──  + requirements.txt
```

---

## 🧠 Data Model Overview

### Brand
- `name`: Brand name
- `daily_budget`: Daily spend limit
- `monthly_budget`: Monthly spend limit

### Campaign
- Linked to `Brand`
- `current_daily_spend`, `current_monthly_spend`
- `is_active`: Automatically managed

### SpendLog
- Logs each spend instance
- `amount`, `timestamp`

### DaypartingSchedule
- Linked to one `Campaign`
- `start_hour`, `end_hour`: Active hours in 24h format

---

## 🔄 Daily Workflow
1. **Spends are recorded** via logs.
2. **Campaigns are monitored** periodically:
   - Paused if they exceed brand budget
   - Paused outside dayparting hours
3. **At midnight (daily)**:
   - Daily spend resets
   - Campaigns reactivated if within budget and in dayparting window
4. **On 1st of the month**:
   - Monthly spend resets

---

## 🚀 Setup Instructions

### 1. Clone the Repo
```bash
git clone <your-repo-url>
cd budget_management
```

### 2. Docker Setup (Recommended)

#### Build and Run with Docker Compose
```bash
docker-compose up --build
```

#### Services
- **web**: Django application (http://localhost:8000)
- **celery**: Celery worker
- **celery_beat**: Celery beat scheduler
- **redis**: Redis message broker

### 3. Without Docker (Manual Setup)

#### Install Redis (if not using Docker)
- **macOS**: `brew install redis`
- **Ubuntu/Debian**: `sudo apt update && sudo apt install redis`
- **Windows**: Use [Memurai](https://www.memurai.com/) or install via [WSL](https://learn.microsoft.com/en-us/windows/wsl/).

Ensure Redis is running:
```bash
redis-server
```

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
celery -A budget_management worker --loglevel=info
```

---

## 📊 Logging Spend via Management Command

You can manually log spend for a campaign using the custom Django management command:

```bash
python manage.py log_spend <campaign_id> <amount>
```

---

## ✅ Static Typing
- All logic is typed with PEP 484 annotations.
- `mypy.ini` enforces strict rules.
- Run type checks:
```bash
mypy .
```

---

## ✅ Assumptions & Simplifications
- Dayparting does not support ranges that cross midnight (e.g., 23 to 5).
- Budget enforcement uses summed SpendLogs as current totals.
- All timezones are assumed to be local/server time.

---

## 📄 License
MIT

---

## 📫 Author
Samuel Adole ([@samueladole](https://github.com/samueladole))

---

## 🧪 Next Steps (Stretch Goals)
- Admin UI for managing brands & campaigns
- REST API integration
- Timezone-aware dayparting
- Separate "Paused due to budget" and "Paused due to schedule" states
