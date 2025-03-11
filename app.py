import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import re
from datetime import datetime

st.set_page_config(
    page_title="전기 케이블 가격 분석",
    page_icon="⚡",
    layout="wide"
)

# 스타일 적용
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stSelectbox, .stMultiSelect {
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_process_data():
    with open('onlycable.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # text 필드에서 필요한 정보만 추출
    text = data.get('text', '')
    
    # 데이터 추출을 위한 패턴
    year_pattern = r'(\d{4})년'
    size_pattern = r'(\d+(?:\.\d+)?SQ)'
    price_pattern = r'(\d{1,3}(?:,\d{3})*)'
    
    # 데이터 저장을 위한 리스트
    cable_data = []
    
    # 텍스트를 줄 단위로 분리
    lines = text.split('\n')
    current_year = None
    current_size = None
    
    for line in lines:
        # 연도 확인
        year_match = re.search(year_pattern, line)
        if year_match:
            current_year = year_match.group(1)
            continue
            
        # 사이즈 확인
        size_match = re.search(size_pattern, line)
        if size_match:
            current_size = size_match.group(1)
            continue
            
        # 가격 확인
        price_match = re.search(price_pattern, line)
        if price_match and current_year and current_size:
            price = int(price_match.group(1).replace(',', ''))
            if price > 0:  # 유효한 가격만 저장
                cable_data.append({
                    'year': int(current_year),
                    'size': current_size,
                    'price': price
                })
    
    # DataFrame 생성 및 정리
    df = pd.DataFrame(cable_data)
    df = df.drop_duplicates()
    df = df.sort_values(['year', 'size'])
    
    return df

def calculate_price_changes(df, size):
    size_data = df[df['size'] == size].sort_values('year')
    if len(size_data) >= 2:
        initial_price = size_data.iloc[0]['price']
        final_price = size_data.iloc[-1]['price']
        years_diff = size_data.iloc[-1]['year'] - size_data.iloc[0]['year']
        
        if years_diff > 0:
            total_change = ((final_price - initial_price) / initial_price) * 100
            avg_annual_change = ((final_price / initial_price) ** (1/years_diff) - 1) * 100
            return total_change, avg_annual_change
    return None, None

# 데이터 로드
df = load_and_process_data()

# 메인 타이틀
st.title('⚡ 전기 케이블 가격 분석 대시보드')
st.markdown('*가격 단위: 원/미터*')

# 사이드바 필터
st.sidebar.header('📊 분석 옵션')

# 연도 선택
available_years = sorted(df['year'].unique())
selected_years = st.sidebar.multiselect(
    '연도 선택',
    options=available_years,
    default=available_years
)

# 케이블 사이즈 선택
available_sizes = sorted(df['size'].unique())
selected_sizes = st.sidebar.multiselect(
    '케이블 사이즈 선택',
    options=available_sizes,
    default=available_sizes[:5] if len(available_sizes) > 5 else available_sizes
)

# 데이터 필터링
filtered_df = df[
    (df['year'].isin(selected_years)) &
    (df['size'].isin(selected_sizes))
]

# 메인 컨텐츠 영역을 두 컬럼으로 분할
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader('📈 연도별 케이블 가격 추이')
    
    fig = go.Figure()
    for size in selected_sizes:
        size_data = filtered_df[filtered_df['size'] == size]
        fig.add_trace(go.Scatter(
            x=size_data['year'],
            y=size_data['price'],
            name=size,
            mode='lines+markers'
        ))
    
    fig.update_layout(
        xaxis_title='연도',
        yaxis_title='가격 (원/m)',
        height=500,
        hovermode='x unified',
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader('📊 가격 변동률 분석')
    
    for size in selected_sizes:
        total_change, avg_annual_change = calculate_price_changes(filtered_df, size)
        if total_change is not None and avg_annual_change is not None:
            st.markdown(f"**{size}**")
            
            # 변동률에 따른 색상 설정
            total_color = 'red' if total_change > 0 else 'blue'
            annual_color = 'red' if avg_annual_change > 0 else 'blue'
            
            st.markdown(f"""
                - 총 변동률: <span style='color:{total_color}'>{total_change:,.2f}%</span>
                - 연평균 변동률: <span style='color:{annual_color}'>{avg_annual_change:,.2f}%</span>
            """, unsafe_allow_html=True)
            st.markdown("---")

# 데이터 테이블 표시
st.subheader('📋 상세 데이터')
st.dataframe(
    filtered_df.pivot(index='size', columns='year', values='price').round(2),
    use_container_width=True
) 