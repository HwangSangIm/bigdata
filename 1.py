import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import time

def clear_all_state():
    file_uploader_key = f"file_uploader_{st.session_state.reset_trigger}"
    if st.session_state[file_uploader_key] is None:
        st.session_state['df_original'] = None
        st.session_state['df_current'] = None
        if 'reset_trigger' in st.session_state:
            st.session_state.reset_trigger += 1
        else:
            st.session_state.reset_trigger = 0

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
csvfile = st.file_uploader('파일을 업로드하세요.', type='csv',key=f"file_uploader_{st.session_state.reset_trigger}",on_change=clear_all_state)
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
    dfrs = df.copy()
    st.dataframe(df)
    first_options = ['선택하세요','데이터 추출하기','결측치 제어하기','변수 추가하기','그래프로 출력하기']
    firstselect = st.selectbox('어떠한 분석을 하시겠습니까?',first_options,index=0,key=f'first_select_{st.session_state.analysis_step_key}')
    if firstselect == '데이터 추출하기':
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
                if fourtyselect:
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
    if firstselect == '결측치 제어하기':
        st.text('결측치 제어하기')
        second_option = ['선택하세요','결측치 확인','결측치 제거','결측치 변경']
        secondselect = st.selectbox('어떠한 방법을 사용하시겠습니까?',second_option)
        selected_index = second_option.index(secondselect)
        if selected_index == 1:
            thirdselect = st.multiselect('어떤 데이터의 결측치를 확인하시겠습니까?',df.columns)
            if len(thirdselect) > 0:
                dfrs = df[thirdselect].isna().sum()
                st.dataframe(dfrs)
        if selected_index == 2:
            thirdselect = st.multiselect('어떤 데이터 결측치를 제거하시겠습니까?(빈칸 포함)',df.columns)
            if len(thirdselect) > 0:
                dfrs[thirdselect] = dfrs[thirdselect].replace(r'^\s*$',np.nan,regex=True)
                dfrs = df.dropna(subset=thirdselect)
                st.text('제거할 데이터')
                st.dataframe(df[thirdselect])
                st.text('결측치를 제거한 결과')
                resultset()
        if selected_index == 3:
            thirdselect = st.multiselect('어떤 데이터의 결측치 값을 바꾸겠습니까?(빈칸 포함)',df.columns)
            if len(thirdselect) > 0:
                count = 0
                for checktype in thirdselect:
                    checktype = thirdselect[count]
                    thirdtype = df[checktype].dtype
                    
                    if thirdtype.kind in ('i','f'):
                        NaNChange = st.text_input('변경할 숫자를 입력하세요.', key=f'input_int_{checktype}')
                        if NaNChange:
                            dfrs[checktype] = dfrs[checktype].replace(r'^\s*$',np.nan,regex=True)
                            changeVal = float(NaNChange)
                            if thirdtype.kind == 'i':
                                changeVal = int(changeVal)
                            dfrs[checktype] = dfrs[checktype].fillna(changeVal)
                            count = count + 1
                    elif thirdtype == 'object':
                        NaNChange = st.text_input('변경할 이름을 입력하세요.', key=f'input_object_{checktype}')
                        if NaNChange:
                            dfrs[checktype] = dfrs[checktype].replace(r'^\s*$',np.nan,regex=True)
                            dfrs[checktype] = dfrs[checktype].fillna(NaNChange)
                            count = count + 1
                if count == len(thirdselect):
                    st.text('변경할 데이터')
                    st.dataframe(df[thirdselect])
                    dfrs = df
                    st.text('결측치의 내용을 변경한 결과')
                    resultset()
    if firstselect == '변수 추가하기':
        st.text('변수 추가하기')
        secondselect = st.selectbox('어떠한 변수를 추가하실건가요?',['선택하세요','상수 추가','기존 열을 이용한 계산','사용자 입력'])
        if secondselect == '상수 추가':
            byunsuName = st.text_input('변수 이름을 입력하세요')
            if byunsuName:
                gap = st.text_input('값을 입력하세요')
                if gap:
                    dfrs[byunsuName] = gap
                    st.text('상수를 추가한 결과')
                    resultset()
        if secondselect == '기존 열을 이용한 계산':
            byunsuName = st.text_input('변수 이름을 입력하세요.')
            if byunsuName:
                thirdselect = st.selectbox('어떠한 계산을 하시겠습니까?',['선택하세요','기본 연산자 사용','스칼라(단일 값) 연산','단일 조건문'])
                if thirdselect == '기본 연산자 사용':
                    fourtyselect = st.multiselect('데이터를 선택헤주세요.(순서 상관 있습니다.)',df.select_dtypes(include=['number']).columns)
                    if fourtyselect:
                        fiftyselect = st.selectbox('기호를 선택하세요.',['선택하세요','+','-','*','/','%'])
                        if fiftyselect == '+':
                            dfrs[byunsuName] = dfrs[fourtyselect].sum(axis=1)
                            st.text('기존 열을 이용해 추가한 결과')
                            resultset()
                        if fiftyselect == '-':
                            if len(fourtyselect) == 2:
                                dfrs[byunsuName] = dfrs[fourtyselect[0]] - dfrs[fourtyselect[1]]
                                st.text('기존 열을 이용해 추가한 결과')
                                resultset()
                            elif len(fourtyselect) > 2:
                                st.error('뺄셈은 계산 기준이 명확하도록 두 개의 데이터만 선택해주세요.')
                            else:
                                st.error('뺄셈을 위해 두 개의 데이터를 선택해야 합니다.')
                        if fiftyselect == '*':
                            dfrs[byunsuName] = dfrs[fourtyselect].prod(axis=1)
                            st.text('기존 열을 이용해 추가한 결과')
                            resultset()
                        if fiftyselect == '/':
                            if len(fourtyselect) == 2:
                                dfrs[byunsuName] = dfrs[fourtyselect[0]]/dfrs[fourtyselect[1]]
                                st.text('기존 열을 이용해 추가한 결과')
                                resultset()
                            elif len(fourtyselect) >2:
                                st.error('나눗셈은 계산 기준이 명확하도록 두 개의 데이터만 선택해주세요.')
                            else:
                                st.error('나눗셈을 위해 두 개의 데이터를 선택해야 합니다.')
                        if fiftyselect == '%':
                            if len(fourtyselect) == 2:
                                dfrs[byunsuName] = dfrs[fourtyselect[0]] % dfrs[fourtyselect[1]]
                                st.text('기존 열을 이용해 추가한 결과')
                                resultset()
                            elif len(fourtyselect) >2:
                                st.error('나머지는 계산 기준이 명확하도록 두 개의 데이터만 선택해주세요.')
                            else:
                                st.error('나머지를 위해 두 개의 데이터를 선택해야 합니다.')
                if thirdselect == '스칼라(단일 값) 연산':
                    fourtyselect = st.selectbox('데이터를 선택해주세요.',['선택하세요']+list(df.select_dtypes(include=['number']).columns))
                    if fourtyselect != '선택하세요':
                        fiftyselect = st.selectbox('기호를 입력해주세요.',['선택하세요','+','-','*','/','%'])
                        if fiftyselect !='선택하세요':
                            su = st.number_input('값을 입력해주세요.')
                            if su:
                                changeStr = f"dfrs['{fourtyselect}'] {fiftyselect} {su}"
                                condition_str = eval(changeStr)
                                dfrs[byunsuName] = condition_str
                                st.text('기존 열을 이용해 추가한 결과')
                                resultset()
                if thirdselect == '단일 조건문':
                    fourtyselect = st.selectbox('데이터를 선택해주세요.',['선택하세요']+list(df.select_dtypes(include=['number']).columns))
                    if fourtyselect != '선택하세요':
                        fiftyselect = st.selectbox('연산자를 선택해주세요.',['선택하세요','>','<','>=','<=','==','!='])
                        if fiftyselect !='선택하세요':
                            su = st.number_input('기준 값을 입력해주세요.')
                            true_su = st.text_input('조건이 참일 경우 할당할 값 입력')
                            false_su = st.text_input('조건이 거짓일 경우 할당할 값 입력')
                            if true_su.strip() and false_su.strip():
                                changeStr = f"dfrs['{fourtyselect}']{fiftyselect}{su}"
                                condition_str = eval(changeStr)
                                dfrs[byunsuName] = np.where(condition_str,true_su,false_su)
                                st.text('기존 열을 이용해 추가한 결과')
                                resultset()
        if secondselect == '사용자 입력':
            byunsuName = st.text_input('변수를 입력해주세요.')
            if byunsuName:
                codeName = st.text_input('사용자가 원하는 내용을 입력해주세요. 예) df[변수명1] + df[변수명2]')
                if codeName:
                    try:
                        codeChange = eval(codeName)
                        dfrs[byunsuName] = codeChange
                        st.text('사용자의 입력에 의한 결과')
                        resultset()
                    except Exception as e:
                        st.error("코드 실행 중 오류가 발생했습니다.")
    if firstselect == '그래프로 출력하기':
        st.text('그래프로 출력하기')
