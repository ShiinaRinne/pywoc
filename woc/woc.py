from pathlib import Path
from .models import *
from aiohttp import ClientSession, FormData
from typing import List, Dict, Any, Literal
import os
from qiniu import put_file, etag
import asyncio


class WOC:
    def __init__(self, token):
        self.token = token

    def _headers(self):
        return {
            "Origin": "https://woc.space",
            "Referer": "https://woc.space",
            "Authorization": f"{self.token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        }


    async def _request(self,  url: str,method: Literal["GET", "POST"] ="POST", data: FormData | None = None) -> Dict[str, Any]:
        async with ClientSession(headers=self._headers()) as session:
            async with session.request(method, url, data=data) as response:
                result = await response.json()
                if response.status != 200:
                    raise Exception(f"请求失败: {result}")
                return result
        
    async def _account(self) -> AccountResponse:
        """获取账户信息

        Returns:
            AccountResponse: _description_
        """
        url = "https://api.woc.space/account"
        response = await self._request(url, "GET")
        return AccountResponse(**response)

    async def _mine(self) -> MineResponse:
        """获取当前拥有的Space列表

        Returns:
            MineResponse: _description_
        """
        url = "https://api.woc.space/space/mine"
        response = await self._request(url, "GET")
        return MineResponse(**response)

    async def _create(self, name: str) -> CreateResponse:
        """新建Space

        Args:
            name (str): _description_

        Returns:
            WocResponse: _description_
        """
        url = "https://api.woc.space/space/create"
        data = FormData()
        data.add_field("name", name)
        response = await self._request(url, data=data)
        return CreateResponse(**response)

    async def _remove(self, spaceGuid: str) -> WocResponse:
        """删除Space

        Args:
            spaceGuid (_type_): _description_

        Returns:
            WocResponse: _description_
        """
        url = "https://api.woc.space/space/remove"
        data = FormData()
        data.add_field("spaceGuid", spaceGuid)
        response = await self._request(url, data=data)
        return WocResponse(**response)

    async def _initial_file_entity(
        self, file_name: str, size: int, space_guid: str
    ) -> InitialFileEntityResponse:
        """初始化文件实体

        Args:
            file_name (str): 包含扩展名的文件名. 实际请求中还需要一个扩展名参数, 会在该方法内部自动提取
            space_guid (str): 待上传的space的guid
            size (int): 文件大小

        Returns:
            InitialFileEntityResponse: _description_
        """
        url = "https://api.woc.space/space/initial_file_entity"
        data = FormData()
        data.add_field("fileName", file_name)
        data.add_field("extensionName", file_name.split(".")[-1])
        data.add_field("size", str(size))
        data.add_field("spaceGuid", space_guid)
        response = await self._request(url, data=data)
        if response["code"] != 200:
            raise Exception(f"初始化文件实体失败: {response}")
        return InitialFileEntityResponse(**response)

    async def _file_entity_uploaded(
        self, space_guid: str, file_guid: str, size: int
    ) -> FileEntityUploadedResponse:
        """上传文件验证?

        Args:
            space_guid (str): _description_
            file_guid (str): _description_
            size (int): _description_

        Raises:
            Exception: _description_

        Returns:
            FileEntityUploadedResponse: _description_
        """
        url = "https://api.woc.space/space/file_entity_uploaded"
        data = FormData()
        data.add_field("spaceGuid", space_guid)
        data.add_field("fileGuid", file_guid)
        data.add_field("size", str(size))
        response = await self._request(url, data=data)
        if response["code"] != 200:
            raise Exception(f"文件上传失败: {response}")
        return FileEntityUploadedResponse(**response)

    async def _assets(self, space_guid: str, page: int = 0) -> SpaceAssetsResponse:
        """获取文件实体列表

        Args:
            space_guid (str): _description_
            page (int, optional): _description_. Defaults to 0.

        Returns:
            SpaceAssetsResponse: _description_
        """
        url = f"https://api.woc.space/space/{space_guid}/assets?page={page}"
        response = await self._request(url, "GET")
        return SpaceAssetsResponse(**response)

    async def _entities_remove(self, space_guid: str, entity_Guids: str) -> WocResponse:
        """删除文件实体

        Args:
            space_guid (str): _description_
            entity_Guids (str): _description_

        Raises:
            Exception: _description_

        Returns:
            WocResponse: _description_
        """
        url = "https://api.woc.space/space/entities_remove"
        data = FormData()
        data.add_field("spaceGuid", space_guid)
        data.add_field("entityGuids", entity_Guids)
        response = await self._request(url, data=data)
        if response["code"] != 200:
            raise Exception(f"删除文件实体失败: {response}")
        return WocResponse(**response)

    async def refresh(self) -> None:
        """刷新状态
        TODO: 在创建删除 Space 后也需要调用
        """
        self.spaces = [
            SpaceGuid2Name(guid=space.guid, name=space.name)
            for space in await self.list_spaces()
        ]

    async def list_spaces(self) -> List[MineResponseDataSpace]:
        return (await self._mine()).data.spaces

    async def list_entities(
        self, space_guid: str, page: int = 0
    ) -> SpaceAssetsResponse:
        return await self._assets(space_guid, page)

    async def upload_file(
        self, file_path: Path, space_guid: str
    ) -> FileEntityUploadedResponseData:
        file_name = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        init_response = await self._initial_file_entity(file_name, size, space_guid)

        if init_response.code != 200:
            raise Exception(f"初始化文件实体失败: {init_response}")

        token = init_response.data.token
        key = init_response.data.key
        ret, info = put_file(token, key, file_path, version="v2")

        if ret["key"] != key or ret["hash"] != etag(file_path):  # type: ignore
            raise Exception(f"上传文件失败: key: {ret['key']} => {key}, hash: {ret['hash']} => {etag(file_path)}")  # type: ignore

        uploaded_response = await self._file_entity_uploaded(
            space_guid, init_response.data.guid, size
        )
        if uploaded_response.code != 200:
            raise Exception(f"文件上传失败: {uploaded_response}")
        return uploaded_response.data

    async def remove_file(self, space_guid: str, entity_Guids: List[str]) -> WocResponse:  # type: ignore
        entity_Guids: str = ",".join(entity_Guids)
        return await self._entities_remove(space_guid, entity_Guids)
