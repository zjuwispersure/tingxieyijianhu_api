from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from ..models.user import User
from ..extensions import db
import requests

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """微信授权登录"""
    code = request.json.get('code')
    if not code:
        return jsonify({'error': '缺少code参数'}), 400
        
    # 调用微信接口获取openid
    wx_api_url = f"https://api.weixin.qq.com/sns/jscode2session"
    params = {
        'appid': current_app.config['WECHAT_APP_ID'],
        'secret': current_app.config['WECHAT_APP_SECRET'],
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    
    resp = requests.get(wx_api_url, params=params)
    wx_data = resp.json()
    
    if 'openid' not in wx_data:
        return jsonify({'error': '微信授权失败'}), 401
        
    # 查找或创建用户
    user = User.query.filter_by(openid=wx_data['openid']).first()
    if not user:
        user = User(openid=wx_data['openid'])
        db.session.add(user)
        db.session.commit()
    
    # 生成JWT token
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}) 