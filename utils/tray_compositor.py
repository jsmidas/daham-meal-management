"""
급식 식판 이미지 합성 유틸리티
- 식판 템플릿에 메뉴 이미지 합성
- 각 칸에 맞게 자동 크기 조정
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

class TrayCompositor:
    def __init__(self):
        """식판 합성기 초기화"""
        self.tray_template = "static/templates/tray_template.png"  # 빈 식판 이미지

        # 식판 각 칸의 좌표 (밥, 국, 메인반찬, 부반찬1, 부반찬2, 김치)
        self.compartments = {
            'rice': {'x': 50, 'y': 50, 'width': 200, 'height': 200},      # 밥
            'soup': {'x': 270, 'y': 50, 'width': 200, 'height': 200},     # 국
            'main': {'x': 50, 'y': 270, 'width': 200, 'height': 150},     # 메인반찬
            'side1': {'x': 270, 'y': 270, 'width': 100, 'height': 150},   # 부반찬1
            'side2': {'x': 380, 'y': 270, 'width': 100, 'height': 150},   # 부반찬2
            'kimchi': {'x': 490, 'y': 50, 'width': 100, 'height': 100}    # 김치
        }

    def load_tray_template(self):
        """식판 템플릿 로드"""
        if os.path.exists(self.tray_template):
            return Image.open(self.tray_template)
        else:
            # 템플릿이 없으면 기본 하얀 식판 생성
            tray = Image.new('RGB', (600, 450), 'white')
            draw = ImageDraw.Draw(tray)

            # 각 칸 그리기
            for name, comp in self.compartments.items():
                draw.rectangle(
                    [comp['x'], comp['y'],
                     comp['x'] + comp['width'],
                     comp['y'] + comp['height']],
                    outline='#dddddd',
                    width=2
                )

            return tray

    def fit_image_to_compartment(self, image_path, compartment):
        """이미지를 식판 칸에 맞게 조정"""
        if not os.path.exists(image_path):
            return None

        img = Image.open(image_path)

        # RGBA 변환
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 칸 크기에 맞게 리사이징 (비율 유지)
        comp = self.compartments[compartment]
        img.thumbnail((comp['width'], comp['height']), Image.Resampling.LANCZOS)

        # 중앙 정렬을 위한 패딩 계산
        x_offset = (comp['width'] - img.width) // 2
        y_offset = (comp['height'] - img.height) // 2

        return img, (comp['x'] + x_offset, comp['y'] + y_offset)

    def create_meal_tray(self, menu_data):
        """
        식판 이미지 생성

        Args:
            menu_data: {
                'rice': {'name': '흰쌀밥', 'image': 'path/to/rice.jpg'},
                'soup': {'name': '김치찌개', 'image': 'path/to/soup.jpg'},
                'main': {'name': '제육볶음', 'image': 'path/to/main.jpg'},
                'side1': {'name': '시금치나물', 'image': 'path/to/side1.jpg'},
                'side2': {'name': '멸치볶음', 'image': 'path/to/side2.jpg'},
                'kimchi': {'name': '배추김치', 'image': 'path/to/kimchi.jpg'}
            }

        Returns:
            합성된 식판 이미지
        """
        # 식판 템플릿 로드
        tray = self.load_tray_template()

        # 각 메뉴 이미지 합성
        for position, menu_info in menu_data.items():
            if menu_info and 'image' in menu_info and menu_info['image']:
                result = self.fit_image_to_compartment(menu_info['image'], position)

                if result:
                    img, (x, y) = result

                    # 음식 이미지를 원형으로 마스킹 (선택사항)
                    # mask = self.create_circular_mask(img.size)
                    # img.putalpha(mask)

                    # 식판에 합성
                    tray.paste(img, (x, y), img if img.mode == 'RGBA' else None)

                    # 메뉴명 추가 (선택사항)
                    if 'name' in menu_info:
                        self.add_text(tray, menu_info['name'], position)

        return tray

    def create_circular_mask(self, size):
        """원형 마스크 생성 (음식이 더 자연스럽게 보이도록)"""
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        return mask

    def add_text(self, image, text, position):
        """메뉴명 텍스트 추가"""
        draw = ImageDraw.Draw(image)
        comp = self.compartments[position]

        # 폰트 설정 (한글 폰트 필요)
        try:
            font = ImageFont.truetype("malgun.ttf", 12)
        except:
            font = ImageFont.load_default()

        # 텍스트 위치 (칸 하단)
        text_x = comp['x'] + comp['width'] // 2
        text_y = comp['y'] + comp['height'] - 20

        # 텍스트 그리기 (중앙 정렬)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((text_x - text_width // 2, text_y), text, fill='black', font=font)

    def save_tray_image(self, tray_image, output_path):
        """식판 이미지 저장"""
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # JPEG로 저장 (배경 흰색)
        if tray_image.mode == 'RGBA':
            background = Image.new('RGB', tray_image.size, (255, 255, 255))
            background.paste(tray_image, mask=tray_image.split()[3])
            tray_image = background

        tray_image.save(output_path, 'JPEG', quality=95, optimize=True)
        return output_path

# 사용 예시
if __name__ == "__main__":
    compositor = TrayCompositor()

    # 메뉴 데이터 예시
    menu_data = {
        'rice': {'name': '흰쌀밥', 'image': 'static/uploads/recipes/compressed/rice.jpg'},
        'soup': {'name': '김치찌개', 'image': 'static/uploads/recipes/compressed/kimchi_stew.jpg'},
        'main': {'name': '제육볶음', 'image': 'static/uploads/recipes/compressed/pork.jpg'},
        'side1': {'name': '시금치나물', 'image': 'static/uploads/recipes/compressed/spinach.jpg'},
        'side2': {'name': '멸치볶음', 'image': 'static/uploads/recipes/compressed/anchovy.jpg'},
        'kimchi': {'name': '배추김치', 'image': 'static/uploads/recipes/compressed/kimchi.jpg'}
    }

    # 식판 이미지 생성
    tray_image = compositor.create_meal_tray(menu_data)

    # 저장
    output_path = compositor.save_tray_image(
        tray_image,
        'static/uploads/trays/today_meal.jpg'
    )

    print(f"식판 이미지 생성 완료: {output_path}")