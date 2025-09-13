import pandas as pd
import glob

# 가장 최근 temp_upload 파일 찾기
files = glob.glob('temp_upload*.xlsx')
if files:
    latest_file = files[-1]
    print(f"Checking file: {latest_file}")
    
    df = pd.read_excel(latest_file)
    
    # 고유코드 컬럼에서 중복 확인
    duplicates = df[df.duplicated('고유코드', keep=False)]
    
    if len(duplicates) > 0:
        print(f"\n중복된 고유코드가 {len(duplicates)}개 발견됨:")
        print(duplicates[['고유코드', '식자재명']].head(20))
        
        # 3200972 코드 확인
        code_3200972 = df[df['고유코드'] == 3200972]
        if len(code_3200972) > 0:
            print(f"\n코드 3200972가 {len(code_3200972)}번 나타남")
    else:
        print("중복된 고유코드 없음")
else:
    print("No temp_upload files found")