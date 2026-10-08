# Hotel Booking Cancellation & Revenue Analytics
#
# How to run:
#   1. Download hotel_bookings.csv from Kaggle and put it in a folder called "data"
#   2. pip install -r requirements.txt
#   3. streamlit run project_code.py

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DATA_FILE = "data/hotel_bookings.csv"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

st.set_page_config(page_title="Hotel Cancellation Analytics", layout="wide")


# ---------------------------------------------------------------
# 1. LOAD + CLEAN
# ---------------------------------------------------------------
@st.cache_data
def load_and_clean():
    df = pd.read_csv(DATA_FILE)

    df = df.drop_duplicates()

    # missing values
    df["children"] = df["children"].fillna(0)
    df["country"] = df["country"].fillna("Unknown")

    # remove bookings with no guests, negative price or crazy price
    df["guests"] = df["adults"] + df["children"] + df["babies"]
    df = df[df["guests"] > 0]
    df = df[(df["adr"] >= 0) & (df["adr"] < 1000)]

    # arrival date and stay length
    df["month_num"] = df["arrival_date_month"].map({m: i + 1 for i, m in enumerate(MONTHS)})
    df["arrival_date"] = pd.to_datetime(
        dict(year=df["arrival_date_year"], month=df["month_num"], day=df["arrival_date_day_of_month"])
    )
    df["arrival_month"] = df["arrival_date"].dt.to_period("M").dt.to_timestamp()
    df["nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]

    # revenue: what the room would have earned (adr x nights)
    df["room_value"] = df["adr"] * df["nights"]
    df["realized_revenue"] = np.where(df["is_canceled"] == 0, df["room_value"], 0)
    df["lost_revenue"] = np.where(df["is_canceled"] == 1, df["room_value"], 0)

    # buckets
    df["lead_bucket"] = pd.cut(
        df["lead_time"],
        bins=[-1, 7, 30, 90, 180, 1000],
        labels=["0-7 days", "8-30 days", "31-90 days", "91-180 days", "180+ days"],
    )
    df["requests_group"] = df["total_of_special_requests"].clip(upper=3).astype(str)
    df["requests_group"] = df["requests_group"].replace({"3": "3+"})
    df["prev_cancel_group"] = np.where(df["previous_cancellations"] > 0, "Has cancelled before", "No previous cancellation")
    df["changes_group"] = np.where(df["booking_changes"] > 0, "Changed booking", "No changes")
    return df


def cancel_rate_by(data, col, min_bookings=1):
    out = data.groupby(col, observed=True).agg(
        bookings=("is_canceled", "count"), cancel_rate=("is_canceled", "mean")
    )
    out = out.reset_index()
    out["cancel_rate"] = (out["cancel_rate"] * 100).round(2)
    return out[out["bookings"] >= min_bookings]


try:
    full = load_and_clean()
except FileNotFoundError:
    st.error("hotel_bookings.csv not found. Download it from Kaggle and put it in the 'data' folder.")
    st.stop()

# ---------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------
st.sidebar.title("Hotel Analytics")
page = st.sidebar.radio(
    "Go to",
    ["1. Overview", "2. Cancellation Drivers", "3. Revenue & Guests", "4. Recommendations"],
)
hotel_choice = st.sidebar.selectbox("Hotel", ["All", "City Hotel", "Resort Hotel"])
df = full if hotel_choice == "All" else full[full["hotel"] == hotel_choice]

# KPIs
total_bookings = len(df)
cancel_rate = df["is_canceled"].mean() * 100
kept = df[df["is_canceled"] == 0]
avg_adr = kept["adr"].mean()
realized = df["realized_revenue"].sum()
lost = df["lost_revenue"].sum()
avg_lead = df["lead_time"].mean()
repeat_guests = df["is_repeated_guest"].mean() * 100

# ---------------------------------------------------------------
# PAGE 1 - OVERVIEW
# ---------------------------------------------------------------
if page == "1. Overview":
    st.title("Executive Overview")

    a, b, c, d = st.columns(4)
    a.metric("Total bookings", f"{total_bookings:,}")
    b.metric("Cancellation rate", f"{cancel_rate:.1f}%")
    c.metric("Avg daily rate (kept bookings)", f"{avg_adr:,.1f}")
    d.metric("Avg lead time (days)", f"{avg_lead:.0f}")

    e, f, g, h = st.columns(4)
    e.metric("Realized revenue", f"{realized:,.0f}")
    f.metric("Revenue lost to cancellations", f"{lost:,.0f}")
    g.metric("Lost share of potential revenue", f"{lost / (realized + lost) * 100:.1f}%")
    h.metric("Repeat guests", f"{repeat_guests:.1f}%")

    st.info(
        f"About {cancel_rate:.0f} out of every 100 bookings are cancelled, "
        f"which is roughly {lost:,.0f} in room revenue that never arrives."
    )

    # monthly trend
    monthly = df.groupby("arrival_month").agg(
        bookings=("is_canceled", "count"), cancel_rate=("is_canceled", "mean")
    )
    monthly = monthly.reset_index()
    monthly["cancel_rate"] = monthly["cancel_rate"] * 100

    st.plotly_chart(px.line(monthly, x="arrival_month", y="bookings", markers=True,
                            title="Bookings by arrival month"), use_container_width=True)
    st.plotly_chart(px.line(monthly, x="arrival_month", y="cancel_rate", markers=True,
                            title="Cancellation rate by arrival month (%)"), use_container_width=True)

    # City vs Resort
    by_hotel = full.groupby("hotel").agg(
        bookings=("is_canceled", "count"),
        cancel_rate=("is_canceled", "mean"),
        adr=("adr", "mean"),
    )
    by_hotel = by_hotel.reset_index()
    by_hotel["cancel_rate"] = (by_hotel["cancel_rate"] * 100).round(1)
    by_hotel["adr"] = by_hotel["adr"].round(1)
    st.subheader("City vs Resort hotel")
    st.dataframe(by_hotel, use_container_width=True)

# ---------------------------------------------------------------
# PAGE 2 - DRIVERS
# ---------------------------------------------------------------
elif page == "2. Cancellation Drivers":
    st.title("What drives cancellations?")
    st.caption("Cancellation rate (%) for different kinds of bookings.")

    col1, col2 = st.columns(2)
    with col1:
        t = cancel_rate_by(df, "lead_bucket")
        st.plotly_chart(px.bar(t, x="lead_bucket", y="cancel_rate", text="cancel_rate",
                               title="Lead time (days between booking and arrival)"),
                        use_container_width=True)
    with col2:
        t = cancel_rate_by(df, "market_segment", min_bookings=500)
        t = t.sort_values("cancel_rate", ascending=False)
        st.plotly_chart(px.bar(t, x="market_segment", y="cancel_rate", text="cancel_rate",
                               title="Market segment"), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        t = cancel_rate_by(df, "requests_group").sort_values("requests_group")
        st.plotly_chart(px.bar(t, x="requests_group", y="cancel_rate", text="cancel_rate",
                               title="Number of special requests"), use_container_width=True)
    with col4:
        t = cancel_rate_by(df, "deposit_type")
        st.plotly_chart(px.bar(t, x="deposit_type", y="cancel_rate", text="cancel_rate",
                               title="Deposit type"), use_container_width=True)
    st.caption(
        "Note: 'Non Refund' deposits show a very high cancellation rate in this dataset. "
        "This looks odd and is probably caused by how the data was recorded, so it is not used for recommendations."
    )

    col5, col6 = st.columns(2)
    with col5:
        t = cancel_rate_by(df, "customer_type")
        st.plotly_chart(px.bar(t, x="customer_type", y="cancel_rate", text="cancel_rate",
                               title="Customer type"), use_container_width=True)
    with col6:
        t = cancel_rate_by(df, "prev_cancel_group")
        st.plotly_chart(px.bar(t, x="prev_cancel_group", y="cancel_rate", text="cancel_rate",
                               title="Cancellation history"), use_container_width=True)

    st.subheader("Top 10 countries by bookings")
    top_countries = df["country"].value_counts().head(10).index
    t = cancel_rate_by(df[df["country"].isin(top_countries)], "country")
    t = t.sort_values("cancel_rate", ascending=False)
    st.dataframe(t, use_container_width=True)

# ---------------------------------------------------------------
# PAGE 3 - REVENUE & GUESTS
# ---------------------------------------------------------------
elif page == "3. Revenue & Guests":
    st.title("Revenue & Guests")

    # seasonality of price
    season = kept.groupby(["arrival_date_month", "hotel"]).agg(adr=("adr", "mean")).reset_index()
    season["arrival_date_month"] = pd.Categorical(season["arrival_date_month"], categories=MONTHS, ordered=True)
    season = season.sort_values("arrival_date_month")
    st.plotly_chart(px.line(season, x="arrival_date_month", y="adr", color="hotel", markers=True,
                            title="Average daily rate by month"), use_container_width=True)

    # revenue by segment
    seg = df.groupby("market_segment").agg(
        bookings=("is_canceled", "count"),
        realized=("realized_revenue", "sum"),
        lost=("lost_revenue", "sum"),
    )
    seg = seg.reset_index()
    seg = seg[seg["bookings"] >= 500]
    seg_long = seg.melt(id_vars="market_segment", value_vars=["realized", "lost"],
                        var_name="type", value_name="revenue")
    st.plotly_chart(px.bar(seg_long, x="market_segment", y="revenue", color="type", barmode="group",
                           title="Realized vs lost revenue by market segment"),
                    use_container_width=True)

    # countries by revenue
    ctry = df.groupby("country").agg(realized=("realized_revenue", "sum"), bookings=("is_canceled", "count"))
    ctry = ctry.reset_index().sort_values("realized", ascending=False).head(10)
    st.plotly_chart(px.bar(ctry, x="country", y="realized", title="Top 10 countries by realized revenue"),
                    use_container_width=True)

    # guest mix
    col1, col2 = st.columns(2)
    with col1:
        meal = kept["meal"].value_counts().reset_index()
        meal.columns = ["meal", "bookings"]
        st.plotly_chart(px.pie(meal, names="meal", values="bookings", title="Meal plan (kept bookings)"),
                        use_container_width=True)
    with col2:
        st.plotly_chart(px.histogram(kept, x="nights", nbins=15, range_x=[0, 15],
                                     title="Length of stay (nights)"), use_container_width=True)

# ---------------------------------------------------------------
# PAGE 4 - RECOMMENDATIONS
# ---------------------------------------------------------------
else:
    st.title("Recommended Actions")
    st.caption(f"Calculated from the data (hotel filter: {hotel_choice}).")

    # facts
    long_lead = df[df["lead_time"] > 180]["is_canceled"].mean() * 100
    short_lead = df[df["lead_time"] <= 30]["is_canceled"].mean() * 100

    no_req = df[df["total_of_special_requests"] == 0]["is_canceled"].mean() * 100
    with_req = df[df["total_of_special_requests"] >= 1]["is_canceled"].mean() * 100

    seg = cancel_rate_by(df, "market_segment", min_bookings=1000).sort_values("cancel_rate", ascending=False)
    risky = seg.head(2)
    safe = seg.tail(2)
    risky_text = ", ".join(f"{s} ({r}%)" for s, r in zip(risky["market_segment"], risky["cancel_rate"]))
    safe_text = ", ".join(f"{s} ({r}%)" for s, r in zip(safe["market_segment"], safe["cancel_rate"]))

    month_rate = df.groupby("month_num").agg(rate=("is_canceled", "mean"), n=("is_canceled", "count"))
    worst_month = MONTHS[int(month_rate["rate"].idxmax()) - 1]
    worst_month_rate = month_rate["rate"].max() * 100

    top_ctry = df.groupby("country")["realized_revenue"].sum().sort_values(ascending=False).head(3)
    ctry_text = ", ".join(top_ctry.index)

    long_lead_lost = df[df["lead_time"] > 180]["lost_revenue"].sum()

    st.subheader("Risks")
    st.markdown(
        f"- **Overall cancellation rate is {cancel_rate:.1f}%**, with {lost:,.0f} of room revenue lost.\n"
        f"- **Early bookings are risky:** bookings made more than 180 days ahead are cancelled "
        f"{long_lead:.1f}% of the time vs {short_lead:.1f}% for bookings made within 30 days "
        f"(about {long_lead_lost:,.0f} lost revenue from the 180+ day group).\n"
        f"- **Riskiest segments:** {risky_text}.\n"
        f"- **Worst month for cancellations:** {worst_month} ({worst_month_rate:.1f}%)."
    )

    st.subheader("Opportunities")
    st.markdown(
        f"- **Most reliable segments:** {safe_text}.\n"
        f"- **Engaged guests stay:** bookings with at least one special request are cancelled "
        f"{with_req:.1f}% of the time vs {no_req:.1f}% with none.\n"
        f"- **Top revenue countries:** {ctry_text}."
    )

    st.subheader("Recommended actions")
    st.markdown(
        f"1. **Ask for a deposit or stricter terms on long lead-time bookings** (180+ days), "
        f"especially from {risky_text}.\n"
        "2. **Send a reconfirmation message** 30 days before arrival for early bookings, and "
        "release rooms for resale if there is no reply.\n"
        f"3. **Plan a small overbooking buffer for {worst_month}**, the month with the highest cancellation rate.\n"
        f"4. **Shift marketing and sales effort towards the most reliable segments** ({safe_text}), "
        "for example direct booking offers.\n"
        "5. **Invite guests to add requests** (room type, late check-in, extras) after booking, since "
        "guests who make requests cancel less.\n"
        f"6. **Focus campaigns on the top revenue countries** ({ctry_text})."
    )

    st.warning(
        "This is observational data. The patterns show links with cancellations, not proof of cause. "
        "Test any new policy on a small group first."
    )
