from typing import Optional, Any, List
from pydantic import BaseModel


class SpaceGuid2Name(BaseModel):
    guid: str
    name: str


class WocResponse(BaseModel):
    code: int
    error: bool
    message: Optional[str]
    data: Optional[Any]


class AccountResponseDataAccounts(BaseModel):
    accountType: str
    activated: bool
    guid: str
    totalSize: int
    usedSize: int
    users: int


class AccountResponseData(BaseModel):
    accountType: str
    accounts: List[AccountResponseDataAccounts]
    totalSize: int
    usedSize: int
    users: int
    aiCredits: int
    allowZip: bool
    anonymousAbleToDownload: bool
    canUploadLogo: bool
    expireIn: int
    guid: str
    hasPassword: bool
    name: str
    notifyWhenAccess: bool
    notifyWhenDownload: bool
    password: str
    proExpireAt: str
    signatureDtos: list
    spaceAmountLimit: int
    spaces: int
    totalSize: int
    usedAiCredits: int
    usedSize: int
    visitorAbleToComment: bool
    visitorAbleToDownload: bool


class AccountResponse(WocResponse):
    data: AccountResponseData


class SpaceEntity(BaseModel):
    blocked: bool
    comments: int
    coverKey: Optional[str]
    extensionName: str
    file: bool
    fileId: str
    fileSize: int
    folderFiles: int
    folderFirstThreeFiles: List[str]
    folderSize: int
    guid: str
    key: str  # 下载链接
    mimeType: str
    name: str
    parentGuid: Optional[str]
    parentName: Optional[str]
    type: str


class SpaceAssetsResponseData(BaseModel):
    currentPage: int
    totalPages: int
    spaceEntities: List[SpaceEntity]


class SpaceAssetsResponse(WocResponse):
    data: SpaceAssetsResponseData


class CreateSpaceResponseData(BaseModel):
    expiredAt: str
    expired: bool
    guid: str
    hoursLeft: int
    listMode: str
    logo: Optional[str]
    name: str
    owner: bool
    visitorAbleToComment: bool
    visitorAbleToDownload: bool
    visitorAbleToUpload: bool


class CreateResponse(WocResponse):
    data: CreateSpaceResponseData


class MineResponseDataSpace(BaseModel):
    entityAmount: int
    expireAt: str
    expired: bool
    guid: str
    logo: Optional[str]
    name: str
    owner: bool
    ownerName: str
    received: bool
    shareLink: Optional[str]
    size: int
    spaceEntities: List[SpaceEntity]


class MineResponseData(BaseModel):
    spaces: List[MineResponseDataSpace]


class MineResponse(WocResponse):
    data: MineResponseData


class InitialFileEntityRequest(BaseModel):
    fileName: str
    extensionName: str
    size: int
    spaceGuid: str


class InitialFileEntityResponseData(BaseModel):
    accessKeyId: Optional[str]
    bucket: Optional[str]
    endpoint: Optional[str]
    region: Optional[str]
    secretAccessKey: Optional[str]

    guid: str
    key: str
    supplier: str
    token: str


class InitialFileEntityResponse(WocResponse):
    data: InitialFileEntityResponseData


class FileEntityUploadedResponseData(BaseModel):
    fileId: str
    spaceEntityGuid: str
    url: str


class FileEntityUploadedResponse(WocResponse):
    data: FileEntityUploadedResponseData
