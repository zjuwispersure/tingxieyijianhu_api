from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token, verify_jwt_in_request
from app.models.user import User
from ..models.family import Family, FamilyMember, UserFamilyRelation
from ..extensions import db
from ..models import Child, DictationConfig
from ..utils.logger import log_api_call, logger
import traceback
from ..utils.error_codes import *  # 导入错误码
from sqlalchemy.exc import OperationalError
from sqlalchemy import event
from time import sleep
from functools import wraps

family_bp = Blueprint('family', __name__)

def jwt_required_with_logger():
    """带日志的 JWT 验证装饰器"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            logger.info("Starting token verification...")
            auth_header = request.headers.get('Authorization', '')
            logger.info(f"Auth header: {auth_header}")
            try:
                # 手动验证 JWT
                verify_jwt_in_request()
                user_id = int(get_jwt_identity())
                claims = get_jwt()
                logger.info(f"Token claims: user_id={user_id}, claims={claims}")
                return fn(*args, **kwargs)
            except Exception as e:
                logger.error(f"Token verification failed: {str(e)}\n{traceback.format_exc()}")
                return jsonify({
                    'status': 'error',
                    'code': 2001,
                    'message': '请先登录'
                }), 401
        return decorator
    return wrapper

@family_bp.route('/family/create', methods=['POST'])
@jwt_required()
def create_family():
    """创建家庭群组"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'name')
            }), 400
        
        user_id = get_jwt_identity()
        
        # 创建家庭
        family = Family(
            name=data['name'],
            created_by=user_id
        )
        db.session.add(family)
        db.session.commit()
        
        # 创建用户-家庭关系，设置为管理员
        relation = UserFamilyRelation(
            user_id=user_id,
            family_id=family.id,
            role='parent',
            is_admin=True  # 创建者自动成为管理员
        )
        db.session.add(relation)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': {
                'family': family.to_dict(),
                'relation': relation.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"创建家庭失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@family_bp.route('/family/get', methods=['GET'])
@jwt_required()
def get_family():
    """获取当前用户的家庭群组信息"""
    try:
        user_id = get_jwt_identity()
        family = Family.query.filter_by(user_id=user_id).first()
        
        if not family:
            return jsonify({
                'status': 'error',
                'code': RESOURCE_NOT_FOUND,
                'message': get_error_message(RESOURCE_NOT_FOUND)
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': family.to_dict()
        })
        
    except Exception as e:
        logger.error(f"获取家庭信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@family_bp.route('/family/invite', methods=['POST'])
@jwt_required()
def invite_member():
    """邀请家庭成员"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'user_id')
            }), 400
        
        user_id = get_jwt_identity()
        family = Family.query.filter_by(user_id=user_id).first()
        
        if not family:
            return jsonify({
                'status': 'error',
                'code': RESOURCE_NOT_FOUND,
                'message': get_error_message(RESOURCE_NOT_FOUND)
            }), 404
            
        # 检查是否已是成员
        if FamilyMember.query.filter_by(
            family_id=family.id,
            user_id=data['user_id']
        ).first():
            return jsonify({
                'status': 'error',
                'code': RESOURCE_ALREADY_EXISTS,
                'message': '该用户已是家庭成员'
            }), 400
        
        member = FamilyMember(
            family_id=family.id,
            user_id=data['user_id']
        )
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': member.to_dict()
        })
        
    except Exception as e:
        logger.error(f"邀请家庭成员失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@family_bp.route('/family/members', methods=['GET'])
@jwt_required()
def get_members():
    """获取家庭成员列表"""
    try:
        user_id = get_jwt_identity()
        family = Family.query.filter_by(user_id=user_id).first()
        
        if not family:
            return jsonify({
                'status': 'error',
                'code': RESOURCE_NOT_FOUND,
                'message': get_error_message(RESOURCE_NOT_FOUND)
            }), 404
        
        members = FamilyMember.query.filter_by(family_id=family.id).all()
        return jsonify({
            'status': 'success',
            'data': [member.to_dict() for member in members]
        })
        
    except Exception as e:
        logger.error(f"获取家庭成员列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@family_bp.route('/family/member/<int:id>', methods=['DELETE'])
@jwt_required()
def remove_member(id):
    """移除家庭成员"""
    user_id = get_jwt_identity()
    family = Family.query.filter_by(user_id=user_id).first_or_404()
    
    member = FamilyMember.query.filter_by(
        family_id=family.id,
        id=id
    ).first_or_404()
    
    db.session.delete(member)
    db.session.commit()
    
    return '', 204 

@family_bp.route('/family/child/add', methods=['POST'])
@jwt_required()
def add_child():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # 获取用户下一个可用的 child_id
        max_child = Child.query.filter_by(user_id=user_id).order_by(Child.child_id.desc()).first()
        next_child_id = (max_child.child_id + 1) if max_child else 1
        
        # 创建 Child 记录
        child = Child(
            user_id=user_id,
            family_id=data['family_id'],
            child_id=next_child_id,
            nickname=data['nickname'],
            province=data.get('province'),
            city=data.get('city'),
            grade=data.get('grade'),
            semester=data.get('semester'),
            textbook_version=data.get('textbook_version')
        )
        db.session.add(child)
        
        # 同步创建 FamilyMember 记录
        member = FamilyMember(
            family_id=data['family_id'],
            name=data['nickname'],
            role='child',
            is_child=True
        )
        db.session.add(member)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': {
                'child': child.to_dict(),
                'member': member.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        # ... 错误处理

@family_bp.route('/child/get', methods=['GET'])
@log_api_call
@jwt_required()
def get_children():
    """获取当前用户的所有孩子"""
    try:
        user_id = int(get_jwt_identity())
        children = Child.query.filter_by(user_id=user_id).all()
        return jsonify({
            'status': 'success',
            'data': [{
                'id': child.id,
                'nickname': child.nickname,
                'grade': child.grade,
                'semester': child.semester,
                'province': child.province,
                'city': child.city,
                'textbook_version': child.textbook_version
            } for child in children]
        })
    except Exception as e:
        logger.error(f"获取孩子列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@family_bp.route('/child/check-nickname', methods=['GET'])
@jwt_required()
def check_nickname():
    """检查昵称是否存在（在当前用户的孩子中检查）"""
    try:
        nickname = request.args.get('nickname')
        if not nickname:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'nickname')
            }), 400
            
        user_id = int(get_jwt_identity())
        exists = Child.query.filter_by(
            user_id=user_id,
            nickname=nickname
        ).first() is not None
        
        return jsonify({
            'status': 'success',
            'data': {
                'exists': exists
            }
        })
        
    except Exception as e:
        logger.error(f"检查昵称失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500


@family_bp.route('/child/count', methods=['GET'])
@log_api_call
@jwt_required()
def get_children_count():
    """获取当前用户的孩子数量统计信息"""
    try:
        user_id = get_jwt_identity()
        
        # 获取所有孩子数量
        total_count = Child.query.filter_by(user_id=int(user_id)).count()
        
        # 获取已配置听写的孩子数量
        configured_count = Child.query.join(DictationConfig).filter(
            Child.user_id == int(user_id)
        ).count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total': total_count,
                'configured': configured_count,
                'unconfigured': total_count - configured_count
            }
        })
        
    except Exception as e:
        logger.error(f"获取孩子数量统计失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500



@family_bp.route('/child/update', methods=['POST'])
@log_api_call
@jwt_required()
def update_child():
    """更新孩子信息
    
    请求参数:
    {
        "id": 1,                    # 必填，孩子ID
        "nickname": "小明",         # 选填，昵称
        "province": "广东省",       # 选填，省份
        "city": "深圳市",          # 选填，城市
        "grade": 3,                # 选填，年级
        "semester": 1,             # 选填，学期
        "textbook_version": "rj"   # 选填，教材版本
    }
    
    返回数据:
    {
        "status": "success",        # success 表示成功，error 表示失败
        "message": "保存成功"       # 成功或错误信息
    }
    
    错误码:
    - 400: 参数错误
    - 404: 找不到该孩子
    - 500: 服务器错误
    """
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数 id'
            }), 400
        
        user_id = get_jwt_identity()
        # 查找孩子并验证所有权
        child = Child.query.filter_by(
            id=data['id'],
            user_id=int(user_id)
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'message': '找不到该孩子'
            }), 404
        
        # 更新信息（只更新提供的字段）
        if 'nickname' in data:
            child.nickname = data['nickname']
        if 'province' in data:
            child.province = data['province']
        if 'city' in data:
            child.city = data['city']
        if 'grade' in data:
            child.grade = data['grade']
        if 'semester' in data:
            child.semester = data['semester']
        if 'textbook_version' in data:
            child.textbook_version = data['textbook_version']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '保存成功'
        })
        
    except Exception as e:
        logger.error(f"更新孩子信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'更新失败: {str(e)}'
        }), 500 

@family_bp.route('/debug-token', methods=['GET'])
@log_api_call
@jwt_required_with_logger()
def debug_token():
    """调试 JWT token 信息"""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        logger.info(f"Token verification passed in debug_token: user_id={user_id}, claims={claims}")
        
        # 获取用户信息
        user = User.query.get(int(user_id)) if user_id else None
        
        return jsonify({
            'status': 'success',
            'data': {
                'jwt_identity': user_id,
                'jwt_identity_type': type(user_id).__name__,
                'auth_header': request.headers.get('Authorization', ''),
                'user_exists': user is not None,
                'user_id': user.id if user else None
            }
        })
        
    except Exception as e:
        logger.error(f"Token 调试失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': str(e)
        }), 500

@family_bp.route('/family/switch', methods=['POST'])
@jwt_required()
def switch_family():
    """切换当前家庭"""
    try:
        data = request.get_json()
        new_family_id = data.get('family_id')
        user_id = get_jwt_identity()
        
        # 验证用户是否有权限访问该家庭
        relation = UserFamilyRelation.query.filter_by(
            user_id=user_id,
            family_id=new_family_id
        ).first()
        
        if not relation:
            return jsonify({
                'status': 'error',
                'code': 403,
                'message': '无权访问该家庭'
            }), 403
            
        # 创建新的 token，包含新的 family_id
        new_token = create_access_token(
            identity=user_id,
            additional_claims={
                'family_id': new_family_id,
                'is_admin': relation.is_admin
            }
        )
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': {
                'token': new_token,
                'family_id': new_family_id
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in switch_family: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500