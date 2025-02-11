import os
from datetime import datetime, timedelta
import oss2
import json
from aliyunsdkcore import client
from aliyunsdksts.request.v20150401 import AssumeRoleRequest
from flask import current_app

def get_sts_token():
    """获取 STS Token
    
    Returns:
        dict: 包含 access_key_id, access_key_secret, security_token 的字典
    """
    try:
        # 从环境变量获取 RAM 配置
        access_key = os.getenv('OSS_ACCESS_KEY')
        access_secret = os.getenv('OSS_ACCESS_SECRET')
        role_arn = os.getenv('OSS_ROLE_ARN')  # RAM角色ARN
        
        # 创建 AcsClient 实例
        clt = client.AcsClient(access_key, access_secret, 'cn-shanghai')
        
        # 创建 AssumeRole 请求
        request = AssumeRoleRequest.AssumeRoleRequest()
        request.set_accept_format('json')
        request.set_RoleArn(role_arn)
        request.set_RoleSessionName('yuwen-app')  # 自定义会话名称
        
        # 设置权限策略(可选)
        policy = {
            "Version": "1",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["oss:GetObject"],
                    "Resource": [
                        f"acs:oss:*:*:{os.getenv('OSS_BUCKET')}/data/yuwen/*"
                    ]
                }
            ]
        }
        request.set_Policy(json.dumps(policy))
        
        # 设置过期时间(最长3600秒)
        request.set_DurationSeconds(3600)
        
        # 发起请求
        response = json.loads(clt.do_action_with_exception(request))
        
        return {
            'access_key_id': response['Credentials']['AccessKeyId'],
            'access_key_secret': response['Credentials']['AccessKeySecret'],
            'security_token': response['Credentials']['SecurityToken']
        }
    except Exception as e:
        current_app.logger.error(f"Error getting STS token: {str(e)}")
        return None

def get_ecs_metadata_token():
    """获取实例元数据Token"""
    try:
        import requests
        metadata_token_url = 'http://100.100.100.200/latest/api/token'
        token_headers = {'X-aliyun-ecs-metadata-token-ttl-seconds': '3600'}
        r = requests.put(metadata_token_url, headers=token_headers, timeout=5)
        return r.text
    except Exception as e:
        current_app.logger.error(f"Error getting metadata token: {str(e)}")
        return None

def get_ecs_role_credentials():
    """从 ECS 实例元数据获取 STS 凭证"""
    try:
        token = get_ecs_metadata_token()
        if not token:
            return None
            
        import requests
        metadata_url = 'http://100.100.100.200/latest/meta-data/ram/security-credentials/'
        headers = {'X-aliyun-ecs-metadata-token': token}
        
        # 获取角色名
        r = requests.get(metadata_url, headers=headers, timeout=5)
        role_name = r.text.strip()
        
        # 获取临时凭证
        r = requests.get(f"{metadata_url}{role_name}", headers=headers, timeout=5)
        credentials = r.json()
        
        return {
            'access_key_id': credentials['AccessKeyId'],
            'access_key_secret': credentials['AccessKeySecret'],
            'security_token': credentials['SecurityToken']
        }
    except Exception as e:
        current_app.logger.error(f"Error getting ECS role credentials: {str(e)}")
        return None

def get_signed_url(audio_url: str, expires: int = 3600) -> str:
    """根据环境生成签名URL"""
    try:
        endpoint = os.getenv('OSS_ENDPOINT')
        bucket_name = os.getenv('OSS_BUCKET')
        
        if not all([endpoint, bucket_name, audio_url]):
            current_app.logger.warning("Missing OSS config or audio_url")
            return audio_url
            
        # 判断是否在 ECS 环境
        is_ecs = os.getenv('ALIBABA_CLOUD_ECS_METADATA') == 'true'
        
        if is_ecs:
            # ECS 环境：使用实例角色
            credentials = get_ecs_role_credentials()
            if not credentials:
                return audio_url
                
            auth = oss2.StsAuth(
                credentials['access_key_id'],
                credentials['access_key_secret'],
                credentials['security_token']
            )
        else:
            # 本地环境：使用 STS Token
            sts_token = get_sts_token()  # 之前实现的 STS Token 方法
            if not sts_token:
                return audio_url
                
            auth = oss2.StsAuth(
                sts_token['access_key_id'],
                sts_token['access_key_secret'],
                sts_token['security_token']
            )
        
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        object_key = audio_url.split('/', 3)[-1]
        return bucket.sign_url('GET', object_key, expires)
        
    except Exception as e:
        current_app.logger.error(f"Error generating signed URL: {str(e)}")
        return audio_url 