"""
Enhanced File Upload System
대용량 엑셀 파일을 위한 개선된 업로드 시스템
- 청크 업로드 지원
- 백그라운드 처리
- 실시간 진행률 추적
- 강력한 유효성 검사
"""

import os
import uuid
import time
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, session
import sqlite3

class FileUploadProcessor:
    """파일 업로드 처리기"""
    
    def __init__(self, upload_dir: str = "uploads", chunk_size: int = 1024*1024*2):  # 2MB chunks
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.chunk_size = chunk_size
        self.processing_status = {}  # 처리 상태 추적
        self.active_uploads = {}     # 활성 업로드 추적
        
        # 임시 파일 디렉토리
        self.temp_dir = self.upload_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 완료된 파일 디렉토리
        self.completed_dir = self.upload_dir / "completed"
        self.completed_dir.mkdir(exist_ok=True)
        
    def validate_file(self, filename: str, file_size: int) -> Dict:
        """파일 유효성 검사"""
        errors = []
        
        # 파일 확장자 검사
        allowed_extensions = {'.xlsx', '.xls'}
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            errors.append(f"지원하지 않는 파일 형식: {file_ext}")
        
        # 파일 크기 검사 (100MB 제한)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            errors.append(f"파일 크기가 너무 큼: {file_size/1024/1024:.1f}MB (최대 100MB)")
        
        # 파일명 검사
        if len(filename) > 255:
            errors.append("파일명이 너무 김")
        
        # 안전한 파일명인지 검사
        safe_filename = secure_filename(filename)
        if not safe_filename:
            errors.append("유효하지 않은 파일명")
            
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'safe_filename': safe_filename
        }
    
    def start_chunked_upload(self, filename: str, file_size: int, total_chunks: int) -> Dict:
        """청크 업로드 시작"""
        validation = self.validate_file(filename, file_size)
        if not validation['valid']:
            return {
                'success': False,
                'errors': validation['errors']
            }
        
        upload_id = str(uuid.uuid4())
        safe_filename = validation['safe_filename']
        
        # 업로드 세션 생성
        upload_info = {
            'upload_id': upload_id,
            'filename': filename,
            'safe_filename': safe_filename,
            'file_size': file_size,
            'total_chunks': total_chunks,
            'received_chunks': 0,
            'status': 'uploading',
            'created_at': datetime.now().isoformat(),
            'temp_path': str(self.temp_dir / f"{upload_id}_{safe_filename}"),
            'chunks_received': set()
        }
        
        self.active_uploads[upload_id] = upload_info
        
        return {
            'success': True,
            'upload_id': upload_id,
            'chunk_size': self.chunk_size
        }
    
    def receive_chunk(self, upload_id: str, chunk_index: int, chunk_data: bytes) -> Dict:
        """청크 데이터 수신"""
        if upload_id not in self.active_uploads:
            return {'success': False, 'error': '유효하지 않은 업로드 ID'}
        
        upload_info = self.active_uploads[upload_id]
        
        # 중복 청크 체크
        if chunk_index in upload_info['chunks_received']:
            return {'success': True, 'message': '이미 수신된 청크'}
        
        try:
            # 임시 파일에 청크 쓰기
            temp_path = Path(upload_info['temp_path'])
            
            # 파일이 없으면 생성
            if not temp_path.exists():
                temp_path.touch()
            
            # 청크를 올바른 위치에 쓰기
            with open(temp_path, 'r+b') as f:
                f.seek(chunk_index * self.chunk_size)
                f.write(chunk_data)
            
            # 수신된 청크 추가
            upload_info['chunks_received'].add(chunk_index)
            upload_info['received_chunks'] = len(upload_info['chunks_received'])
            
            # 진행률 계산
            progress = (upload_info['received_chunks'] / upload_info['total_chunks']) * 100
            
            return {
                'success': True,
                'progress': round(progress, 1),
                'received_chunks': upload_info['received_chunks'],
                'total_chunks': upload_info['total_chunks']
            }
            
        except Exception as e:
            return {'success': False, 'error': f'청크 쓰기 오류: {str(e)}'}
    
    def complete_upload(self, upload_id: str) -> Dict:
        """업로드 완료 처리"""
        if upload_id not in self.active_uploads:
            return {'success': False, 'error': '유효하지 않은 업로드 ID'}
        
        upload_info = self.active_uploads[upload_id]
        
        # 모든 청크가 수신되었는지 확인
        if upload_info['received_chunks'] != upload_info['total_chunks']:
            return {
                'success': False, 
                'error': f'청크 누락: {upload_info["received_chunks"]}/{upload_info["total_chunks"]}'
            }
        
        try:
            temp_path = Path(upload_info['temp_path'])
            final_path = self.completed_dir / upload_info['safe_filename']
            
            # 임시 파일을 완료 디렉토리로 이동
            temp_path.rename(final_path)
            
            # 파일 정보 업데이트
            upload_info['status'] = 'completed'
            upload_info['completed_at'] = datetime.now().isoformat()
            upload_info['final_path'] = str(final_path)
            
            # 백그라운드에서 엑셀 처리 시작
            processing_thread = threading.Thread(
                target=self._process_excel_file,
                args=(upload_id, final_path)
            )
            processing_thread.daemon = True
            processing_thread.start()
            
            return {
                'success': True,
                'message': '업로드 완료. 파일 처리를 시작합니다.',
                'file_path': str(final_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'업로드 완료 처리 오류: {str(e)}'}
    
    def _process_excel_file(self, upload_id: str, file_path: Path):
        """엑셀 파일 백그라운드 처리"""
        try:
            upload_info = self.active_uploads[upload_id]
            upload_info['status'] = 'processing'
            
            # 처리 상태 초기화
            self.processing_status[upload_id] = {
                'status': 'reading_file',
                'progress': 0,
                'message': '파일을 읽는 중...',
                'start_time': time.time()
            }
            
            # 엑셀 파일 읽기
            try:
                df = pd.read_excel(file_path)
                self.processing_status[upload_id]['progress'] = 20
                self.processing_status[upload_id]['message'] = f'{len(df):,}개 행 발견. 데이터 검증 중...'
                
            except Exception as e:
                self.processing_status[upload_id]['status'] = 'error'
                self.processing_status[upload_id]['error'] = f'파일 읽기 오류: {str(e)}'
                return
            
            # 데이터 유효성 검사
            validation_result = self._validate_excel_data(df)
            if not validation_result['valid']:
                self.processing_status[upload_id]['status'] = 'error'
                self.processing_status[upload_id]['error'] = f'데이터 유효성 검사 실패: {validation_result["errors"]}'
                return
            
            self.processing_status[upload_id]['progress'] = 40
            self.processing_status[upload_id]['message'] = '데이터베이스에 저장 중...'
            
            # 데이터베이스 저장 (배치 처리)
            saved_count = self._save_to_database(df, upload_id)
            
            # 처리 완료
            upload_info['status'] = 'done'
            upload_info['processed_items'] = saved_count
            
            self.processing_status[upload_id] = {
                'status': 'completed',
                'progress': 100,
                'message': f'{saved_count:,}개 식자재가 성공적으로 등록되었습니다.',
                'end_time': time.time(),
                'duration': time.time() - self.processing_status[upload_id]['start_time']
            }
            
        except Exception as e:
            self.processing_status[upload_id]['status'] = 'error'
            self.processing_status[upload_id]['error'] = f'처리 중 오류: {str(e)}'
            upload_info['status'] = 'error'
    
    def _validate_excel_data(self, df: pd.DataFrame) -> Dict:
        """엑셀 데이터 유효성 검사"""
        errors = []
        
        # 필수 컬럼 체크
        required_columns = ['식자재명', '단가', '단위']  # 기본 필수 컬럼
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f'필수 컬럼 누락: {", ".join(missing_columns)}')
        
        # 데이터 행 수 체크
        if len(df) == 0:
            errors.append('데이터가 없습니다')
        elif len(df) > 100000:  # 10만개 제한
            errors.append(f'데이터가 너무 많습니다: {len(df):,}개 (최대 100,000개)')
        
        # 데이터 타입 체크 (샘플)
        if '단가' in df.columns:
            invalid_prices = df[df['단가'].notna()]['단가'].apply(
                lambda x: not isinstance(x, (int, float)) or x < 0
            ).sum()
            if invalid_prices > 0:
                errors.append(f'잘못된 단가 데이터 {invalid_prices}개 발견')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _save_to_database(self, df: pd.DataFrame, upload_id: str) -> int:
        """데이터베이스에 배치 저장"""
        try:
            # SQLite 연결
            conn = sqlite3.connect('meal_management.db')
            cursor = conn.cursor()
            
            # ingredients 테이블이 없으면 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    unit TEXT,
                    price REAL,
                    supplier TEXT,
                    upload_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            saved_count = 0
            batch_size = 1000  # 배치 크기
            
            # 데이터를 배치로 나누어 저장
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                # 배치 데이터 준비
                batch_data = []
                for _, row in batch_df.iterrows():
                    if pd.notna(row.get('식자재명', '')):  # 식자재명이 있는 경우만
                        batch_data.append((
                            str(row.get('식자재명', '')),
                            str(row.get('분류', '') if pd.notna(row.get('분류', '')) else '기타'),
                            str(row.get('단위', '') if pd.notna(row.get('단위', '')) else '개'),
                            float(row.get('단가', 0) if pd.notna(row.get('단가', 0)) else 0),
                            str(row.get('공급업체', '') if pd.notna(row.get('공급업체', '')) else '미지정'),
                            upload_id
                        ))
                
                # 배치 인서트
                if batch_data:
                    cursor.executemany('''
                        INSERT INTO ingredients (name, category, unit, price, supplier, upload_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', batch_data)
                    saved_count += len(batch_data)
                
                # 진행률 업데이트
                progress = 40 + (i / len(df)) * 60  # 40%에서 100%까지
                self.processing_status[upload_id]['progress'] = int(progress)
                self.processing_status[upload_id]['message'] = f'저장 중... ({saved_count:,}/{len(df):,})'
            
            conn.commit()
            conn.close()
            
            return saved_count
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            raise e
    
    def get_upload_status(self, upload_id: str) -> Dict:
        """업로드 상태 조회"""
        if upload_id not in self.active_uploads:
            return {'success': False, 'error': '유효하지 않은 업로드 ID'}
        
        upload_info = self.active_uploads[upload_id].copy()
        
        # set 객체를 list로 변환 (JSON 직렬화 가능하도록)
        if 'chunks_received' in upload_info:
            upload_info['chunks_received_list'] = list(upload_info['chunks_received'])
            del upload_info['chunks_received']  # set 객체 제거
        
        # 처리 상태 추가
        if upload_id in self.processing_status:
            upload_info['processing'] = self.processing_status[upload_id]
        
        return {'success': True, 'data': upload_info}
    
    def cleanup_old_uploads(self, max_age_hours: int = 24):
        """오래된 업로드 세션 정리"""
        current_time = datetime.now()
        to_remove = []
        
        for upload_id, upload_info in self.active_uploads.items():
            created_at = datetime.fromisoformat(upload_info['created_at'])
            age_hours = (current_time - created_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                to_remove.append(upload_id)
                
                # 임시 파일 삭제
                temp_path = Path(upload_info['temp_path'])
                if temp_path.exists():
                    temp_path.unlink()
        
        # 세션 제거
        for upload_id in to_remove:
            del self.active_uploads[upload_id]
            if upload_id in self.processing_status:
                del self.processing_status[upload_id]
        
        return len(to_remove)

# 전역 프로세서 인스턴스
file_processor = FileUploadProcessor()