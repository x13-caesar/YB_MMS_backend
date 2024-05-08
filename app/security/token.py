# -*- coding: UTF-8 -*-
import os

from fastapi import APIRouter, Depends
from app import schemas
from app.security import token_service
from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from dotenv import load_dotenv

from app.dependencies import get_db

import base64
import time
import datetime
import json
import hmac
from hashlib import sha1 as sha


router = APIRouter(
    prefix="/token",
    tags=["token"],
    responses={404: {"description": "Not found"}},
)

load_dotenv()

# 请填写您的AccessKeyId。
access_key_id = os.getenv("ALI_OSS_ACCESS_KEY_ID")
# 请填写您的AccessKeySecret。
access_key_secret = os.getenv("ALI_OSS_ACCESS_KEY_SECRET")
# host的格式为 bucketname.endpoint ，请替换为您的真实信息。
host = os.getenv("ALI_OSS_HOST")
# callback_url为 上传回调服务器的URL，请将下面的IP和Port配置为您自己的真实信息。
callback_url = os.getenv("ALI_CALLBACK_URL")
# 用户上传文件时指定的前缀。
bucket = os.getenv("ALI_OSS_BUCKET")
upload_dir = os.getenv("ALI_OSS_UPLOAD_DIR")
expire_time = os.getenv("ALI_EXPIRE_TIME")


def get_iso_8601(expire):
    gmt = datetime.datetime.utcfromtimestamp(expire).isoformat()
    gmt += "Z"
    return gmt


def get_token():
    now = int(time.time())
    expire_syncpoint = now + expire_time
    expire = get_iso_8601(expire_syncpoint)

    policy_dict = {}
    policy_dict["expiration"] = expire
    condition_array = []
    array_item = []
    array_item.append("starts-with")
    array_item.append("$key")
    array_item.append(upload_dir)
    condition_array.append(array_item)
    policy_dict["conditions"] = condition_array
    policy = json.dumps(policy_dict).strip()
    policy_encode = base64.b64encode(policy.encode())
    h = hmac.new(access_key_secret.encode(), policy_encode, sha)
    sign_result = base64.encodestring(h.digest()).strip()

    callback_dict = {}
    callback_dict["callbackUrl"] = callback_url
    callback_dict["callbackBody"] = (
        "filename=${object}&size=${size}&mimeType=${mimeType}"
        "&height=${imageInfo.height}&width=${imageInfo.width}"
    )
    callback_dict["callbackBodyType"] = "application/x-www-form-urlencoded"
    callback_param = json.dumps(callback_dict).strip()
    base64_callback_body = base64.b64encode(callback_param.encode())

    token_dict = {}
    token_dict["accessid"] = access_key_id
    token_dict["host"] = host
    token_dict["bucket"] = bucket
    token_dict["policy"] = policy_encode.decode()
    token_dict["signature"] = sign_result.decode()
    token_dict["expire"] = expire_syncpoint
    token_dict["dir"] = upload_dir
    token_dict["callback"] = base64_callback_body.decode()
    result = json.dumps(token_dict)
    return token_dict


@router.post("/", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = token_service.authenticate_user(
        form_data.username, form_data.password, db=db
    )
    access_token_expires = timedelta(days=token_service.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = token_service.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/get_user", response_model=schemas.Token)
async def get_user(user_token: str):
    return token_service.get_current_user(user_token)


@router.post("/check_login", response_model=schemas.Token)
async def check_login(user_token: str):
    return token_service.get_current_user(user_token)


@router.get("/oss_policy")
async def get_oss_policy():
    return get_token()
