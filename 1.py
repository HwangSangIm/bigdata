import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import time
from pandas.errors import ParserError
import io
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.font_manager as fm

font_path = 'malgun.ttf' 
fm.fontManager.addfont(font_path) 
plt.rcParams['font.family'] =  'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

def convert_to_numeric_if_possible(value):
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        return value

def get_csv_options(file_object, header_delimiter=',', data_sep_candidates=[',','\t',';','|']):
    file_object.seek(0)
    encodings = ['cp949','euc-kr','utf-8-sig','utf-8']
    content_string = None
    successful_encoding = None

    for enc in encodings:
        file_object.seek(0)
        try:
            content_string = file_object.read().decode(enc)
            successful_encoding = enc
            break
        except UnicodeDecodeError:
            continue

    if content_string is None:
        raise Exception("모든 시도된 인코딩으로 파일 내용을 읽을 수 없습니다.")

    string_io = io.StringIO(content_string)
    lines = string_io.readlines()

    max_delimiters_overall = -1

    for line in lines[:50]:
        stripped_line = line.strip()
        delimiter_count = stripped_line.count(header_delimiter)
        if delimiter_count > max_delimiters_overall:
            max_delimiters_overall = delimiter_count
    
    threshold = max(1, int(max_delimiters_overall * 0.9))
    header_index = -1
    for i, line in enumerate(lines[:50]):
        stripped_line = line.strip()
        delimiter_count = stripped_line.count(header_delimiter)
        if delimiter_count >= threshold and delimiter_count > 0:
            header_index = i
            break
            
    skipped_lines_count = header_index if header_index != -1 else 0

    string_io.seek(0)
    for _ in range(skipped_lines_count + 1):
        string_io.readline()
    
    delimiter_counts = Counter()
    for i in range(5):
        line = string_io.readline()
        if not line:
            break
        for delim in data_sep_candidates:
            count = line.count(delim)
            if count > 0:
                delimiter_counts[delim] += 1

    final_sep = delimiter_counts.most_common(1)[0][0] if delimiter_counts else ','

    header_is_present = True
    
    try:
        temp_df = pd.read_csv(
            io.StringIO(content_string), 
            sep=final_sep, 
            encoding=successful_encoding, 
            skiprows=skipped_lines_count, 
            nrows=10, 
            header=0
        )
        
        unnamed_count = sum(['Unnamed' in str(col) for col in temp_df.columns])
        if unnamed_count > len(temp_df.columns) / 2:
             header_is_present = False

        if all(str(col).isdigit() for col in temp_df.columns):
             header_is_present = False

    except ParserError:
        header_is_present = False
    except Exception:
        header_is_present = False


    final_header_arg = 0 if header_is_present else None
    
    file_object.seek(0)

    return skipped_lines_count , successful_encoding , final_sep, final_header_arg

def clear_all_state():
    file_uploader_key = f"file_uploader_{st.session_state.reset_trigger}"
    if st.session_state[file_uploader_key] is None:
        st.session_state['df_original'] = None
        st.session_state['df_current'] = None
        if 'reset_trigger' in st.session_state:
            st.session_state.reset_trigger += 1
        else:
            st.session_state.reset_trigger = 0

def resultset (fig=None):
    global dfrs 
    
    # 데이터프레임 결과일 때만 테이블 표시
    if fig is None:
        st.dataframe(dfrs)
        st.subheader('다음 행동 선택')
    else:
        st.subheader('그래프 행동 선택') # 그래프일 때는 헤더 문구 변경
        
    col_reset , col_next , col_save = st.columns(3)
    
    with col_reset:
        if st.button('처음부터 다시 시작하기', key=f'btn_reset_{"graph" if fig else "data"}'): # 키 변경
            st.session_state['df_original'] = None
            st.session_state['df_current'] = None
            st.warning('모든 정보가 삭제되고 파일 업로드 상태로 돌아갑니다.')
            time.sleep(3)
            st.session_state.reset_trigger += 1
            st.session_state.analysis_step_key += 1
            st.rerun()
            
    with col_next:
        # 그래프 출력 시에도 현재의 dfrs(==df_current)를 다음 분석에 적용하는 것은 가능
        if fig is None:
            if st.button('다음 분석에 결과 적용', key=f'btn_next_{"graph" if fig else "data"}'): # 키 변경
                st.session_state['df_current'] = dfrs
                st.success('결과가 저장되어 다음 분석에 사용됩니다.')
                time.sleep(3)
                st.session_state.analysis_step_key += 1
                st.rerun()
        else:
            if st.button('그래프 생성 데이터 적용', key=f'btn_next_{"graph" if fig else "data"}'): # 키 변경
                st.session_state['df_current'] = dfrs
                st.success('결과가 저장되어 다음 분석에 사용됩니다.')
                time.sleep(3)
                st.session_state.analysis_step_key += 1
                st.rerun()
    with col_save:
        name = st.text_input("저장할 파일 이름을 적으세요.", key=f'save_input_{"graph" if fig else "data"}') # 키 변경
        
        if not name.strip():
            st.error("저장할 파일 이름을 반드시 입력해야 합니다.")
        else:
            if fig is None:
                # CSV 저장 (기존 기능)
                st.download_button(
                    label='결과 파일로 저장(CSV)', 
                    data=dfrs.to_csv(index=False).encode('utf-8'), 
                    file_name=f'{name}.csv',
                    mime='text/csv'
                )
            elif isinstance(fig, plt.Figure): 
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', bbox_inches='tight')
                img_buffer.seek(0)
                st.download_button(
                    label='결과 그래프로 저장(PNG)', 
                    data=img_buffer, 
                    file_name=f'{name}.png',
                    mime='image/png')
                plt.close(fig)
            elif isinstance(fig,go.Figure):
                html_data = fig.to_html(include_plotlyjs='cdn').encode('utf-8')
                st.download_button(label='결과 그래프로 저장(HTML)', data=html_data, file_name=f'{name}.html', mime='text/html')
            else:
                st.error("알 수 없는 유형의 그래프입니다.")
if 'reset_trigger' not in st.session_state:
    st.session_state.reset_trigger = 0
if 'analysis_step_key' not in st.session_state:
    st.session_state.analysis_step_key = 0
if 'df_original' not in st.session_state:
    st.session_state['df_original'] = None
if 'df_current' not in st.session_state:
    st.session_state['df_current'] = None
sideoption = st.sidebar.selectbox('menu',['파일 업로드','예시'])
if sideoption == '파일 업로드':
    st.header('정보 분석 사이트')
    csvfile = st.file_uploader('파일을 업로드하세요.', type='csv',key=f"file_uploader_{st.session_state.reset_trigger}",on_change=clear_all_state)
    if csvfile is not None and st.session_state['df_original'] is None:
        try:
            calculated_skiprows , encoding_used , final_sep , final_header_arg = get_csv_options(csvfile,header_delimiter=',')
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
            st.session_state['df_original'] = None
            st.stop()
        
        try:
            csvfile.seek(0)
            df_header_assumed = pd.read_csv(
                csvfile, 
                skiprows=calculated_skiprows, 
                encoding=encoding_used, 
                sep=final_sep,
                header=0
            )
            csvfile.seek(0)
            df_no_header_assumed = pd.read_csv(
                csvfile, 
                skiprows=calculated_skiprows, 
                encoding=encoding_used, 
                sep=final_sep,
                header=None
            )

            df_no_header_assumed.columns = [f'Col_{i}' for i in range(df_no_header_assumed.shape[1])]

            st.info("⚠️ **데이터 로드 설정 확인**")
            st.dataframe(df_header_assumed)
            st.text("자동 감지 결과:")
            
            default_index = 0 if final_header_arg == 0 else 1
            
            header_choice = st.radio(
                "업로드한 파일의 첫 번째 데이터 행이 **헤더(컬럼명)**가 맞습니까?",
                ["예, 헤더입니다. (첫 행을 컬럼명으로 사용)", "아니요, 데이터입니다. (자동 컬럼명: Col_0, Col_1...)"],
                index=default_index,
                key=f'header_choice_{st.session_state.reset_trigger}'
            )
            
            if header_choice == "예, 헤더입니다. (첫 행을 컬럼명으로 사용)":
                df_preview = df_header_assumed
            else:
                df_preview = df_no_header_assumed
                
            # 미리보기만 보여줍니다.
            st.subheader("선택 결과 미리보기 (상위 5줄)")
            st.dataframe(df_preview.head())
            
            st.warning('⚠️ **헤더 선택을 완료하셨다면, 아래 버튼을 클릭하여 분석을 시작하세요.**')

            # === 수정된 핵심 로직: 최종 세션 상태 저장은 버튼 클릭 시에만 수행 ===
            if st.button('데이터 확인 완료 및 분석 시작', key=f'start_analysis_{st.session_state.reset_trigger}'):
                # 선택에 따라 최종 데이터프레임 결정 및 세션 상태 저장
                if header_choice == "예, 헤더입니다. (첫 행을 컬럼명으로 사용)":
                    st.session_state['df_original'] = df_header_assumed.copy()
                else:
                    st.session_state['df_original'] = df_no_header_assumed.copy()
                
                st.session_state['df_current'] = st.session_state['df_original'].copy()
                st.rerun() # 버튼 클릭 후 다음 분석 단계로 진행

            st.stop() # 버튼을 누르기 전까지는 이 화면에서 멈춤

        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {e}")
            st.session_state['df_original'] = None
            st.stop()

    if st.session_state['df_current'] is not None:
        if st.session_state['df_current'].equals(st.session_state['df_original']):
            st.text('업로드한 파일 내용')
        else:
            st.text('수정된 파일 내용')
        df = st.session_state['df_current']
        df.columns = df.columns.str.replace(r'[^\w]', '', regex=True)
        df.columns = df.columns.str.replace('℃', '', regex=False)
        dfrs = df.copy()
        st.dataframe(df)
        first_options = ['선택하세요','데이터 추출하기','결측치 제어하기','변수 추가하기','그래프로 출력하기','정보확인']
        firstselect = st.selectbox('어떠한 분석을 하시겠습니까?',first_options,index=0,key=f'first_select_{st.session_state.analysis_step_key}')
        if firstselect == '데이터 추출하기':
            second_option = ['선택하세요','조건에 맞는 데이터만 추출하기','필요한 변수만 추출하기','순서대로 정렬하기','집단별로 요약하기','사용자 입력']
            secondselect = st.selectbox('어떠한 방법으로 전처리 하시겠습니까?',second_option,key=f'second_select_{st.session_state.analysis_step_key}')
            selected_index = second_option.index(secondselect)
            if selected_index == 1:
                query_oper = st.radio("선택한 조건들을 어떻게 연결하시겠습니까?",('AND','OR'), index=0)
                thirdselect = st.multiselect('어떤 데이터를 추출하시겠습니까?',df.columns)
                if len(thirdselect) > 0:
                    query_conditions = []
                    for index , columns_name in enumerate(thirdselect):
                        fourtyselect = st.selectbox(f'{columns_name}의 어떤 값을 추출하실겁니까?',df[columns_name].unique().tolist())
                        if df[columns_name].dtype == object or pd.api.types.is_string_dtype(df[columns_name]):
                            condition = f'`{columns_name}` == "{fourtyselect}"'
                        else:
                            condition = f'`{columns_name}` == {fourtyselect}'
                        query_conditions.append(condition)
                    rs = f'{query_oper.lower()}'.join(query_conditions)
                    dfrs = df.query(rs)
                    st.text('쿼리 결과')
                    resultset()

            elif selected_index == 2:
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
            elif selected_index == 5:
                agg_text = st.text_input("사용자가 원하는 내용을 입력해주세요. 예 : df.groupby('지점')")
                if agg_text:
                    try:
                        st.text('사용자가 원하는 대로 입력한 결과')
                        dfrs = eval(agg_text)
                        resultset()
                    except Exception as e:
                        st.error(f'코드 실행 중 오류가 발생했습니다. {e}')
        if firstselect == '결측치 제어하기':
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
                    dfrs_temp = df.copy() # 원본 df(df_current)에서 시작
                    dfrs_temp[thirdselect] = dfrs_temp[thirdselect].replace(r'^\s*$', np.nan, regex=True)
                    dfrs[thirdselect] = dfrs[thirdselect].replace(r'^\s*$',np.nan,regex=True)
                    na_count_before = dfrs_temp[thirdselect].isnull().any(axis=1).sum()
                    if na_count_before > 0:
                        removed_data = dfrs_temp[dfrs_temp[thirdselect].isna().any(axis=1)]
                        dfrs = dfrs_temp.dropna(subset=thirdselect)
                        st.text('제거할 데이터')
                        st.dataframe(removed_data)
                        st.text('결측치를 제거한 결과')
                        resultset()
                    else:
                        st.warning("선택한 컬럼들에는 제거할 결측치(또는 빈칸)가 없습니다.")
            if selected_index == 3:
                thirdselect = st.selectbox('어떤 데이터의 결측치 값을 바꾸겠습니까?(빈칸 포함)',['선택하세요'] + list(df.columns))
                if thirdselect != '선택하세요':
                    checktype = thirdselect
                    thirdtype = df[checktype].dtype
                    if thirdtype.kind in ('i','f'):
                        NaNChange = st.number_input('변경할 숫자를 입력하세요.')
                        if NaNChange:
                            dfrs[checktype] = dfrs[checktype].replace(r'^\s*$', np.nan, regex=True)
                            changeVal = float(NaNChange)
                            if thirdtype.kind == 'i':
                                changeVal = int(changeVal)
                            dfrs[checktype] = dfrs[checktype].fillna(changeVal)
                            st.text('변경할 데이터 (원본)')
                            st.dataframe(df[checktype])
                            st.text('결측치의 내용을 변경한 결과')
                            resultset()
                    elif thirdtype == 'object':
                        NaNChange = st.text_input('변경할 데이터를 입력하세요.')
                        if NaNChange:
                            dfrs[checktype] = dfrs[checktype].replace(r'^\s*$', np.nan, regex=True)
                            dfrs[checktype] = dfrs[checktype].fillna(NaNChange)
                            st.text('변경할 데이터 (원본)')
                            st.dataframe(df[checktype])
                            st.text('결측치의 내용을 변경한 결과')
                            resultset()
        if firstselect == '변수 추가하기':
            secondselect = st.selectbox('어떠한 변수를 추가하실건가요?',['선택하세요','상수 추가','기존 열을 이용한 계산','사용자 입력'])
            if secondselect == '상수 추가':
                byunsuName = st.text_input('변수 이름을 입력하세요')
                if byunsuName:
                    gap = st.text_input('값을 입력하세요')
                    if gap:
                        try:
                            if '.' in gap:
                                chgap = float(gap)
                            else:
                                chgap = int(gap)
                        except ValueError:
                            chgap = gap
                        dfrs[byunsuName] = chgap
                        st.text('상수를 추가한 결과')
                        resultset()
            if secondselect == '기존 열을 이용한 계산':
                byunsuName = st.text_input('변수 이름을 입력하세요.')
                if byunsuName:
                    thirdselect = st.selectbox('어떠한 계산을 하시겠습니까?',['선택하세요','기본 연산자 사용','스칼라(단일 값) 연산','단일 조건문'])
                    if thirdselect == '기본 연산자 사용':
                        fourtyselect = st.multiselect('데이터를 선택해주세요.(순서 상관 있습니다.)',df.select_dtypes(include=['number']).columns)
                        if fourtyselect:
                            fiftyselect = st.selectbox('기호를 선택하세요.',['선택하세요','+','-','*','/','%'])
                            if fiftyselect == '+':
                                if len(fourtyselect) >= 2:
                                    dfrs[byunsuName] = dfrs[fourtyselect].sum(axis=1)
                                    st.text('기존 열을 이용해 추가한 결과')
                                    resultset()
                            elif fiftyselect == '-':
                                if len(fourtyselect) == 2:
                                    dfrs[byunsuName] = dfrs[fourtyselect[0]] - dfrs[fourtyselect[1]]
                                    st.text('기존 열을 이용해 추가한 결과')
                                    resultset()
                                elif len(fourtyselect) > 2:
                                    st.error('뺄셈은 계산 기준이 명확하도록 두 개의 데이터만 선택해주세요.')
                                else:
                                    st.error('뺄셈을 위해 두 개의 데이터를 선택해야 합니다.')
                            elif fiftyselect == '*':
                                if len(fourtyselect) >= 2:
                                    dfrs[byunsuName] = dfrs[fourtyselect].prod(axis=1)
                                    st.text('기존 열을 이용해 추가한 결과')
                                    resultset()
                            elif fiftyselect == '/':
                                if len(fourtyselect) == 2:
                                    dfrs[byunsuName] = dfrs[fourtyselect[0]]/dfrs[fourtyselect[1]]
                                    st.text('기존 열을 이용해 추가한 결과')
                                    resultset()
                                elif len(fourtyselect) >2:
                                    st.error('나눗셈은 계산 기준이 명확하도록 두 개의 데이터만 선택해주세요.')
                                else:
                                    st.error('나눗셈을 위해 두 개의 데이터를 선택해야 합니다.')
                            elif fiftyselect == '%':
                                if len(fourtyselect) == 2:
                                    dfrs[byunsuName] = dfrs[fourtyselect[0]] % dfrs[fourtyselect[1]]
                                    st.text('기존 열을 이용해 추가한 결과')
                                    resultset()
                                elif len(fourtyselect) >2:
                                    st.error('나머지는 계산 기준이 명확하도록 두 개의 데이터만 선택해주세요.')
                                else:
                                    st.error('나머지를 위해 두 개의 데이터를 선택해야 합니다.')
                            else:
                                st.error('연산을 선택해주세요.')
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
                                    ch_true = convert_to_numeric_if_possible(true_su)
                                    ch_false = convert_to_numeric_if_possible(false_su)
                                    changeStr = f"dfrs['{fourtyselect}']{fiftyselect}{su}"
                                    condition_str = eval(changeStr)
                                    dfrs[byunsuName] = np.where(condition_str,ch_true,ch_false)
                                    st.text('기존 열을 이용해 추가한 결과')
                                    resultset()
            if secondselect == '사용자 입력':
                byunsuName = st.text_input('변수를 입력해주세요.')
                if byunsuName:
                    codeName = st.text_input('사용자가 원하는 내용을 입력해주세요. 예) df[변수명1] + df[변수명2]')
                    if codeName:
                        try:
                            codeChange = eval(codeName)
                            if isinstance(codeChange, pd.Series):
                                if pd.api.types.is_datetime64_any_dtype(codeChange):
                                    final_rs = codeChange
                                else:
                                    final_rs = pd.to_numeric(codeChange, errors='ignore')
                            elif isinstance(codeChange, str):
                                try:
                                    if '.' in codeChange:
                                        final_rs = float(codeChange)
                                    else:
                                        final_rs = int(codeChange)
                                except ValueError:
                                    pass
                            if pd.api.types.is_datetime64_any_dtype(final_rs):
                                dfrs[byunsuName] = final_rs
                                dfrs[byunsuName] = dfrs[byunsuName].dt.date
                            else:
                                dfrs[byunsuName] = final_rs
                            st.text('사용자의 입력에 의한 결과')
                            resultset()
                        except Exception as e:
                            st.error("코드 실행 중 오류가 발생했습니다.")
        if firstselect == '그래프로 출력하기':
            fig , ax = plt.subplots()
            secondselect = st.selectbox('어떤 그래프를 그리겠습니까?',['선택하세요','산점도로 표현하기','막대 그래프로 표현하기','선 그래프로 표현하기','상자 그림으로 표현하기'])
            if secondselect == '산점도로 표현하기':
                x_options = ['선택하세요'] + list(df.columns)
                y_options = ['선택하세요'] + list(df.columns)
                fo = st.selectbox('x축에 넣을 데이터를 고르세요.',x_options)
                so = st.selectbox('y축에 넣을 데이터를 고르세요.',y_options)
                if fo != '선택하세요' and so != '선택하세요':
                    thirdselect = st.selectbox('어떤 방식으로 그리겠습니까?',['선택하세요','seaborn','plotly'])
                    if thirdselect == 'seaborn':
                        sns.scatterplot(x=fo , y = so , ax=ax,data=df)
                        ax.set_xlabel(fo)
                        ax.set_ylabel(so)
                        st.pyplot(fig)
                        resultset(fig=fig)
                    elif thirdselect == 'plotly':
                        fig_plotly = px.scatter(df, x=fo , y=so)
                        st.plotly_chart(fig_plotly, width='stretch')
                        resultset(fig=fig_plotly)
                        plt.close(fig)
                    else:
                        plt.close(fig)
                else:
                    plt.close(fig)
            elif secondselect == '막대 그래프로 표현하기':
                x_options = ['선택하세요'] + list(df.columns)
                y_options = ['선택하세요'] + list(df.columns)
                fo = st.selectbox('x축에 넣을 데이터를 고르세요.',x_options)
                so = st.selectbox('y축에 넣을 데이터를 고르세요.',y_options)
                if fo != '선택하세요' and so != '선택하세요':
                    thirdselect = st.selectbox('어떤 방식으로 그리겠습니까?',['선택하세요','seaborn','plotly'])
                    if thirdselect == 'seaborn':
                        sns.barplot(x=fo , y = so , ax=ax,data=df)
                        ax.set_xlabel(fo)
                        ax.set_ylabel(so)
                        st.pyplot(fig)
                        resultset(fig=fig)
                    elif thirdselect == 'plotly':
                        fig_plotly = px.bar(df, x=fo , y=so)
                        st.plotly_chart(fig_plotly, width='stretch')
                        resultset(fig=fig_plotly)
                        plt.close(fig)
                    else:
                        plt.close(fig)
                else:
                    plt.close(fig)
            if secondselect =='선 그래프로 표현하기':
                x_options = ['선택하세요'] + list(df.columns)
                y_options = ['선택하세요'] + list(df.columns)
                fo = st.selectbox('x축에 넣을 데이터를 고르세요.',x_options)
                so = st.selectbox('y축에 넣을 데이터를 고르세요.',y_options)
                if fo != '선택하세요' and so != '선택하세요':
                    thirdselect = st.selectbox('어떤 방식으로 그리겠습니까?',['선택하세요','seaborn','plotly'])
                    if thirdselect == 'seaborn':
                        sns.lineplot(x=fo , y = so , ax=ax,data=df)
                        ax.set_xlabel(fo)
                        ax.set_ylabel(so)
                        st.pyplot(fig)
                        resultset(fig=fig)
                    elif thirdselect == 'plotly':
                        fig_plotly = px.line(df, x=fo , y=so)
                        st.plotly_chart(fig_plotly, width='stretch')
                        resultset(fig=fig_plotly)
                        plt.close(fig)
                    else:
                        plt.close(fig)
                else:
                    plt.close(fig)
            if secondselect =='상자 그림으로 표현하기':
                x_options = ['선택하세요'] + list(df.columns)
                y_options = ['선택하세요'] + list(df.columns)
                fo = st.selectbox('x축에 넣을 데이터를 고르세요.',x_options)
                so = st.selectbox('y축에 넣을 데이터를 고르세요.',y_options)
                if fo != '선택하세요' and so != '선택하세요':
                    thirdselect = st.selectbox('어떤 방식으로 그리겠습니까?',['선택하세요','seaborn','plotly'])
                    if thirdselect == 'seaborn':
                        sns.boxplot(x=fo , y = so , ax=ax,data=df)
                        ax.set_xlabel(fo)
                        ax.set_ylabel(so)
                        st.pyplot(fig)
                        resultset(fig=fig)
                    elif thirdselect == 'plotly':
                        fig_plotly = px.box(df, x=fo , y=so)
                        st.plotly_chart(fig_plotly, width='stretch')
                        resultset(fig=fig_plotly)
                        plt.close(fig)
                    else:
                        plt.close(fig)
                else:
                    plt.close(fig)
        if firstselect == '정보확인':
            buffer = io.StringIO()
            df.info(buf=buffer)
            info_string = buffer.getvalue()
            st.code(info_string, language='text')
            st.dataframe(df.describe())
if sideoption == '예시':
    if st.session_state['df_original'] is not None or st.session_state['df_current'] is not None:
        st.session_state['df_original'] = None
        st.session_state['df_current'] = None
        st.session_state.reset_trigger += 1
        st.session_state.analysis_step_key += 1
        st.rerun() # 변경 사항을 바로 적용
    st.header("예시 페이지")
    st.text("예시입니다.")
    image_url1 = "https://github.com/HwangSangIm/bigdata/blob/main/%EC%98%88%EC%8B%9C1.png?raw=true"
    image_url2 = "https://github.com/HwangSangIm/bigdata/blob/main/%EC%98%88%EC%8B%9C2.png?raw=true"
    image_url3 = "https://github.com/HwangSangIm/bigdata/blob/main/%EC%98%88%EC%8B%9C3.png?raw=true"
    st.text('사용자가 원하는대로 데이터를 추출한 결과')
    st.image(image_url1)
    st.text('막대 그래프(plotly)로 출력한 결과')
    st.image(image_url2)
    st.text('결측치를 변경한 결과')
    st.image(image_url3)
