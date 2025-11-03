import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import time

def resultset ():
    st.dataframe(dfrs)
    st.subheader('다음 행동 선택')
    col_reset , col_next , col_save = st.columns(3)
    with col_reset:
        if st.button('처음부터 다시 시작하기', key='btn_reset'):
            st.session_state['df_original'] = None
            st.session_state['df_current'] = None
            st.warning('모든 정보가 삭제되고 파일 업로드 상태로 돌아갑니다.')
            time.sleep(3)
            st.session_state.reset_trigger += 1
            st.session_state.analysis_step_key += 1
            st.rerun()
    with col_next:
        if st.button('다음 분석에 결과 적용', key='btn_next'):
            st.session_state['df_current'] = dfrs
            st.success('결과가 저장되어 다음 분석에 사용됩니다.')
            time.sleep(3)
            st.session_state.analysis_step_key += 1
            st.rerun()
    with col_save:
        name = st.text_input("저장할 파일 이름을 적으세요.")
        if not name.strip():
            st.error("저장할 파일 이름을 반드시 입력해야 합니다.")
        else:
            st.download_button(label='결과 파일로 저장(CSV)', data=dfrs.to_csv(index=False).encode('utf-8'), file_name=f'{name}.csv',mime='text/csv')


if 'reset_trigger' not in st.session_state:
    st.session_state.reset_trigger = 0
if 'analysis_step_key' not in st.session_state:
    st.session_state.analysis_step_key = 0
if 'df_original' not in st.session_state:
    st.session_state['df_original'] = None
if 'df_current' not in st.session_state:
    st.session_state['df_current'] = None

st.header('정보 분석 사이트')
csvfile = st.file_uploader('파일을 업로드하세요.', type='csv',key=f"file_uploader_{st.session_state.reset_trigger}")
if csvfile is not None and st.session_state['df_original'] is None:
    try:
        st.session_state['df_original'] = pd.read_csv(csvfile)
    except UnicodeDecodeError:
        csvfile.seek(0)
        st.session_state['df_original'] = pd.read_csv(csvfile, encoding='cp949')
    # 초기 분석 대상은 원본 데이터로 설정
    st.session_state['df_current'] = st.session_state['df_original'].copy() 
    st.rerun() # 데이터 로드 후 새로고침하여 상태 반영

if st.session_state['df_current'] is not None:
    if st.session_state['df_current'].equals(st.session_state['df_original']):
        st.text('업로드한 파일 내용')
    else:
        st.text('수정된 파일 내용')
    df = st.session_state['df_current']
    st.dataframe(df)
    first_options = ['선택하세요','데이터 추출하기','결측치 제거하기','변수 추가하기','그래프로 출력하기']
    firstselect = st.selectbox('어떠한 분석을 하시겠습니까?',first_options,index=0,key=f'first_select_{st.session_state.analysis_step_key}')
    if firstselect == '데이터 추출하기':
        st.text('데이터 추출하기')
        second_option = ['선택하세요','조건에 맞는 데이터만 추출하기','필요한 변수만 추출하기','순서대로 정렬하기','집단별로 요약하기']
        secondselect = st.selectbox('어떠한 방법으로 전처리 하시겠습니까?',second_option,key=f'second_select_{st.session_state.analysis_step_key}')
        selected_index = second_option.index(secondselect)
        print(selected_index)
        if selected_index == 1:
            thirdselect = st.multiselect('어떤 데이터를 추출하시겠습니까?',df.columns)
            print(thirdselect)
            if len(thirdselect) > 0:
                query_conditions = []
                for index , columns_name in enumerate(thirdselect):
                    fourtyselect = st.selectbox(f'{columns_name}의 어떤 값을 추출하실겁니까?',df[columns_name].unique().tolist())
                    if df[columns_name].dtype == object or pd.api.types.is_string_dtype(df[columns_name]):
                        condition = f'{columns_name} == "{fourtyselect}"'
                    else:
                        condition = f'{columns_name} == {fourtyselect}'
                    print("hello" + condition)
                    query_conditions.append(condition)
                rs = ' or '.join(query_conditions)
                dfrs = df.query(rs)
                st.text('쿼리 결과')
                resultset()

        elif selected_index == 2:
            st.text('필요한 변수만 추출 및 제거')
            thirdselect = st.selectbox('추출하시겠습니까? 제거하시겠습니까?',['선택하세요','추출하기','제거하기'])
            if thirdselect == '추출하기':
                fourtyselect = st.multiselect('추출할 변수를 선택하세요.',df.columns)
                if len(fourtyselect) > 0:
                    dfrs = df[fourtyselect]
                    st.text('추출한 결과')
                    resultset()
            if thirdselect == '제거하기':
                fourtyselect = st.multiselect('제거할 변수를 선택하세요.',df.columns)
                if len(fourtyselect) > 0:
                    st.text('제거할 부분')
                    st.dataframe(df[fourtyselect])
                    dfrs = df.drop(columns = fourtyselect)
                    st.text('제거한 결과')
                    resultset()
        elif selected_index == 3:
            st.text('순서대로 정렬하기')
            thirdselect = st.selectbox('기준을 고르세요.',['선택하세요']+list(df.columns))
            if thirdselect != '선택하세요':
                fourtyselect = st.checkbox('정렬 순서를 선택하세요. (기본값: 오름차순)')
                if fourtyselect == '오름차순':
                    st.text(thirdselect + '기준으로 내림차순 정렬한 결과')
                    dfrs = df.sort_values(thirdselect , ascending=False)
                    resultset()
                else:
                    st.text(thirdselect + '기준으로 오름차순 정렬한 결과')
                    dfrs = df.sort_values(thirdselect)
                    resultset()
        elif selected_index == 4:
            st.text('집단별로 요약하기')
            thirdselect = st.selectbox('기준을 고르세요.',['선택하세요'] + list(df.columns))
            if thirdselect != '선택하세요':
                agg_text = st.text_input('추가할 변수명을 적으세요.')
                if agg_text:
                    fourtyselect = st.selectbox('원래 변수명',['선택하세요'] + list(df.columns))
                    if fourtyselect != '선택하세요':
                        fiftyselect = st.selectbox('함수명',['선택하세요','mean','std','sum','median','min','max','count'])
                        if fiftyselect != '선택하세요':
                            sixthselect = st.checkbox('정렬 순서를 선택하세요. (기본값: 오름차순)')
                            if sixthselect:
                                st.text('집단별로 요약한 결과')
                                dfrs = df.groupby(thirdselect , as_index = False).agg(**{agg_text : (fourtyselect , fiftyselect)}).sort_values(agg_text , ascending=False)
                                resultset()
                            else:
                                st.text('집단별로 요약한 결과')
                                dfrs = df.groupby(thirdselect , as_index = False).agg(**{agg_text : (fourtyselect , fiftyselect)}).sort_values(agg_text)
                                resultset()
    if firstselect == '결측치 제거하기':
        st.text('결측치 제거하기')
    if firstselect == '변수 추가하기':
        st.text('변수 추가하기')
    if firstselect == '그래프로 출력하기':
        st.text('그래프로 출력하기')