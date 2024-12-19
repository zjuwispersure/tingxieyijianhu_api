from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.family import Family, FamilyMember
from ..extensions import db

family_bp = Blueprint('family', __name__)

@family_bp.route('/family', methods=['POST'])
@jwt_required()
def create_family():
    """创建家庭群组"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
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
    
    return jsonify(family.to_dict())

@family_bp.route('/family', methods=['GET'])
@jwt_required()
def get_family():
    """获取当前用户的家庭群组信息"""
    user_id = get_jwt_identity()
    family = Family.query.filter_by(user_id=user_id).first_or_404()
    return jsonify(family.to_dict())

@family_bp.route('/family/invite', methods=['POST'])
@jwt_required()
def invite_member():
    """邀请家庭成���"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    family = Family.query.filter_by(user_id=user_id).first_or_404()
    
    member = FamilyMember(
        family_id=family.id,
        user_id=data['user_id']
    )
    
    db.session.add(member)
    db.session.commit()
    
    return jsonify(member.to_dict())

@family_bp.route('/family/members', methods=['GET'])
@jwt_required()
def get_members():
    """获取家庭成员列表"""
    user_id = get_jwt_identity()
    family = Family.query.filter_by(user_id=user_id).first_or_404()
    
    members = FamilyMember.query.filter_by(family_id=family.id).all()
    return jsonify([member.to_dict() for member in members])

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