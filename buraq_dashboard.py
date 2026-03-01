import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import io

# =============================
# إعداد الصفحة الاحترافي
# =============================
st.set_page_config(
    page_title="Dashboard جمعية البراق",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================
# CSS احترافي (لون أخضر من اللوجو)
# =============================
st.markdown("""
<style>
.main {
    background-color: #0E1117;
}
.block-container {
    padding-top: 1rem;
}
.metric-card {
    background: linear-gradient(135deg, #92d050, #6ca33f); /* الأخضر الجديد من اللوجو */
    padding: 20px;
    border-radius: 15px;
    color: black;
    text-align: center;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
}
.metric-title {
    font-size: 18px;
    font-weight: bold;
}
.metric-value {
    font-size: 32px;
    font-weight: bold;
}
.title-style {
    font-size: 40px;
    font-weight: bold;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# =============================
# فاصل لتنزيل اللوجو والأسلوب
# =============================
st.markdown("<br><br>", unsafe_allow_html=True)

# =============================
# لوجو وعنوان على جنب (اللوجو أصغر)
# =============================
col_logo, col_title = st.columns([1,5])
with col_logo:
    st.image("logo.png", width=80)  # صغرنا العرض
with col_title:
    st.markdown('<div class="title-style">Dashboard جمعية البراق</div>', unsafe_allow_html=True)

# =============================
# الاتصال بـ Google Sheets
# =============================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "zinc-arc-377113-0e09fed6fb4c.json",
    scope
)
client = gspread.authorize(creds)
sheet = client.open("حسابات الجمعية 2026")
worksheet = sheet.worksheet("تجميع مدخلات")

# =============================
# قراءة البيانات وتنظيفها
# =============================
data = worksheet.get()
headers = data[0]
rows = data[1:]

# إزالة الأعمدة الفارغة
clean_headers = []
valid_indexes = []
for i, h in enumerate(headers):
    h = str(h).strip()
    if h != "":
        clean_headers.append(h)
        valid_indexes.append(i)

clean_rows = []
for row in rows:
    clean_row = []
    for i in valid_indexes:
        if i < len(row):
            clean_row.append(row[i])
        else:
            clean_row.append(None)
    clean_rows.append(clean_row)

df = pd.DataFrame(clean_rows, columns=clean_headers)

# إزالة duplicate columns إذا موجودة
def make_unique(cols):
    seen = {}
    result = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            result.append(col)
    return result
df.columns = make_unique(df.columns)

# تنظيف وتحويل الأعمدة الرقمية
def clean_number(x):
    try:
        if x is None or x == "":
            return None
        x = str(x).replace(",", "").replace("جنيه", "").strip()
        return float(x)
    except:
        return None

df["التبرع قبل خصم المصاريف الادارية"] = df["التبرع قبل خصم المصاريف الادارية"].apply(clean_number)
df["الشهر"] = df["الشهر"].apply(clean_number)
df["السنة"] = df["السنة"].apply(clean_number)

df = df[df["التبرع قبل خصم المصاريف الادارية"].notna()]

# إصلاح الأعمدة النصية واستبعاد الإداريات
df["النشاط الأساسي"] = df["النشاط الأساسي"].astype(str)
df["النشاط الفرعي"] = df["النشاط الفرعي"].astype(str)
df = df[~(
    (df["النشاط الأساسي"].str.strip() == "صدقة عامة") &
    (df["النشاط الفرعي"].str.strip() == "اداريات نسبه من التبرع")
)]

# =============================
# الفلاتر
# =============================
st.sidebar.markdown("## الفلاتر")
years = sorted(df["السنة"].dropna().unique())
selected_year = st.sidebar.selectbox("السنة", ["الكل"] + list(years))
months = sorted(df["الشهر"].dropna().unique())
selected_month = st.sidebar.selectbox("الشهر", ["الكل"] + list(months))
main_activity = st.sidebar.selectbox("النشاط الأساسي", ["الكل"] + list(df["النشاط الأساسي"].dropna().unique()))

if main_activity != "الكل":
    sub_df = df[df["النشاط الأساسي"] == main_activity]
else:
    sub_df = df

sub_activity = st.sidebar.selectbox("النشاط الفرعي", ["الكل"] + list(sub_df["النشاط الفرعي"].dropna().unique()))

# =============================
# تطبيق الفلاتر
# =============================
filtered_df = df.copy()
if selected_year != "الكل":
    filtered_df = filtered_df[filtered_df["السنة"] == selected_year]
if selected_month != "الكل":
    filtered_df = filtered_df[filtered_df["الشهر"] == selected_month]
if main_activity != "الكل":
    filtered_df = filtered_df[filtered_df["النشاط الأساسي"] == main_activity]
if sub_activity != "الكل":
    filtered_df = filtered_df[filtered_df["النشاط الفرعي"] == sub_activity]

# =============================
# المؤشرات الاحترافية
# =============================
total = filtered_df["التبرع قبل خصم المصاريف الادارية"].sum()
count = filtered_df.shape[0]
avg = filtered_df["التبرع قبل خصم المصاريف الادارية"].mean()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">إجمالي التبرعات</div>
        <div class="metric-value">{total:,.0f} جنيه</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">عدد العمليات</div>
        <div class="metric-value">{count}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">متوسط التبرع</div>
        <div class="metric-value">{avg:,.0f} جنيه</div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# اختيار نوع الرسم البياني: النشاط الأساسي أو النشاط الفرعي
# =============================
chart_type = st.sidebar.radio(
    "اختر نوع الداشبورد",
    ("النشاط الفرعي", "النشاط الأساسي")
)

st.markdown(f"## التبرعات حسب {chart_type}")

fig = px.bar(
    filtered_df,
    x=chart_type,
    y="التبرع قبل خصم المصاريف الادارية",
    color=chart_type,
    title=f"التبرعات حسب {chart_type}",
    labels={chart_type: chart_type, "التبرع قبل خصم المصاريف الادارية": "المبلغ (جنيه)"}
)
st.plotly_chart(fig, use_container_width=True)

# =============================
# جدول البيانات
# =============================
st.markdown("## تفاصيل التبرعات")
st.dataframe(filtered_df, use_container_width=True)

# =============================
# زر تصدير CSV
# =============================
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

csv = convert_df_to_csv(filtered_df)
st.download_button(
    label="تحميل التبرعات كملف CSV",
    data=csv,
    file_name='تبرعات_الجمعية.csv',
    mime='text/csv'
)