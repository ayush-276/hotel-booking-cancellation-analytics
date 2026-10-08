# Hotel Booking Cancellation & Revenue Analytics

## Problem Statement
Hotels lose money when guests cancel, because the room may stay empty or be resold at a lower price. This project analyses hotel booking data to answer:

1. How many bookings get cancelled, and how much revenue does that cost?
2. Which kinds of bookings (lead time, market segment, guest behaviour) are most likely to be cancelled?
3. What should the hotel do to reduce cancellations and protect revenue?

## Dataset
- **Name:** Hotel Booking Demand
- **Source / link:** https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand
- **File used:** `hotel_bookings.csv` (City Hotel and Resort Hotel bookings, 2015-2017)

Download the file from the link above and place it in a folder named `data/` next to the code file.

## Technologies Used
- Python
- pandas, numpy (cleaning and analysis)
- plotly (charts)
- Streamlit (dashboard)

## How to Run
```bash
# 1. clone the repo and go into the folder
git clone <your-repo-link>
cd <repo-folder>

# 2. install libraries
pip install -r requirements.txt

# 3. put hotel_bookings.csv inside a folder called data/

# 4. start the app
streamlit run project_code.py
```

## What the Project Does
Flow: **Dataset → Clean → KPIs → Trends → Drivers → Risks/Opportunities → Actions**

1. **Cleaning:** removes duplicates, fills missing children and country values, removes bookings with zero guests and impossible prices, builds the arrival date, stay length and revenue columns.
2. **Overview page:** KPIs (bookings, cancellation rate, average daily rate, lead time, realized and lost revenue, repeat guests) with monthly trends and a City vs Resort comparison.
3. **Cancellation Drivers page:** cancellation rate by lead time, market segment, special requests, deposit type, customer type, cancellation history and country.
4. **Revenue & Guests page:** seasonal prices, realized vs lost revenue by segment, top countries, meal plans and length of stay.
5. **Recommendations page:** risks, opportunities and actions. All numbers are calculated from the data. A sidebar filter lets you view all hotels, City Hotel or Resort Hotel.

## Key Insights

- About **27.5%** of bookings are cancelled, which is roughly **11.5 million** in lost room revenue (33.3% of potential revenue).
- Bookings made more than 180 days ahead are cancelled **[X]%** of the time vs **[X]%** for bookings made within 30 days.
- The riskiest market segments are **[segment, segment]**; the most reliable are **[segment, segment]**.
- Guests who make special requests cancel **[X]%** vs **[X]%** for those who don't.
- The month with the most cancellations is **[month]**.
- Only **3.9%** of guests are repeat guests, so most revenue comes from new customers.

## Notes and Limitations
- The "Non Refund" deposit type shows a very high cancellation rate, which looks like a data recording issue, so it is not used for recommendations.
- Revenue is estimated as average daily rate × nights, not actual billing.
- This is observational data, so the drivers show links and not proof of cause.

## Project Files
```
├── project_code.py
├── requirements.txt
├── README.md
└── Project_Report.pdf
```
