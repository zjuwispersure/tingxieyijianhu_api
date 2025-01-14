from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token, verify_jwt_in_request
from app.models.user import User
from app.utils.decorators import log_api_call
from ...models.family import Family, FamilyMember, UserFamilyRelation
from ...extensions import db
from ...utils.logger import logger
import traceback
from ...utils.error_codes import *  # 导入错误码
from sqlalchemy.exc import OperationalError
from time import sleep
from functools import wraps
from . import family_bp


@family_bp.route('/family/create', methods=['POST'])
@jwt_required()
@log_api_call
def create_family():
    """创建家庭"""
    try:
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        user_id = get_jwt_identity()
        
        try:
            # 创建家庭
            family = Family(
                name=data.get('name', '我的家庭'),
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
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'family_id': family.id
                }
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
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
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'user_id')
            }), 400
        
        user_id = get_jwt_identity()
        try:
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
            db.session.flush()
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': member.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
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
    try:
        # 开启事务
        db.session.begin_nested()
        user_id = get_jwt_identity()
        
        try:
            family = Family.query.filter_by(user_id=user_id).first_or_404()
            
            member = FamilyMember.query.filter_by(
                family_id=family.id,
                id=id
            ).first_or_404()
            
            db.session.delete(member)
            # 提交事务
            db.session.commit()
            
            return '', 204
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"移除家庭成员失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500


@family_bp.route('/family/switch', methods=['POST'])
@jwt_required()
def switch_family():
    """切换当前家庭"""
    try:
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        new_family_id = data.get('family_id')
        user_id = get_jwt_identity()
        
        try:
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
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'code': 0,
                'data': {
                    'token': new_token,
                    'family_id': new_family_id
                }
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"切换家庭失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@family_bp.route('/family/update', methods=['POST'])
@jwt_required()
@log_api_call
def update_family():
    """更新家庭信息"""
    try:
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        user_id = get_jwt_identity()
        
        try:
            # 验证家庭所有权
            family = Family.query.filter_by(
                id=data['family_id'],
                created_by=user_id
            ).first()
            
            if not family:
                return jsonify({
                    'status': 'error',
                    'code': RESOURCE_NOT_FOUND,
                    'message': get_error_message(RESOURCE_NOT_FOUND)
                }), 404
                
            # 更新信息
            if 'name' in data:
                family.name = data['name']
                
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': '更新成功'
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"更新家庭信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500