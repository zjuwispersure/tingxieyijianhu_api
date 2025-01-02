from flask import Blueprint, request, jsonify, current_app
from ..models import User
from ..utils.wx_service import WXService
from ..utils.logger import log_message
from ..models.database import db
import traceback
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """微信登录接口"""
    data = request.get_json()
    code = data.get('code')
    
    # 记录登录请求
    log_message({
        "event": "login_attempt",
        "code": code
    })
    
    if not code:
        log_message({
            "event": "login_error",
            "error": "Missing code parameter"
        })
        return jsonify({'error': 'Missing code parameter'}), 400
    
    try:
        # 初始化微信服务
        wx_service = WXService(
            app_id=current_app.config['WX_APP_ID'],
            app_secret=current_app.config['WX_APP_SECRET']
        )
        
        # 获取openid
        openid = wx_service.get_openid(code, use_fallback=True)
        is_temp_user = openid.startswith('temp_')
        
        if is_temp_user:
            log_message({
                "event": "using_temp_id",
                "temp_id": openid,
                "code": code,
                "reason": "Failed to get real openid"
            })
        
        # 查找或创建用户
        user = User.query.filter_by(openid=openid).first()
        if not user:
            user = User(openid=openid)
            db.session.add(user)
            db.session.commit()
            
            log_message({
                "event": "new_user_created",
                "openid": openid,
                "is_temp": is_temp_user,
                "user_id": user.id
            })
        else:
            log_message({
                "event": "user_login",
                "user_id": user.id,
                "openid": openid,
                "is_temp": is_temp_user
            })
        
        # 生成token
        token = user.generate_token()
        
        log_message({
            "event": "login_success",
            "user_id": user.id,
            "is_temp": is_temp_user
        })
        
        return jsonify({
            'code': 0,
            'data': {
                'access_token': token,
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        log_message({
            "event": "login_error",
            "error": str(e),
            "code": code,
            "error_type": type(e).__name__,
            "stack_trace": getattr(e, '__traceback__', None) and 
                          ''.join(traceback.format_tb(e.__traceback__))
        })
        return jsonify({'error': 'Login failed'}), 500 