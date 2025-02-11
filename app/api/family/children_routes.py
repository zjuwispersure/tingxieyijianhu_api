from flask import jsonify, request, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...models.child import Child
from ...models.yuwen_item import YuwenItem
from ...models.family import Family, FamilyMember, UserFamilyRelation
from ...models.dictation import DictationConfig
from ...extensions import db
from ...utils.logger import logger
from ...utils.decorators import log_api_call, with_db_retry
from ...utils.error_codes import *
import traceback
from . import family_bp
from ...models.user import User 
from sqlalchemy.exc import IntegrityError
from datetime import datetime

@family_bp.route('/child/add', methods=['POST'])
@jwt_required()
@log_api_call
def add_child():
    """添加孩子"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        # 获取用户
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'code': USER_NOT_FOUND,
                'message': '用户不存在'
            }), 404
        
        # 获取或创建家庭
        relation = UserFamilyRelation.query.filter_by(user_id=current_user_id).first()
        if not relation:
            family_name = "我的家庭"  # 使用默认名称
            family = Family(
                name=family_name,
                created_by=current_user_id
            )
            db.session.add(family)
            db.session.flush()  # 获取 family.id
            
            # 创建用户-家庭关系
            relation = UserFamilyRelation(
                user_id=current_user_id,
                family_id=family.id,
                role='parent',
                is_admin=True
            )
            db.session.add(relation)
            
        # 验证必需参数
        required_fields = ['nickname']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'code': MISSING_REQUIRED_PARAM,
                    'message': get_error_message(MISSING_REQUIRED_PARAM, field)
                }), 400
        
        # 检查昵称是否已存在
        if Child.check_nickname_exists(relation.family_id, data['nickname']):
            return jsonify({
                'status': 'error',
                'code': DUPLICATE_NICKNAME,
                'message': '该昵称在家庭内已存在'
            }), 400
        
        # 获取下一个可用的 child_id
        max_child = Child.query.filter_by(user_id=current_user_id).order_by(Child.child_id.desc()).first()
        next_child_id = (max_child.child_id + 1) if max_child else 1
        
        # 创建新孩子
        child = Child(
            user_id=current_user_id,
            family_id=relation.family_id,
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
            family_id=relation.family_id,
            name=data['nickname'],
            role='child',
            is_child=True
        )
        db.session.add(member)
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': child.to_dict()
        })
        
    except IntegrityError as e:
        # 处理唯一约束冲突
        db.session.rollback()
        if "unique_user_family_child" in str(e):
            return jsonify({
                'status': 'error',
                'code': DUPLICATE_CHILD,
                'message': get_error_message(DUPLICATE_CHILD)
            }), 400
        raise
        
    except ValueError as e:
        # 处理验证错误
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'code': INVALID_PARAMS,
            'message': str(e)
        }), 400
        
    except Exception as e:
        # 处理其他错误
        db.session.rollback()
        raise
        
    except Exception as e:
        # 确保清理会话状态
        db.session.remove()
        logger.error(f"添加孩子失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@family_bp.route('/child/get/all', methods=['GET'])
@jwt_required()
@log_api_call
@with_db_retry()
def get_all_children():
    """获取当前用户的所有孩子"""
    try:
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        children = Child.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).order_by(
            Child.child_id.asc()
        ).all()
        
        # 记录查询结果
        child_info = [{
            'id': c.id,
            'child_id': c.child_id,
            'nickname': c.nickname
        } for c in children]
        logger.info(f"Found children: {child_info}")
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': {
                'children': [child.to_dict() for child in children]
            }
        })
        
    except Exception as e:
        logger.error(f"获取孩子列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@family_bp.route('/child/get/', methods=['GET'])
@jwt_required()
@log_api_call
def get_child():
    """获取指定孩子的信息
    
    Query Parameters:
        child_id: 孩子ID
        
    Returns:
        成功返回:
        {
            'status': 'success',
            'code': 0,
            'data': {
                'child': {...}  # 孩子信息
            }
        }
        
        失败返回:
        {
            'status': 'error',
            'code': CHILD_NOT_FOUND,
            'message': '找不到该孩子'
        }
    """
    try:
        # 获取参数
        child_id = request.args.get('child_id', type=int)
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400
            
        # 获取当前用户ID
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # 查询指定孩子
        child = Child.query.filter_by(
            id=child_id,
            user_id=user_id
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': {
                'child': child.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"获取孩子信息失败: {str(e)}\n{traceback.format_exc()}")
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
@jwt_required()
@log_api_call
@with_db_retry(max_retries=3, delay=0.2)
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
    
    Returns:
        成功返回:
        {
            "status": "success",        # success 表示成功，error 表示失败
            "code": 0,                  # 错误码，0 表示成功
            "message": "保存成功",      # 成功或错误信息
            "data": {                   # 更新后的数据
                "id": 1,
                "nickname": "小明",
                ...
            }
        }
        
        失败返回:
        {
            "status": "error",
            "code": int,               # 错误码
            "message": str             # 错误信息
        }
    
    Raises:
        400: 参数错误
        404: 找不到该孩子
        500: 服务器错误
    """
    try:
        data = request.get_json()
        child_id = data.get('id')
        
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=child_id,
            user_id=int(get_jwt_identity())
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        # 更新字段
        for field in ['grade', 'semester', 'textbook_version', 'province', 'city']:
            if field in data:
                setattr(child, field, data[field])
                
        # 更新时间戳
        child.updated_at = datetime.utcnow()
        
        # 提交更改
        db.session.commit()
        
        # 重新查询以确保数据已更新
        child = Child.query.filter_by(id=child_id).first()
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'message': '保存成功',
            'data': child.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新孩子信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500
