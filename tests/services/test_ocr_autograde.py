import os
import pytest
from app.services.ocr_autograde import auto_grade_image

@pytest.mark.skipif(
    not os.path.exists("tests/data/test_ocr.jpg"),
    reason="测试图片不存在"
)
def test_auto_grade_image_basic(tmp_path):
    # 1. 使用真实拍照图片
    image_path = "tests/data/test_ocr.jpg"
    answers = [
        "奇观", "据说", "宽阔", "人声鼎沸", "昂首", "滚动", "逐渐", "横贯", "犹如", "齐头并进"
    ]
    output_path = tmp_path / "marked.jpg"

    # 2. 调用批改函数
    result = auto_grade_image(str(image_path), answers, str(output_path))

    # 3. 断言返回结构
    assert "marked_image_path" in result
    assert "results" in result
    assert os.path.exists(result["marked_image_path"])
    assert isinstance(result["results"], list)
    assert len(result["results"]) == len(answers)

    # 4. 检查对错判定
    for idx, res in enumerate(result["results"]):
        assert "text" in res
        assert "correct" in res
        assert "box" in res
        assert "std" in res
        # 你可以根据实际图片内容进一步断言对错

    # 5. 清理
    os.remove(result["marked_image_path"]) 