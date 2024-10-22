import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import json
import logging
import aiofiles
from fastapi import HTTPException
import fnmatch

logger = logging.getLogger(__name__)

# ログレベルを DEBUG に設定
logger.setLevel(logging.DEBUG)

# コンソールハンドラを作成
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# ファイルハンドラを作成
file_handler = logging.FileHandler('file_service.log')
file_handler.setLevel(logging.DEBUG)

# フォーマッタを作成
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# ハンドラをロガーに追加
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 全てのログレベルでメッセージを出力するように設定
logger.debug('デバッグメッセージ')
logger.info('情報メッセージ')
logger.warning('警告メッセージ')
logger.error('エラーメッセージ')
logger.critical('クリティカルメッセージ')

def get_file_path(projectId: str, filename: str, upload_dir: str) -> str:
    """
    projectIdに基づいてファイルパスを決定し、ファイルの存在を確認する関数
    """
    if projectId == "babel":
        file_path = os.path.join('..', filename)
        print(file_path)
    else:
        file_path = os.path.join(os.path.expanduser("~"), "babel_generated", projectId, filename)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイル {filename} が見つかりません")
    
    return file_path

async def save_file(projectId: str, file_data: dict):
    logger.info(f"ファイル保存リクエストを受信: {file_data['file_path']}")
    logger.debug(f"ファイル内容のサイズ: {len(file_data['content'])} バイト")
    try:
        file_path = get_file_path(projectId, file_data['file_path'], "")
        logger.debug(f"ファイルを開いて書き込みを開始: {file_path}")
        async with aiofiles.open(file_path, "w") as f:
            await f.write(file_data['content'])
        logger.info(f"ファイルの保存に成功: {file_path}")
        logger.debug(f"保存されたファイルのパス: {os.path.abspath(file_path)}")
        return {"message": "ファイルが正常に保存されました"}
    except IOError as io_err:
        logger.error(f"ファイルの書き込み中にIOエラーが発生: {str(io_err)}")
        logger.debug(f"IOエラーの詳細: {io_err.__class__.__name__}")
        raise HTTPException(status_code=500, detail=f"ファイルの書き込みに失敗: {str(io_err)}")
    except Exception as e:
        logger.error(f"ファイルの保存中に予期せぬエラーが発生: {str(e)}")
        logger.debug(f"エラーの詳細: {e.__class__.__name__}")
        logger.debug(f"エラーのトレースバック: ", exc_info=True)
        raise HTTPException(status_code=500, detail=f"予期せぬエラー: {str(e)}")

async def load_file(projectId: str, filename: str):
    logger.info(f"ファイル読み込みリクエストを受信: {filename}")
    try:
        file_path = get_file_path(projectId, filename, "")
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
        logger.info(f"ファイルの読み込みに成功: {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {filename}")
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    except Exception as e:
        logger.error(f"ファイルの読み込み中にエラーが発生: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_generated_dirs():
    # ホームディレクトリを取得
    home_dir = os.path.expanduser("~")
    base_path = os.path.join(home_dir, "babel_generated")
    logger.info(f"生成されたディレクトリの取得を開始します。ベースパス: {base_path}")
    try:
        logger.debug("ディレクトリ構造の作成を開始します。")
        gitignore_patterns = read_gitignore("../../.gitignore")
        structure = create_structure(base_path, base_path, gitignore_patterns)
        logger.debug(f"ディレクトリ構造を作成しました: {structure}")
        
        app_dirs = []
        logger.debug("アプリディレクトリの検索を開始します。")
        for item in structure:
            logger.debug(f"項目を処理中: {item['name']}")
            if item["type"] == "folder":
                frontend_path = os.path.join(item["path"])
                full_path = os.path.join(base_path, frontend_path)
                logger.debug(f"フロントエンドパスを確認中: {full_path}")
                
                if os.path.exists(full_path):
                    app_dir = {
                        "name": item["name"],
                        "path": f"../generated/{item['name']}/frontend/App"
                    }
                    app_dirs.append(app_dir)
                    logger.debug(f"アプリディレクトリを追加しました: {app_dir}")
                else:
                    logger.debug(f"フロントエンドパスが存在しません: {full_path}")
        
        logger.info(f"生成されたディレクトリを正常に取得しました。総数: {len(app_dirs)}")
        logger.debug(f"取得されたアプリディレクトリの詳細: {app_dirs}")
        return app_dirs
    except Exception as e:
        logger.error(f"生成されたディレクトリの取得中にエラーが発生しました: {str(e)}", exc_info=True)
        logger.debug(f"エラーの詳細情報: {e.__class__.__name__}")
        raise HTTPException(status_code=500, detail="ディレクトリの取得に失敗しました")

async def get_directory_structure(path_type: str):
    logger.info(f"ディレクトリ構造の取得を開始します。path_type: {path_type}")

    # 現在の作業ディレクトリを取得し、表示する
    import os

    def print_current_directory():
        """
        現在の作業ディレクトリを取得し、表示する関数
        """
        current_dir = os.getcwd()
        logger.debug(f"現在の作業ディレクトリ: {current_dir}")

    # 関数を呼び出して現在のディレクトリを表示
    print_current_directory()

    if path_type == "file_explorer":
        base_path = "../src/components/generated/"
    elif path_type == "requirements_definition":
        base_path = "meta/1_domain_exp"
    elif path_type == "babel":
        base_paths = ["../../src", "../../Dockerfile", "../../docker-compose.yml", "../../README.md"]
    else:
        # ホームディレクトリのbabel_generatedフォルダから取得するように変更
        home_dir = os.path.expanduser("~")
        base_path = os.path.join(home_dir, "babel_generated", path_type)
        logger.debug(f"base_pathを設定しました: {base_path}")

    logger.info(f"base_pathを設定しました: {base_path if path_type != 'babel' else base_paths}")

    try:
        if path_type == "babel":
            gitignore_patterns = read_gitignore("../../.gitignore")
        else:
            gitignore_path = os.path.join(base_path, ".gitignore")
            logger.debug(f".gitignoreファイルのパスを設定しました: {gitignore_path}")
            gitignore_patterns = read_gitignore(gitignore_path)
            logger.info(f".gitignoreファイルを読み込みました: {gitignore_path}")
            logger.debug(f"読み込んだgitignoreパターン: {gitignore_patterns}")

        if path_type == "babel":
            structure = []
            for base_path in base_paths:
                logger.debug(f"babelモード: {base_path}を処理中")
                if os.path.isfile(base_path):
                    if not should_ignore(os.path.basename(base_path), gitignore_patterns):
                        content = read_file_content(base_path)
                        structure.append({
                            "name": os.path.basename(base_path),
                            "type": "file",
                            "path": base_path,
                        })
                        # logger.debug(f"ファイルを追加しました: {os.path.basename(base_path)}")
                else:
                    structure.extend(create_structure(base_path, base_path, gitignore_patterns))
                    # logger.debug(f"ディレクトリ構造を追加しました: {base_path}")
        else:
            structure = create_structure(base_path, base_path, gitignore_patterns)
            # logger.debug(f"ディレクトリ構造を作成しました: {base_path}")

        # logger.info(f"{path_type}のディレクトリ構造を正常に作成しました")
        return {"structure": structure}
    except Exception as e:
        # logger.error(f"{path_type}のディレクトリ構造の取得中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="ディレクトリ構造の取得に失敗しました")

def create_structure(path, base_path, gitignore_patterns):
    structure = []
    for item in os.listdir(path):
        if should_ignore(item, gitignore_patterns):
            continue
        item_path = os.path.join(path, item)
        relative_path = os.path.relpath(item_path, base_path)
        if os.path.isdir(item_path):
            structure.append({
                "name": item,
                "type": "folder",
                "path": relative_path,
                "children": create_structure(item_path, base_path, gitignore_patterns)
            })
        else:
            content = read_file_content(item_path)
            structure.append({
                "name": item,
                "type": "file",
                "path": relative_path,
            })
    return structure

def read_gitignore(path):
    # .gitignoreファイルを読み込む関数
    if os.path.exists(path):
        # ファイルが存在する場合
        with open(path, 'r') as f:
            # ファイルを開いて読み込む
            return [
                line.strip()  # 各行の前後の空白を削除
                for line in f
                if line.strip() and not line.startswith('#')  # 空行とコメント行を除外
            ]
    # ファイルが存在しない場合は空のリストを返す
    return []

def should_ignore(item, gitignore_patterns):
    if gitignore_patterns is None:
        return False
    
    # node_modules、.git、.nextディレクトリを無視
    if any(dir in item.split(os.path.sep) for dir in ['node_modules', '.git']):
        return True
    
    # その他の .gitignore パターンをチェック
    for pattern in gitignore_patterns:
        if fnmatch.fnmatch(item, pattern):
            return True
        # ディレクトリパターンの場合、すべてのサブディレクトリを無視
        if pattern.endswith('/') and (item.startswith(pattern) or item.startswith(pattern.rstrip('/'))):
            return True
    
    return False

def read_file_content(file_path):
    try:
        if os.path.splitext(file_path)[1] in ['.gz', '.woff2', '.ico', '.pyc']:
            return None
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # logger.warning(f"ファイルの読み込みをスキップしました（エンコーディングエラー）: {file_path}")
        return None
    except Exception as e:
        # logger.error(f"ファイル読み込み中にエラーが発生しました: {file_path}, エラー: {str(e)}")
        return None

# ファイル操作サービス
import os
from fastapi import UploadFile
from models.file import FileModel
from utils.file_operations import get_file_size, ensure_directory_exists, read_file, write_file, append_to_file

class FileService:
    def __init__(self, upload_dir=os.path.expanduser("~")):
        """
        FileServiceクラスのコンストラクタ
        
        Parameters:
        upload_dir (str): ファイルをアップロードするディレクトリ。デフォルトはユーザーのホームディレクトリ。
        """
        self.upload_dir = upload_dir
        ensure_directory_exists(self.upload_dir)

    async def save_file(self, file: UploadFile) -> FileModel:
        file_path = get_file_path("babel", file.filename, self.upload_dir)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        size = get_file_size(file_path)
        return FileModel(filename=file.filename, size=size)

    async def list_files(self) -> list[FileModel]:
        files = []
        for filename in os.listdir(self.upload_dir):
            file_path = get_file_path("babel", filename, self.upload_dir)
            size = get_file_size(file_path)
            files.append(FileModel(filename=filename, size=size))
        return files

    async def get_file_content(self, projectId: str, filename: str) -> str:
        file_path = get_file_path(projectId, filename, self.upload_dir)
        return read_file(file_path)


    async def edit_file(self, filename: str, line_number: int, new_content: str):
        file_path = os.path.join(self.upload_dir, filename)
        content = read_file(file_path).splitlines()
        if line_number < 1 or line_number > len(content):
            raise ValueError("Invalid line number")
        content[line_number - 1] = new_content
        write_file(file_path, "\n".join(content))

    async def append_to_file(self, filename: str, content: str):
        file_path = os.path.join(self.upload_dir, filename)
        append_to_file(file_path, content)

    async def delete_file(self, filename: str):
        file_path = os.path.join(self.upload_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {filename} not found")
        os.remove(file_path)

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.changes = set()

    def on_any_event(self, event):
        if not event.is_directory:
            self.changes.add((event.event_type, event.src_path))

async def watch_directory(directory_path: str):
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, directory_path, recursive=True)
    observer.start()
    
    try:
        while True:
            await asyncio.sleep(1)
            if event_handler.changes:
                changes = list(event_handler.changes)
                event_handler.changes.clear()
                yield changes
    finally:
        observer.stop()
        observer.join()

async def get_file_changes(directory_path: str):
    async for changes in watch_directory(directory_path):
        logger.info(f"検知された変更: {changes}")
        # ここで必要な処理を行います（例：WebSocketを通じてクライアントに通知する）