from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

from ...models.family import Family, UserFamilyRelation
from ...models.user import User
from ...utils.error_codes import INVALID_WX_CODE, MISSING_REQUIRED_PARAM, INTERNAL_ERROR, USER_NOT_FOUND, get_error_message
import traceback
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from ...extensions import db
from ...utils.logger import logger
from ...utils.decorators import log_api_call
from ...utils.wx_service import get_openid
from . import auth_bp
import logging
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

@auth_bp.route('/auth/login', methods=['POST'])
@log_api_call
def login():
    """微信小程序登录"""
    try:
        data = request.get_json()
        logger.info(f"Login request data: {data}")
        code = data.get('code')
        logger.info(f"Login code: {code}")
        
        if not code:
            logger.warning("Missing code parameter")
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM)
            }), 400
            
        # 测试模式
        if code.startswith('test_code'):
            test_user_num = code.split('_')[-1] if '_' in code else '1'
            openid = f'test_openid_{test_user_num}'            
        else:
            openid = get_openid(code)
            if not openid:
                return jsonify({
                    'status': 'error',
                    'code': INVALID_WX_CODE,
                    'message': get_error_message(INVALID_WX_CODE)
                }), 400

        # 获取或创建用户
        try:
            user = User.query.filter_by(openid=openid).first()
            if not user:
                try:
                    user = User(openid=openid)
                    db.session.add(user)
                    db.session.commit()
                except IntegrityError:
                    # 如果发生冲突，再次尝试获取用户
                    db.session.rollback()
                    user = User.query.filter_by(openid=openid).first()
                    if not user:
                        raise
        except Exception as e:
            logger.error(f"Error creating/getting user: {str(e)}")
            return jsonify({
                'status': 'error',
                'code': INTERNAL_ERROR,
                'message': get_error_message(INTERNAL_ERROR)
            }), 500

        # 生成 token
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'status': 'success',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
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
    """刷新访问令牌"""
    try:
        # 开启事务
        db.session.begin_nested()
        user_id = get_jwt_identity()
        
        try:
            # 获取用户信息
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'status': 'error',
                    'code': USER_NOT_FOUND,
                    'message': get_error_message(USER_NOT_FOUND)
                }), 404
            
            # 获取用户的家庭关系
            relation = UserFamilyRelation.query.filter_by(
                user_id=user_id
            ).first()
            
            # 创建新的访问令牌
            access_token = create_access_token(
                identity=user_id,
                additional_claims={
                    'family_id': relation.family_id if relation else None,
                    'is_admin': relation.is_admin if relation else False
                }
            )
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'access_token': access_token
                }
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
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
        # 开启事务
        db.session.begin_nested()
        user_id = get_jwt_identity()
        
        try:
            # TODO: 实现令牌黑名单
            # 将来可能需要:
            # 1. 记录登出时间
            # 2. 将token加入黑名单
            # 3. 清除用户session
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': '退出成功'
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"退出登录失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 

@auth_bp.route('/auth/user/update', methods=['POST'])
@jwt_required()
@log_api_call
def update_user_info():
    """更新用户信息"""
    try:
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        user_id = get_jwt_identity()
        
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'status': 'error',
                    'code': USER_NOT_FOUND,
                    'message': get_error_message(USER_NOT_FOUND)
                }), 404
            
            # 更新用户信息
            if 'nickname' in data:
                user.nickname = data['nickname']
            if 'avatar_url' in data:
                user.avatar_url = data['avatar_url']
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'user': user.to_dict()
                }
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 

@auth_bp.route('/auth/test', methods=['GET'])
@jwt_required()
def test_auth():
    current_user_id = get_jwt_identity()
    return jsonify({
        'status': 'success',
        'message': 'Token is valid',
        'user_id': current_user_id
    }) 