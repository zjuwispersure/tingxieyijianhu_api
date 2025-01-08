from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.family import Family, FamilyMember
from ..extensions import db
from ..models import Child, DictationConfig
from ..utils.auth import login_required
from ..utils.logger import log_api_call, logger
import traceback
from ..utils.error_codes import *  # 导入错误码

family_bp = Blueprint('family', __name__)

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
        
        # 检查是否已有家庭
        if Family.query.filter_by(user_id=user_id).first():
            return jsonify({
                'status': 'error',
                'code': RESOURCE_ALREADY_EXISTS,
                'message': get_error_message(RESOURCE_ALREADY_EXISTS)
            }), 400
        
        family = Family(
            user_id=user_id,
            name=data['name']
        )
        
        # 创建者自动成为家庭成员
        member = FamilyMember(
            family=family,
            user_id=user_id
        )
        
        db.session.add(family)
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': family.to_dict()
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

@family_bp.route('/child/create', methods=['POST'])
@login_required
@log_api_call
def add_child():
    """添加孩子
    
    请求参数:
    {
        "nickname": "小明",
        "province": "广东省",
        "city": "深圳市",
        "grade": 3,
        "semester": 1,
        "textbook_version": "rj"
    }
    
    返回数据:
    {
        "status": "success",
        "data": {
            "child": {
                "id": 1,
                "child_id": 1,
                "nickname": "小明",
                ...
            }
        }
    }
    
    错误返回:
    {
        "status": "error",
        "code": 1001,      # 参数无效
        "message": "无效的请求数据格式，需要 JSON 格式"
    }
    或
    {
        "status": "error", 
        "code": 5001,      # 内部错误
        "message": "创建失败: ..."
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'code': 1001,
                'message': '无效的请求数据格式，需要 JSON 格式'
            }), 400
        
        # 验证必要字段
        required_fields = ['nickname', 'province', 'city', 'grade', 'semester', 'textbook_version']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'code': 1002,
                    'message': f'缺少必要参数: {field}'
                }), 400
        
        # 获取当前用户的最大 child_id
        max_child = Child.query.filter_by(user_id=g.user.id).order_by(Child.child_id.desc()).first()
        next_child_id = (max_child.child_id + 1) if max_child else 1
        
        child = Child(
            user_id=g.user.id,
            child_id=next_child_id,
            nickname=data['nickname'],
            province=data['province'],
            city=data['city'],
            grade=data['grade'],
            semester=data['semester'],
            textbook_version=data['textbook_version']
        )
        db.session.add(child)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': {
                'child': child.to_dict()
            }
        })
            
    except Exception as e:
        logger.error(f"创建孩子失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': 5001,
            'message': f'创建失败: {str(e)}'
        }), 500

@family_bp.route('/child/get', methods=['GET'])
@login_required
@log_api_call
def get_children():
    """获取当前用户的所有孩子"""
    try:
        children = Child.query.filter_by(user_id=g.user.id).all()
        return jsonify({
            'status': 'success',
            'data': [{
                'id': child.id,
                'child_id': child.child_id,
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
@login_required
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
            
        exists = Child.query.filter_by(
            user_id=g.user.id,
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
@jwt_required()
@log_api_call
def get_children_count():
    """获取当前用户的孩子数量统计信息"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取所有孩子数量
        total_count = Child.query.filter_by(user_id=user_id).count()
        
        # 获取已配置听写的孩子数量
        configured_count = Child.query.join(DictationConfig).filter(
            Child.user_id == user_id
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


@family_bp.route('/api/test', methods=['GET'])
def test_route():
    return jsonify({'message': 'Family blueprint is working'}) 

@family_bp.route('/api/child/update', methods=['POST'])
@login_required
@log_api_call
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
        
        # 查找孩子并验证所有权
        child = Child.query.filter_by(
            id=data['id'],
            user_id=g.user.id
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