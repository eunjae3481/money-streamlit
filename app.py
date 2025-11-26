import streamlit as st
import pandas as pd
from datetime import date
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="용돈 지수 관리앱", page_icon="💸", layout="centered")

st.title("💸 은재의 용돈 지수 관리앱")
st.write("수입·지출을 기록하고, 카테고리별/기간별로 확인해보세요.")

# 초기화: 세션 상태에 데이터프레임 저장
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(
        columns=["date", "type", "category", "amount", "note"]
    )

# 사이드바: 항목 입력 폼
st.sidebar.header("새 항목 추가")
with st.sidebar.form("entry_form", clear_on_submit=True):
    entry_date = st.date_input("날짜", value=date.today())
    entry_type = st.selectbox("구분", ["지출", "수입"])
    default_cats = ["식비", "교통", "간식", "학용품", "용돈", "문화/여가", "기타"]
    entry_category = st.text_input("카테고리 (직접 입력 가능)", value="식비")
    entry_amount = st.number_input("금액(원)", min_value=0, step=100, value=1000)
    entry_note = st.text_input("메모 (선택)")
    add_clicked = st.form_submit_button("항목 추가")

if add_clicked:
    new_row = {
        "date": pd.to_datetime(entry_date),
        "type": entry_type,
        "category": entry_category.strip() or "기타",
        "amount": float(entry_amount),
        "note": entry_note,
    }
    st.session_state.data = pd.concat(
        [st.session_state.data, pd.DataFrame([new_row])], ignore_index=True
    )
    st.success("✅ 항목이 추가되었어요!")

# 업로드: CSV 불러오기
st.sidebar.header("데이터 가져오기/내보내기")
uploaded = st.sidebar.file_uploader("CSV 파일 업로드 (불러오기)", type=["csv"])
if uploaded is not None:
    try:
        df_up = pd.read_csv(uploaded, parse_dates=["date"])
        # 간단한 유효성 검사
        if {"date", "type", "category", "amount", "note"}.issubset(df_up.columns):
            st.session_state.data = df_up[["date", "type", "category", "amount", "note"]].copy()
            st.sidebar.success("📥 CSV 불러오기 완료")
        else:
            st.sidebar.error("CSV에 필요한 열이 없습니다. (date,type,category,amount,note)")
    except Exception as e:
        st.sidebar.error(f"CSV 로드 실패: {e}")

# 데이터 표시 영역
st.header("📋 기록된 항목")
if st.session_state.data.empty:
    st.info("아직 기록이 없어요. 사이드바에서 항목을 추가해 보세요.")
else:
    df = st.session_state.data.copy()
    # 정렬
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    # 인덱스(편집/삭제 편의)
    df.index.name = "idx"
    st.dataframe(df)

    # 삭제 기능
    st.markdown("#### 항목 삭제")
    to_delete = st.multiselect("삭제할 항목의 인덱스 선택", options=df.index.astype(int).tolist())
    if st.button("선택 항목 삭제"):
        if to_delete:
            st.session_state.data = st.session_state.data.drop(index=to_delete).reset_index(drop=True)
            st.success("삭제 완료")
            st.experimental_rerun()
        else:
            st.warning("삭제할 항목을 하나 이상 선택하세요.")

    # 요약 통계
    st.header("📊 요약")
    total_income = df.loc[df["type"] == "수입", "amount"].sum()
    total_expense = df.loc[df["type"] == "지출", "amount"].sum()
    balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("총 수입(원)", f"{int(total_income):,}")
    col2.metric("총 지출(원)", f"{int(total_expense):,}")
    col3.metric("잔액(원)", f"{int(balance):,}")

    # 카테고리별 지출 (파이/막대)
    st.subheader("카테고리별 지출")
    expense_by_cat = (
        df[df["type"] == "지출"].groupby("category")["amount"].sum().sort_values(ascending=False)
    )
    if not expense_by_cat.empty:
        st.bar_chart(expense_by_cat)
    else:
        st.write("지출 항목이 없어 카테고리 분석을 할 수 없습니다.")

    # 시간 흐름 그래프: 누적 잔액 변화
    st.subheader("시간 흐름 — 누적 잔액 변화")
    df_time = df.sort_values("date").copy()
    # 수입은 +, 지출은 -로 취급
    df_time["signed_amount"] = df_time.apply(lambda r: r["amount"] if r["type"] == "수입" else -r["amount"], axis=1)
    df_time["cumulative_balance"] = df_time["signed_amount"].cumsum()

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(df_time["date"], df_time["cumulative_balance"], marker="o", linewidth=2)
    ax.fill_between(df_time["date"], df_time["cumulative_balance"], alpha=0.12)
    ax.set_xlabel("날짜")
    ax.set_ylabel("누적 잔액(원)")
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    # 최근 항목(옵션)
    st.subheader("최근 5개 항목")
    st.table(df.head(5).reset_index(drop=True))

    # CSV 다운로드
    csv_buf = df.sort_values("date").to_csv(index=False).encode("utf-8")
    st.download_button("📥 CSV로 다운로드", data=csv_buf, file_name="allowance_data.csv", mime="text/csv")

# 도움말 / 팁
st.markdown("---")
st.info(
    "팁: GitHub에 저장한 app.py와 requirements.txt로 Streamlit Cloud에 배포하면,\n"
    "웹에서 친구들과 공유해서 함께 사용 가능해요."
)
