import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.child import Child
from app.models.dictation import Dictation

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """创建测试命令行运行器"""
    return app.test_cli_runner()

@pytest.fixture
def auth_token(app, client):
    """创建测试用认证令牌"""
    with app.app_context():
        user = User(openid='test_openid')
        db.session.add(user)
        db.session.commit()
        
        response = client.post('/login', json={'code': 'test_code'})
        return response.json['access_token']

@pytest.fixture
def test_child(app, auth_token):
    """创建测试用孩子数据"""
    with app.app_context():
        user = User.query.filter_by(openid='test_openid').first()
        child = Child(
            user_id=user.id,
            nickname='Test Child',
            school_province='北京',
            school_city='北京',
            grade='三年级',
            semester='上学期',
            textbook_version='人教版'
        )
        db.session.add(child)
        db.session.commit()
        return child

@pytest.fixture
def test_dictation(app, test_child):
    """创建测试用听写记录"""
    with app.app_context():
        dictation = Dictation(
            child_id=test_child.id,
            mode='normal',
            word_count=10,
            repeat_count=2,
            interval=5,
            prioritize_errors=False,
            content=['测试', '单词']
        )
        db.session.add(dictation)
        db.session.commit()
        return dictation 