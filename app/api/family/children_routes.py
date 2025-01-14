from flask import jsonify, request, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...models.child import Child
from ...models.yuwen_item import YuwenItem
from ...models.family import Family, FamilyMember, UserFamilyRelation
from ...models.dictation_config import DictationConfig
from ...extensions import db
from ...utils.logger import logger
from ...utils.decorators import log_api_call
from ...utils.error_codes import *
import traceback
from . import family_bp
from ...models.user import User 

@family_bp.route('/child/add', methods=['POST'])
@jwt_required()
@log_api_call
def add_child():
    try:
        # 开启事务
        db.session.begin_nested()

        data = request.get_json()
        user_id = get_jwt_identity()

        
        # 获取用户下一个可用的 child_id
        max_child = Child.query.filter_by(user_id=user_id).order_by(Child.child_id.desc()).first()
        next_child_id = (max_child.child_id + 1) if max_child else 1
        relation = UserFamilyRelation.query.filter_by(user_id=user_id).first()

        if next_child_id == 1:
            # 检查用户是否已有家庭关系
            relation = UserFamilyRelation.query.filter_by(user_id=user_id).first()
            
            # 如果没有家庭关系,创建新家庭
            if not relation:
                try:
                    user = User.query.get(user_id)
                    family_name = f"{user.nickname or '我'}的家庭"
                    
                    # 创建新家庭
                    family = Family(
                        name=family_name,
                        created_by=user_id
                    )
                    db.session.add(family)
                    db.session.flush()
                    
                    # 创建用户-家庭关系
                    relation = UserFamilyRelation(
                        user_id=user_id,
                        family_id=family.id,
                        role='parent',
                        is_admin=True
                    )
                    db.session.add(relation)
                    db.session.flush()
                except Exception as e:
                    db.session.rollback()
                    raise e
            
        family_id = relation.family_id     
            
        try:
            # 创建 Child 记录
            child = Child(
                user_id=user_id,
                family_id=family_id,
                child_id=next_child_id,
                nickname=data['nickname'],
                province=data.get('province'),
                city=data.get('city'),
                grade=data.get('grade'),
                semester=data.get('semester'),
                textbook_version=data.get('textbook_version')
            )
            db.session.add(child)
            db.session.flush()
            
            # 同步创建 FamilyMember 记录
            member = FamilyMember(
                family_id=family_id,
                name=data['nickname'],
                role='child',
                is_child=True
            )
            db.session.add(member)
            db.session.flush()
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'child_id': child.id,
                    'family_id': family_id
                }
            })
        except Exception as e:
            # 回滚所有操作
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"增加孩子失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 

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
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数 id'
            }), 400
        
        user_id = get_jwt_identity()
        try:
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
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': '保存成功'
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"更新孩子信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'更新失败: {str(e)}'
        }), 500
