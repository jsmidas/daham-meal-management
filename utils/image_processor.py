"""
이미지 처리 유틸리티
- 이미지 압축
- 썸네일 생성
- 파일 크기 최적화
"""

import os
import hashlib
from PIL import Image
from pathlib import Path
from datetime import datetime
import io

class ImageProcessor:
    def __init__(self, upload_dir="static/uploads/recipes"):
        """
        이미지 처리기 초기화

        Args:
            upload_dir: 업로드 디렉토리 경로
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # 하위 디렉토리 생성
        self.original_dir = self.upload_dir / "original"
        self.compressed_dir = self.upload_dir / "compressed"
        self.thumbnail_dir = self.upload_dir / "thumbnail"

        for dir_path in [self.original_dir, self.compressed_dir, self.thumbnail_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 설정값
        self.max_size = (1200, 1200)  # 최대 크기 (압축용)
        self.thumbnail_size = (300, 300)  # 썸네일 크기
        self.quality = 85  # JPEG 품질 (1-100)
        self.max_file_size_kb = 500  # 최대 파일 크기 (KB)

    def generate_filename(self, original_filename):
        """
        고유한 파일명 생성

        Args:
            original_filename: 원본 파일명

        Returns:
            생성된 파일명
        """
        ext = Path(original_filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(f"{original_filename}{timestamp}".encode()).hexdigest()[:8]
        return f"recipe_{timestamp}_{random_hash}{ext}"

    def compress_image(self, image, max_size=None, quality=None):
        """
        이미지 압축

        Args:
            image: PIL Image 객체
            max_size: 최대 크기 튜플 (width, height)
            quality: JPEG 품질

        Returns:
            압축된 Image 객체
        """
        if max_size is None:
            max_size = self.max_size
        if quality is None:
            quality = self.quality

        # RGBA를 RGB로 변환 (JPEG는 투명도 지원 안함)
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image

        # 이미지 리사이징 (비율 유지)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 품질 조정하여 파일 크기 제어
        output = io.BytesIO()
        current_quality = quality

        while current_quality > 10:
            output.seek(0)
            output.truncate()
            image.save(output, format='JPEG', quality=current_quality, optimize=True)

            # 파일 크기 확인
            size_kb = output.tell() / 1024
            if size_kb <= self.max_file_size_kb:
                break

            # 품질 감소
            current_quality -= 5

        output.seek(0)
        return Image.open(output), output.getvalue()

    def create_thumbnail(self, image):
        """
        썸네일 생성

        Args:
            image: PIL Image 객체

        Returns:
            썸네일 Image 객체
        """
        thumbnail = image.copy()

        # RGBA를 RGB로 변환
        if thumbnail.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', thumbnail.size, (255, 255, 255))
            if thumbnail.mode == 'P':
                thumbnail = thumbnail.convert('RGBA')
            rgb_image.paste(thumbnail, mask=thumbnail.split()[-1] if thumbnail.mode in ('RGBA', 'LA') else None)
            thumbnail = rgb_image

        # 정사각형으로 크롭 (중앙 기준)
        width, height = thumbnail.size
        min_dimension = min(width, height)

        left = (width - min_dimension) // 2
        top = (height - min_dimension) // 2
        right = left + min_dimension
        bottom = top + min_dimension

        thumbnail = thumbnail.crop((left, top, right, bottom))
        thumbnail.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

        return thumbnail

    def process_upload(self, file_data, original_filename):
        """
        업로드된 이미지 처리

        Args:
            file_data: 이미지 파일 데이터 (bytes)
            original_filename: 원본 파일명

        Returns:
            처리 결과 딕셔너리
        """
        try:
            # 파일명 생성
            new_filename = self.generate_filename(original_filename)
            name_without_ext = Path(new_filename).stem

            # 이미지 열기
            image = Image.open(io.BytesIO(file_data))
            original_width, original_height = image.size

            # 원본 저장
            original_path = self.original_dir / new_filename
            with open(original_path, 'wb') as f:
                f.write(file_data)

            # 압축 이미지 생성
            compressed_image, compressed_data = self.compress_image(image)
            compressed_filename = f"{name_without_ext}_compressed.jpg"
            compressed_path = self.compressed_dir / compressed_filename
            with open(compressed_path, 'wb') as f:
                f.write(compressed_data)

            # 썸네일 생성
            thumbnail = self.create_thumbnail(image)
            thumbnail_filename = f"{name_without_ext}_thumb.jpg"
            thumbnail_path = self.thumbnail_dir / thumbnail_filename
            thumbnail.save(thumbnail_path, 'JPEG', quality=90, optimize=True)

            # 결과 반환
            return {
                'success': True,
                'original': {
                    'path': str(original_path).replace('\\', '/'),
                    'size': len(file_data),
                    'width': original_width,
                    'height': original_height
                },
                'compressed': {
                    'path': str(compressed_path).replace('\\', '/'),
                    'size': len(compressed_data),
                    'width': compressed_image.width,
                    'height': compressed_image.height
                },
                'thumbnail': {
                    'path': str(thumbnail_path).replace('\\', '/'),
                    'width': thumbnail.width,
                    'height': thumbnail.height
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup_old_files(self, days=30):
        """
        오래된 파일 정리

        Args:
            days: 보관 기간 (일)
        """
        import time
        current_time = time.time()

        for dir_path in [self.original_dir, self.compressed_dir, self.thumbnail_dir]:
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > (days * 86400):  # 86400 = 24 * 60 * 60
                        file_path.unlink()
                        print(f"삭제됨: {file_path}")

# 사용 예시
if __name__ == "__main__":
    processor = ImageProcessor()

    # 테스트용 이미지 처리
    with open("test_image.jpg", "rb") as f:
        result = processor.process_upload(f.read(), "test_image.jpg")
        print(result)