from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.user import User
from ..models.child import Child
from ..extensions import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    """获取当前登录用户信息"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/child', methods=['POST'])
@jwt_required()
def create_child():
    """创建孩子信息"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    child = Child(
        user_id=user_id,
        nickname=data['nickname'],
        school_province=data['school_province'],
        school_city=data['school_city'],
        grade=data['grade'],
        semester=data['semester'],
        textbook_version=data['textbook_version']
    )
    
    db.session.add(child)
    db.session.commit()
    return jsonify(child.to_dict())

@user_bp.route('/children', methods=['GET'])
@jwt_required()
def get_children():
    """获取当��用户的所有孩子信息"""
    user_id = get_jwt_identity()
    children = Child.query.filter_by(user_id=user_id).all()
    return jsonify([child.to_dict() for child in children])

@user_bp.route('/child/<int:id>', methods=['PUT'])
@jwt_required()
def update_child(id):
    """更新孩子信息"""
    user_id = get_jwt_identity()
    child = Child.query.filter_by(id=id, user_id=user_id).first_or_404()
    
    data = request.get_json()
    for key, value in data.items():
        setattr(child, key, value)
    
    db.session.commit()
    return jsonify(child.to_dict())

@user_bp.route('/child/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_child(id):
    """删除孩子信息"""
    user_id = get_jwt_identity()
    child = Child.query.filter_by(id=id, user_id=user_id).first_or_404()
    
    db.session.delete(child)
    db.session.commit()
    return '', 204 