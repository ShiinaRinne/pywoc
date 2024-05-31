import sys
import argparse
from woc.models import MineResponseDataSpace, SpaceAssetsResponse, SpaceGuid2Name
from woc.woc import WOC
import asyncio
from typing import List
from pathlib import Path
import os


class WOCCli:
    def __init__(self):
        self.token_save_path = f"{os.getenv('LOCALAPPDATA')}/woc_token"
        self.token = self.check_token()
        self.woc: WOC = WOC(self.token) if self.token else None  # type: ignore
        if self.woc is not None:
            asyncio.run(self.woc.refresh())
        self.current_space = (
            self.woc.spaces[0] if self.woc and self.woc.spaces else None
        )

    def check_token(self):
        try:
            with open(self.token_save_path, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    async def login(self, token: str):
        while token is None:
            _token = input("请输入token: ")
            if _token.startswith("Bearer"):
                token = _token
            else:
                print("格式错误, 需要以Bearer开头")
        with open(self.token_save_path, "w") as f:
            f.write(token)
        self.token = token
        self.woc = WOC(token)
        await self.woc.refresh()

    async def shell(self):
        cmd_mapping = {
            "exit": sys.exit,
            "login": self.login,
            "lss": self.list_spaces,
            "lsf": self.list_files,
            "upload": self.upload_files,
            "cd": self.cd,
        }

        while True:
            cmd = input(">>> ").strip()
            action = cmd_mapping.get(cmd.split()[0])
            if action != self.login and not self.woc:
                print("请先登录")
                continue
            if action:
                await action(cmd[1:] if len(cmd.split()) > 1 else None)
            else:
                print("未知命令")

    async def list_spaces(self, cmd):
        print("name         guid                                 size     entityAmount ownerName      expireAt")
        for space in await self.woc.list_spaces():
            print(f"{space.name:<12} {space.guid:<36} {space.size:<8} {space.entityAmount:<12} {space.ownerName:<10} {space.expireAt}")

    async def list_files(self, page: int) -> None:
        if len(self.woc.spaces) > 1 or self.current_space is None:
            print("请先使用cd选择一个 space")
            return
        page = 0 if page is None else int(page) - 1
        assets: SpaceAssetsResponse = await self.woc.list_entities(
            self.current_space.guid, page
        )
        print(f"当前 space:{self.current_space.name} page: {assets.data.currentPage+1}/{assets.data.totalPages}")
        for entity in assets.data.spaceEntities:
            print(f"{entity.name}.{entity.extensionName:<5} {entity.key}")

    async def upload_files(self, paths: str):
        if paths is None:
            paths = input("请输入文件路径(有多个时, 使用空格分隔):").strip()

        if isinstance(paths, str):
            files = paths.split()
        else:
            files = paths

        for file in files:
            file = Path(file)
            await self.woc.upload_file(file, self.current_space.guid)  # type: ignore

    async def cd(self, space_guid: str):
        if space_guid is None:
            space_guid = input(
                "请输入 space 的 guid (使用前缀匹配, 返回第一个匹配的 space): "
            )

        for s in await self.woc.list_spaces():
            if s.guid.startswith(space_guid):
                self.current_space = list(
                    filter(lambda x: x.guid == s.guid, self.woc.spaces)
                )[0]
                print(f"当前 space: {s.name}")


def parse_args():
    parser = argparse.ArgumentParser(description="Woc! Py!!!")
    parser.add_argument(
        "--login",
        help="使用auth bearer 啥的登录。参数为那个token, 从网页f12复制即可, 之后会保存到本地就不需要了. 例如 woc --login 'Bearer eyJ0xxxx'",
    )
    parser.add_argument("--list-space", action="store_true", help="显示当前的所有space")
    parser.add_argument("--upload", action="store_true", help="需要上传的文件列表")
    parser.add_argument("files", nargs="*", help="需要上传的文件列表")
    parser.add_argument("--shell", action="store_true", help="进入shell模式")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cli = WOCCli()
    if args.login:
        asyncio.run(cli.login(args.login))
    if args.shell:
        asyncio.run(cli.shell())
    if args.list_space:
        asyncio.run(cli.list_spaces(None))
    if args.upload or args.files:
        if not args.files:
            print("未指定文件列表。")
        else:
            asyncio.run(cli.upload_files(args.files))
