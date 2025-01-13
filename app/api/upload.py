from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from ..utils.logger import log_api_call, logger
from ..utils.error_codes import *
import traceback
import os
from datetime import datetime
import hashlib

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename, allowed_extensions):
    """检查文件类型是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_filename(file, prefix=''):
    """生成安全的文件名"""
    # 获取文件内容的hash值
    content_hash = hashlib.md5(file.read()).hexdigest()
    file.seek(0)  # 重置文件指针
    
    # 获取原始文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}_{timestamp}_{content_hash[:8]}{ext}"

@upload_bp.route('/upload/image', methods=['POST'])
@jwt_required()
@log_api_call
def upload_image():
    """上传图片
    
    请求参数:
    - file: 图片文件
    - type: 图片类型(avatar/feedback)
    
    返回数据:
    {
        "status": "success",
        "data": {
            "url": "/static/uploads/images/avatar/xxx.jpg"
        }
    }
    """
    try:
        # 验证文件
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'file')
            }), 400
            
        file = request.files['file']
        if not file:
            return jsonify({
                'status': 'error',
                'code': INVALID_FILE,
                'message': get_error_message(INVALID_FILE)
            }), 400
            
        # 验证图片类型
        image_type = request.form.get('type', 'other')
        allowed_types = {'avatar', 'feedback', 'other'}
        if image_type not in allowed_types:
            return jsonify({
                'status': 'error',
                'code': INVALID_PARAM_VALUE,
                'message': get_error_message(INVALID_PARAM_VALUE, 'type')
            }), 400
            
        # 验证文件类型
        if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            return jsonify({
                'status': 'error',
                'code': INVALID_FILE_TYPE,
                'message': get_error_message(INVALID_FILE_TYPE)
            }), 400
            
        # 生成安全的文件名
        filename = generate_filename(file, prefix=image_type)
        
        # 确保上传目录存在
        upload_dir = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            'images',
            image_type
        )
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_dir, filename)
        try:
            file.save(file_path)
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'code': INTERNAL_ERROR,
                'message': get_error_message(INTERNAL_ERROR)
            }), 500
            
        # 生成访问URL
        file_url = f"/static/uploads/images/{image_type}/{filename}"
        
        return jsonify({
            'status': 'success',
            'data': {
                'url': file_url
            }
        })
        
    except Exception as e:
        logger.error(f"上传图片失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 