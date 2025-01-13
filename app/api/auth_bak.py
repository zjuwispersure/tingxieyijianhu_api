from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from ..utils.wx_service import get_openid
from ..models import User
from ..extensions import db
from ..utils.logger import log_api_call
from ..utils.error_codes import *
import traceback
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from ..models.family import Family, UserFamilyRelation

from app.utils import logger

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
@log_api_call
def login():
    """微信小程序登录
    
    请求参数:
    {
        "code": "wx_code"
    }
    
    返回数据:
    {
        "status": "success",
        "data": {
            "access_token": "xxx",
            "refresh_token": "xxx",
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'code')
            }), 400
            
        code = data['code']
        
        # 测试模式
        if code.startswith('test_code'):
            # 从 test_code_1, test_code_2 等提取用户编号
            test_user_num = code.split('_')[-1] if '_' in code else '1'
            test_openid = f'test_openid_{test_user_num}'
            openid = test_openid            
        else:
            # 获取openid
            openid = get_openid(code)
            if not openid:
                return jsonify({
                    'status': 'error',
                    'code': INVALID_WX_CODE,
                    'message': get_error_message(INVALID_WX_CODE)
                }), 400
                
        # 获取或创建用户
        user = User.query.filter_by(openid=openid).first()
        if not user:
            # 创建新用户
            user = User(openid=test_openid)
            db.session.add(user)
            db.session.commit()
            
        # 检查用户是否已有家庭关系
        relation = UserFamilyRelation.query.filter_by(user_id=user.id).first()
        if not relation:
            # 检查是否已有同名家庭
            family_name = f"{user.nickname or '我'}的家庭"
            family = Family.query.filter_by(name=family_name, created_by=user.id).first()
                
            if not family:
                # 创建新家庭
                family = Family(
                    name=family_name,
                    created_by=user.id
                )
                db.session.add(family)
                db.session.commit()
                
            # 创建用户-家庭关系
            relation = UserFamilyRelation(
                user_id=user.id,
                family_id=family.id,
                role='parent'  # 创建者为家长角色
            )
            db.session.add(relation)
            db.session.commit()

        # 获取用户的第一个家庭ID（如果有）
        family_relation = UserFamilyRelation.query.filter_by(user_id=user.id).first()
        family_id = family_relation.family_id if family_relation else None
        is_admin = user.is_admin  # 使用用户表的 is_admin 字段
        
        # 创建包含 family_id 和 is_admin 的 token
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'family_id': family_id,
                'is_admin': is_admin
            }
        )
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': {
                'access_token': access_token,
                'user_id': user.id,
                'family_id': family_id,
                'is_admin': is_admin
            }
        })
        
    except Exception as e:
        logger.error(f"登录失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@auth_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
@log_api_call
def refresh_token():
    """刷新访问令牌
    
    请求参数:
    {
        "refresh_token": "xxx"  # 必填，刷新令牌
    }
    
    返回数据:
    {
        "status": "success",
        "data": {
            "access_token": "xxx"
        }
    }
    """
    try:
        # 获取用户ID
        user_id = get_jwt_identity()
        
        # 生成新的访问令牌
        access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'access_token': access_token
            }
        })
        
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
@log_api_call
def logout():
    """退出登录
    
    返回数据:
    {
        "status": "success",
        "message": "退出成功"
    }
    """
    try:
        # TODO: 实现令牌黑名单
        return jsonify({
            'status': 'success',
            'message': '退出成功'
        })
        
    except Exception as e:
        logger.error(f"退出登录失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 