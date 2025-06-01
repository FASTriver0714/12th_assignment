import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Recruit Searching", layout="wide")

st.title("Title")

if st.button("Recruit Searching", key="recruit_btn"):
    st.session_state.show_results = True

if st.session_state.get('show_results', False):
    st.markdown("---")
    st.title("Title")
    
    try:
        saramin_df = pd.read_csv("data_tmp/data_saramin.csv")
        jobkorea_df = pd.read_csv("data_tmp/jobkorea_data_analysis.csv")
        
        saramin_df['Site'] = 'Saramin'
        jobkorea_df['Site'] = 'Job_Korea'
        
        combined_df = pd.concat([saramin_df, jobkorea_df], ignore_index=True)
        
        site_counts = combined_df['Site'].value_counts().reset_index()
        site_counts.columns = ['Site', 'Count']
        
        total_count = site_counts['Count'].sum()
        site_counts['Ratio'] = (site_counts['Count'] / total_count * 100).round(2)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Recruit Searching")
            
            display_columns = ['Site'] + [col for col in combined_df.columns if col != 'Site']
            display_df = combined_df[display_columns]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
            
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
            
            fig = px.pie(
                site_counts, 
                values='Count', 
                names='Site',
                color_discrete_sequence=['#1f77b4', '#87ceeb']  # 진한 파란색, 연한 파란색
            )
            
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
            
        st.info(f"총 채용공고 수: {len(combined_df)}개 (사람인: {len(saramin_df)}개, 잡코리아: {len(jobkorea_df)}개)")
    
    except FileNotFoundError as e:
        st.error(f"데이터 파일을 찾을 수 없습니다: {e}")
        st.info("data_tmp 폴더에 다음 파일들이 있는지 확인해주세요:")
        st.write("- saramin.csv")
        st.write("- jobkorea.csv")
    
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")

else:
    st.write("")  
