import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import time

# 페이지 설정
st.set_page_config(page_title="Recruit Searching", layout="wide")

def crawl_saramin():
    """사람인 데이터 크롤링"""
    base_url = "https://www.saramin.co.kr/zf_user/search"
    params = {
        'search_area': 'main',
        'search_done': 'y', 
        'search_optional_item': 'n',
        'searchType': 'search',
        'searchword': '데이터분석'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(base_url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    job_items = soup.find_all('div', class_='item_recruit')
    
    for item in job_items:
        company_elem = item.find('strong', class_='corp_name')
        company = company_elem.get_text(strip=True) if company_elem else 'N/A'

        title_elem = item.find('h2', class_='job_tit')
        title = 'N/A'
        url = 'N/A'
        
        if title_elem:
            title_link = title_elem.find('a')
            if title_link:
                title = title_link.get_text(strip=True)
                href = title_link.get('href', '')
                if href.startswith('/zf_user'):
                    url = f"https://www.saramin.co.kr{href}"
                elif href.startswith('http'):
                    url = href
        
        condition_elem = item.find('div', class_='job_condition')
        conditions = []
        if condition_elem:
            condition_spans = condition_elem.find_all('span')
            for span in condition_spans:
                text = span.get_text(strip=True)
                if text and text not in ['↑', '↓', '|']:
                    conditions.append(text)
        
        requirement = ' | '.join(conditions) if conditions else 'N/A'
        
        jobs.append({
            'Site': 'Saramin',
            'Col_Company': company,
            'Col_Recruit': title,
            'Col_detail': requirement,
            'Col_URL': url
        })
    
    return pd.DataFrame(jobs)

def crawl_jobkorea_data():
    """잡코리아 데이터 크롤링"""
    url = "https://www.jobkorea.co.kr/Search/?stext=%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B6%84%EC%84%9D&Page_No=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    job_data = []

    job_list = []
    
    title_links = soup.find_all('a', href=lambda href: href and '/Recruit/GI_Read/' in href)
    
    processed_urls = set() 
    
    for link in title_links:
        href = link.get('href', '')
        if href in processed_urls:
            continue
        processed_urls.add(href)
        
        current = link
        job_container = None
        
        for level in range(7): 
            current = current.parent
            if current is None:
                break
            
            if current.name in ['div', 'li', 'article']:
                company_check = current.find('span', class_=lambda x: x and 'Typography_variant_size16' in str(x))
                detail_check = current.find('div', class_=lambda x: x and 'Flex_gap_space16' in str(x))
                
                if company_check and detail_check:
                    job_container = current
                    break
                elif level >= 4: 
                    job_container = current
                    break
        
        if job_container:
            job_list.append(job_container)
    
    for idx, job_container in enumerate(job_list, 1):
        company_elem = job_container.find('a', style=lambda style: style and 'max-width:120px' in style)
        if not company_elem:
            company_elem = job_container.find('span', class_=lambda x: x and 'Typography_variant_size16' in str(x))
        
        company = company_elem.get_text(strip=True) if company_elem else "회사명 없음"
        
        title_elem = job_container.find('a', class_='h7nnv12')
        if title_elem:
            title_span = title_elem.find('span', class_=lambda x: x and 'Typography_variant_size18' in str(x) and 'Typography_truncate' in str(x))
            if title_span:
                title = title_span.get_text(strip=True)
            else:
                title = title_elem.get_text(strip=True)
            
            job_url = urljoin("https://www.jobkorea.co.kr", title_elem['href'])
        else:
            title = "제목 없음"
            job_url = "URL 없음"
        
        detail_div = job_container.find('div', class_=lambda x: x and 'Flex_gap_space16' in str(x))
        if detail_div:
            detail_spans = detail_div.find_all('span', class_=lambda x: x and 'Typography_variant_size14' in str(x) and 'Typography_color_gray800' in str(x))
            details = [span.get_text(strip=True) for span in detail_spans if span.get_text(strip=True)]
            detail = ' | '.join(details) if details else "상세정보 없음"
        else:
            all_spans = job_container.find_all('span')
            details = []
            for span in all_spans:
                text = span.get_text(strip=True)
                if (text and text not in [title, company] and 
                    any(keyword in text for keyword in ['경력', '학력', '정규직', '계약직', '인턴', '구', '시', '월', '일'])):
                    details.append(text)
            detail = ' | '.join(details[:5]) if details else "상세정보 없음"
        
        job_data.append({
            'Site': 'Job_Korea',
            'Col_Company': company,
            'Col_Recruit': title,
            'Col_detail': detail,
            'Col_URL': job_url
        })

    return pd.DataFrame(job_data)

st.title("Title")

if st.button("Recruit Searching", key="recruit_btn"):
    st.session_state.show_results = True

if st.session_state.get('show_results', False):
    st.markdown("---")
    st.title("Title")
    
    with st.spinner('채용공고 수집 중...'):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text('사람인에서 데이터분석 채용공고를 수집 중...')
            progress_bar.progress(25)
            saramin_df = crawl_saramin()
            
            status_text.text('잡코리아에서 데이터분석 채용공고를 수집 중...')
            progress_bar.progress(50)
            jobkorea_df = crawl_jobkorea_data()
            
            status_text.text('데이터를 정리하는 중...')
            progress_bar.progress(75)
            
            if 'Col_URL' in saramin_df.columns:
                saramin_df = saramin_df.rename(columns={'Col_URL': 'Col_url'})
            
            combined_df = pd.concat([saramin_df, jobkorea_df], ignore_index=True)
            
            status_text.text('데이터를 저장하는 중...')
            progress_bar.progress(90)
            
            if not os.path.exists('data_tmp'):
                os.makedirs('data_tmp')
            
            progress_bar.progress(100)
            status_text.text('수집 완료!')
            
            # 사이트별 집계 계산
            site_counts = combined_df['Site'].value_counts().reset_index()
            site_counts.columns = ['Site', 'Count']
            
            # 비율 계산
            total_count = site_counts['Count'].sum()
            site_counts['Ratio'] = (site_counts['Count'] / total_count * 100).round(2)
            
            # 프로그레스 바와 상태 텍스트 제거
            progress_bar.empty()
            status_text.empty()
            
            # 레이아웃 설정
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 채용 정보 테이블
                st.subheader("Recruit Searching")
                
                # 컬럼 순서 조정 (Site를 첫 번째로)
                display_columns = ['Site'] + [col for col in combined_df.columns if col != 'Site']
                display_df = combined_df[display_columns]
                
                # 테이블 표시
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400
                )
                
                # 사이트별 집계 테이블
                st.subheader("")
                st.dataframe(
                    site_counts,
                    use_container_width=True,
                    height=150,
                    hide_index=True
                )
            
            with col2:
                # 파이차트
                st.subheader("Recruitment Ratio")
                
                # 파이차트 생성
                fig = px.pie(
                    site_counts, 
                    values='Count', 
                    names='Site',
                    color_discrete_sequence=['#1f77b4', '#87ceeb']  # 진한 파란색, 연한 파란색
                )
                
                # 차트 스타일 설정
                fig.update_traces(
                    textposition='inside', 
                    textinfo='percent',
                    textfont_size=12
                )
                
                fig.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.01
                    ),
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            # 요약 정보 표시
            st.success(f"🎉 총 {len(combined_df)}개의 채용공고를 수집했습니다!")
            st.info(f"📊 사람인: {len(saramin_df)}개, 잡코리아: {len(jobkorea_df)}개")
            
        except Exception as e:
            st.error(f"크롤링 중 오류가 발생했습니다: {e}")
            st.info("잠시 후 다시 시도해주세요.")

# 초기 상태에서는 버튼만 표시
else:
    st.write("")  # 공백 추가
