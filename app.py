import streamlit as st
import pandas as pd
from utils.awc_api import metar, pirep_bbox, AWCError
from utils.geo import bbox_from_point
from utils.metar_parse import ceiling_ft_from_raw, visibility_sm_from_raw, flight_category
from utils.pirep_parse import extract_bases_tops

st.set_page_config(page_title="Drone Wx Profile", layout="wide")
st.title("🛸 Drone Wx Profile (METAR/SPECI + PIREPs)")

# --- Inputs (radius-based for drone ops)
icao = st.text_input("Nearby Airport ICAO (for METAR/SPECI)", value="KTRI").strip().upper()

colA, colB, colC = st.columns(3)
with colA:
    lat = st.number_input("Latitude (launch area)", value=36.4752, format="%.4f")
with colB:
    lon = st.number_input("Longitude (launch area)", value=-82.4074, format="%.4f")
with colC:
    radius_nm = st.slider("PIREP radius (NM)", 5, 100, 25)

hours_metar = st.slider("METAR lookback (hours)", 1, 12, 3)
hours_pirep = st.slider("PIREP lookback (hours)", 1, 12, 6)

lat1, lon1, lat2, lon2 = bbox_from_point(lat, lon, radius_nm)

# --- Caching: reduce API calls (good for rate limits and Community Cloud)
@st.cache_data(ttl=120)
def fetch_metars(icao, hours):
    return metar(icao, hours=hours, fmt="json")

@st.cache_data(ttl=180)
def fetch_pireps(lat1, lon1, lat2, lon2, hours):
    return pirep_bbox(lat1, lon1, lat2, lon2, hours=hours, fmt="json")

tabs = st.tabs(["Surface (METAR/SPECI)", "PIREPs", "Combined Summary"])

with tabs[0]:
    st.subheader("Surface (METAR/SPECI)")
    try:
        m = fetch_metars(icao, hours_metar)
        mdf = pd.DataFrame(m if isinstance(m, list) else [m])

        # Find raw METAR text column (API field names can vary)
        raw_col = next((c for c in mdf.columns if c.lower() in ("rawob","raw","text","raw_text")), None)
        if raw_col:
            mdf["ceiling_ft"] = mdf[raw_col].apply(ceiling_ft_from_raw)
            mdf["visibility_sm"] = mdf[raw_col].apply(visibility_sm_from_raw)
            mdf["category"] = mdf.apply(lambda r: flight_category(r["ceiling_ft"], r["visibility_sm"]), axis=1)

        st.dataframe(mdf, use_container_width=True)

        if raw_col and len(mdf) > 0:
            latest = mdf.iloc[0]
            st.metric("Latest Flight Category", latest.get("category", "Unknown"))
            st.code(latest.get(raw_col, ""), language="text")

    except AWCError as e:
        st.error(f"METAR fetch failed: {e}")
        st.caption("This app uses AviationWeather.gov Data API for METAR access. [1](https://www.aviationweather.gov/data/api/)[2](http://www.raob.com/data_sources.php)")

with tabs[1]:
    st.subheader("PIREPs (radius → bbox)")
    st.caption(f"bbox: ({lat1:.3f},{lon1:.3f}) to ({lat2:.3f},{lon2:.3f})")
    try:
        p = fetch_pireps(lat1, lon1, lat2, lon2, hours_pirep)
        pdf = pd.DataFrame(p if isinstance(p, list) else [p])

        text_col = next((c for c in pdf.columns if c.lower() in ("rawob","raw","text","report")), None)
        if text_col:
            bases_tops = pdf[text_col].apply(extract_bases_tops)
            pdf["bases_guess"] = bases_tops.apply(lambda x: x[0])
            pdf["tops_guess"]  = bases_tops.apply(lambda x: x[1])

        st.dataframe(pdf, use_container_width=True)

    except AWCError as e:
        st.error(f"PIREP fetch failed: {e}")
        st.caption("This app uses AviationWeather.gov Data API for PIREP access. [1](https://www.aviationweather.gov/data/api/)[2](http://www.raob.com/data_sources.php)")

with tabs[2]:
    st.subheader("Combined Summary (what you care about for drone ops)")
    summary = []

    # METAR summary
    try:
        m = fetch_metars(icao, 2)
        m0 = m[0] if isinstance(m, list) and m else m
        raw = m0.get("rawOb") or m0.get("raw") or m0.get("text") or ""
        ceil_ft = ceiling_ft_from_raw(raw)
        vis_sm  = visibility_sm_from_raw(raw)
        cat     = flight_category(ceil_ft, vis_sm)
        summary.append(f"**Surface near {icao}:** {cat} | vis ≈ {vis_sm} SM | ceiling ≈ {ceil_ft} ft AGL")
        summary.append(f"`{raw}`")
    except Exception:
        summary.append("**Surface:** unavailable")

    # PIREP tops/bases summary
    try:
        p = fetch_pireps(lat1, lon1, lat2, lon2, hours_pirep)
        pireps = p if isinstance(p, list) else [p]
        all_bases, all_tops = [], []
        for pr in pireps:
            t = pr.get("rawOb") or pr.get("raw") or pr.get("text") or ""
            b, tops = extract_bases_tops(t)
            all_bases += b
            all_tops  += tops

        if all_bases:
            summary.append(f"**Nearby PIREP bases (heuristic):** ~{sorted(all_bases)[:8]} ft")
        else:
            summary.append("**Nearby PIREP bases:** none explicitly found")

        if all_tops:
            summary.append(f"**Nearby PIREP tops (heuristic):** ~{sorted(all_tops)[:8]} ft")
        else:
            summary.append("**Nearby PIREP tops:** none explicitly found")

    except Exception:
        summary.append("**PIREPs:** unavailable")

    st.markdown("\n\n".join(summary))
    st.info("AviationWeather.gov asks you to keep API requests limited and notes rate limiting; caching helps. [1](https://www.aviationweather.gov/data/api/)")
``