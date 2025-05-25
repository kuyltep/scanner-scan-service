from enum import Enum

class FileStatus(Enum):
    UPLOADED = 'UPLOADED'
    PROCESSING = 'PROCESSING'
    PROCESSED = 'PROCESSED'
    FAILED = 'FAILED'

class IncomingMessage:
    def __init__(self, scan_id: str, file_path: str, file_id: str, chunk: int, chunks: int, name: str, folder_name: str):
        self.scan_id = scan_id
        self.file_path = file_path
        self.file_id = file_id
        self.chunk = chunk
        self.chunks = chunks
        self.name = name
        self.folder_name = folder_name

    @staticmethod
    def from_dict(data: dict):
        return IncomingMessage(
            scan_id=data.get("scan_id"),
            file_path=data.get("file_path"),
            file_id=data.get("file_id"),
            chunk=data.get("chunk"),
            chunks=data.get("chunks"),
            name=data.get("name"),
            folder_name=data.get("folder_name")
        )

class OutgoingMessage:
    def __init__(self, scan_id: str, file_path: str, file_id: str, chunk: int, chunks: int, status: FileStatus, body: str):
        self.scan_id = scan_id
        self.file_path = file_path
        self.file_id = file_id
        self.chunk = chunk
        self.chunks = chunks
        self.status = status.value
        self.body = body

    def to_dict(self):
        return {
            "scan_id": self.scan_id,
            "file_path": self.file_path,
            "file_id": self.file_id,
            "chunk": self.chunk,
            "chunks": self.chunks,
            "status": self.status,
            "body": self.body
        }