"""
Enhanced Upload System Test
개선된 파일 업로드 시스템 테스트 스크립트
"""

import os
import time
import requests
import pandas as pd
from pathlib import Path

def create_test_excel_file():
    """테스트용 대용량 엑셀 파일 생성"""
    print("테스트용 엑셀 파일 생성 중...")
    
    # 대용량 데이터 생성 (10,000개 식자재)
    data = []
    categories = ['채소류', '육류', '수산물', '곡류', '양념류', '유제품', '냉동식품', '기타']
    units = ['kg', '개', 'g', 'L', '포', '박스']
    suppliers = ['사조푸디스트', '동원홈푸드', '현대그린푸드', 'CJ', '영유통']
    
    for i in range(10000):
        data.append({
            '식자재명': f'테스트식자재_{i+1:05d}',
            '분류': categories[i % len(categories)],
            '단위': units[i % len(units)],
            '단가': round(1000 + (i * 10.5), 2),
            '공급업체': suppliers[i % len(suppliers)],
            '규격': '1kg' if i % 3 == 0 else '500g',
            '비고': f'테스트 데이터 {i+1}'
        })
    
    df = pd.DataFrame(data)
    test_file = Path('test_ingredients_10k.xlsx')
    df.to_excel(test_file, index=False, sheet_name='식자재목록')
    
    print(f"테스트 파일 생성 완료: {test_file}")
    print(f"파일 크기: {test_file.stat().st_size / (1024*1024):.2f}MB")
    print(f"데이터 행 수: {len(df):,}개")
    
    return test_file

def test_file_validation():
    """파일 유효성 검사 테스트"""
    print("\n=== 파일 유효성 검사 테스트 ===")
    
    test_cases = [
        {'filename': 'test.xlsx', 'file_size': 1024*1024, 'expected': True},
        {'filename': 'test.txt', 'file_size': 1024, 'expected': False},  # 잘못된 확장자
        {'filename': 'huge_file.xlsx', 'file_size': 200*1024*1024, 'expected': False},  # 너무 큰 파일
    ]
    
    for case in test_cases:
        try:
            response = requests.post('http://localhost:5000/api/upload/validate', 
                json={
                    'filename': case['filename'],
                    'file_size': case['file_size']
                }
            )
            
            result = response.json()
            print(f"파일: {case['filename']}")
            print(f"  - 유효성: {'통과' if result['valid'] == case['expected'] else '실패'}")
            if not result['valid']:
                print(f"  - 오류: {result['errors']}")
            print()
            
        except Exception as e:
            print(f"테스트 오류: {e}")

def test_chunked_upload(file_path):
    """청크 업로드 테스트"""
    print("\n=== 청크 업로드 테스트 ===")
    
    if not file_path.exists():
        print("테스트 파일이 없습니다.")
        return None
    
    file_size = file_path.stat().st_size
    chunk_size = 2 * 1024 * 1024  # 2MB
    total_chunks = (file_size + chunk_size - 1) // chunk_size
    
    print(f"파일: {file_path.name}")
    print(f"크기: {file_size / (1024*1024):.2f}MB")
    print(f"청크 수: {total_chunks}개")
    
    try:
        # 1. 업로드 시작
        start_response = requests.post('http://localhost:5000/api/upload/start',
            json={
                'filename': file_path.name,
                'file_size': file_size,
                'total_chunks': total_chunks
            }
        )
        
        start_result = start_response.json()
        if not start_result['success']:
            print(f"업로드 시작 실패: {start_result['error']}")
            return None
        
        upload_id = start_result['upload_id']
        print(f"업로드 ID: {upload_id}")
        
        # 2. 청크 업로드
        with open(file_path, 'rb') as f:
            for chunk_index in range(total_chunks):
                chunk_data = f.read(chunk_size)
                
                files = {'chunk': chunk_data}
                data = {
                    'upload_id': upload_id,
                    'chunk_index': chunk_index
                }
                
                chunk_response = requests.post('http://localhost:5000/api/upload/chunk',
                    files=files,
                    data=data
                )
                
                chunk_result = chunk_response.json()
                if not chunk_result['success']:
                    print(f"청크 {chunk_index} 업로드 실패: {chunk_result['error']}")
                    return None
                
                progress = chunk_result.get('progress', 0)
                print(f"청크 {chunk_index+1}/{total_chunks} 업로드 완료 ({progress:.1f}%)")
        
        # 3. 업로드 완료
        complete_response = requests.post('http://localhost:5000/api/upload/complete',
            json={'upload_id': upload_id}
        )
        
        complete_result = complete_response.json()
        if not complete_result['success']:
            print(f"업로드 완료 실패: {complete_result['error']}")
            return None
        
        print("업로드 완료! 백그라운드 처리 시작됨")
        return upload_id
        
    except Exception as e:
        print(f"청크 업로드 오류: {e}")
        return None

def monitor_processing_status(upload_id, max_wait=300):
    """처리 상태 모니터링"""
    print(f"\n=== 처리 상태 모니터링 ({upload_id}) ===")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f'http://localhost:5000/api/upload/status/{upload_id}')
            result = response.json()
            
            if not result['success']:
                print(f"상태 조회 실패: {result['error']}")
                break
            
            data = result['data']
            status = data.get('status', 'unknown')
            processing = data.get('processing', {})
            
            if processing:
                progress = processing.get('progress', 0)
                message = processing.get('message', '처리 중...')
                proc_status = processing.get('status', status)
                
                print(f"[{proc_status}] {progress:.1f}% - {message}")
                
                if proc_status in ['completed', 'error']:
                    print(f"처리 완료! 최종 상태: {proc_status}")
                    if proc_status == 'completed' and processing.get('duration'):
                        print(f"처리 시간: {processing['duration']:.2f}초")
                    break
            else:
                print(f"상태: {status}")
                if status in ['done', 'error']:
                    break
            
            time.sleep(2)
            
        except Exception as e:
            print(f"상태 조회 오류: {e}")
            break
    
    else:
        print("타임아웃: 처리가 완료되지 않았습니다.")

def test_file_list():
    """파일 목록 조회 테스트"""
    print("\n=== 등록된 파일 목록 조회 ===")
    
    try:
        response = requests.get('http://localhost:5000/api/ingredients/list')
        result = response.json()
        
        if result['success']:
            files = result['files']
            print(f"등록된 파일 수: {len(files)}개")
            
            for i, file_info in enumerate(files[:5], 1):  # 상위 5개만 표시
                print(f"{i}. {file_info['sample_name']} ({file_info['supplier']})")
                print(f"   식자재 수: {file_info['ingredient_count']:,}개")
                print(f"   업로드 일시: {file_info['upload_date']}")
                print()
        else:
            print(f"파일 목록 조회 실패: {result['error']}")
            
    except Exception as e:
        print(f"파일 목록 조회 오류: {e}")

def main():
    """메인 테스트 함수"""
    print("Enhanced File Upload System 테스트 시작")
    print("=" * 50)
    
    # 1. 테스트 파일 생성
    test_file = create_test_excel_file()
    
    # 2. 파일 유효성 검사 테스트
    test_file_validation()
    
    # 3. 청크 업로드 테스트
    upload_id = test_chunked_upload(test_file)
    
    if upload_id:
        # 4. 처리 상태 모니터링
        monitor_processing_status(upload_id)
        
        # 5. 파일 목록 조회
        test_file_list()
    
    print("\n테스트 완료!")

if __name__ == '__main__':
    main()