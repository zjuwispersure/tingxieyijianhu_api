import os
from typing import List, Dict, Any
import cv2
import numpy as np
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='ch')

def auto_grade_image(image_path: str, answers: List[str], output_path: str = None) -> Dict[str, Any]:
    """
    自动批改听写图片：识别、比对、标记错误（支持词语/单字）
    Args:
        image_path: 图片路径
        answers: 标准答案列表（词语/单字，顺序）
        output_path: 标记后图片保存路径（可选）
    Returns:
        dict: {
            'marked_image_path': str,
            'results': List[{'text': str, 'correct': bool, 'boxes': list, 'std': str}]
        }
    """
    # 1. OCR识别
    result = ocr.ocr(image_path, cls=True)
    if not result or not result[0]:
        return {'marked_image_path': None, 'results': []}

    # 2. 取识别内容和坐标（单字序列）
    ocr_items = []
    for line in result[0]:
        box = line[0]  # 4点坐标
        text = line[1][0].strip()
        # 拆分为单字
        for i, char in enumerate(text):
            # 计算单字box（如果是单字，直接用box；多字时简单均分box横坐标）
            if len(text) == 1:
                char_box = box
            else:
                # 横向均分box
                x0, y0 = box[0]
                x1, y1 = box[1]
                x2, y2 = box[2]
                x3, y3 = box[3]
                n = len(text)
                # 仅支持横排，近似分割
                left = int(x0 + (x1 - x0) * i / n)
                right = int(x0 + (x1 - x0) * (i + 1) / n)
                char_box = [
                    [left, y0],
                    [right, y1],
                    [right, y2],
                    [left, y3]
                ]
            ocr_items.append({'text': char, 'box': char_box})

    # 3. 按标准答案词语长度拼接
    idx = 0
    grouped = []
    for std in answers:
        chars = []
        boxes = []
        for _ in std:
            if idx < len(ocr_items):
                chars.append(ocr_items[idx]['text'])
                boxes.append(ocr_items[idx]['box'])
                idx += 1
        grouped.append({'text': ''.join(chars), 'boxes': boxes, 'std': std})

    # 4. 比对与结果
    results = []
    for item in grouped:
        correct = (item['text'] == item['std'])
        results.append({
            'text': item['text'],
            'correct': correct,
            'boxes': item['boxes'],
            'std': item['std']
        })

    # 5. 标记错误
    img = cv2.imread(image_path)
    for res in results:
        if not res['correct']:
            for box in res['boxes']:
                pts = np.array(box, np.int32).reshape((-1, 1, 2))
                cv2.polylines(img, [pts], True, (0, 0, 255), 2)

    # 6. 保存/返回图片
    if not output_path:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_marked{ext}"
    cv2.imwrite(output_path, img)

    return {
        'marked_image_path': output_path,
        'results': results
    } 