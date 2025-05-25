import logging
import os
import asyncio
from app_types.message_types import FileStatus, OutgoingMessage
from consumers.kafka_consumer import KafkaConsumerHandler
from producers.kafka_producer import KafkaProducerHandler
from services.minio_service import MinioService
from scanner.scanner import Scanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def process_file_async(incoming_message, producer, minio_handler, scanner):
    """Async file processing for APK files"""
    
    try:
        local_path = f"{os.getcwd()}/tmp/{incoming_message.file_path}"
        logger.info(f"Downloading file from MinIO: {incoming_message.file_path}")
        minio_handler.download_file(incoming_message.file_path, local_path)
        logger.info(f"File downloaded successfully: {local_path}")

        logger.info(f"Async scanning APK file: {local_path}")
        result_file_path, result_file_name, json_body = await scanner.scan_file_async(
            local_path, incoming_message.file_path, incoming_message.folder_name, incoming_message.name
        )
        logger.info(f"Async scan completed. Result saved to: {result_file_path}")

        logger.info(f"Uploading result file to MinIO: {result_file_name}")
        minio_handler.upload_file(result_file_path, result_file_name, "application/pdf")
        logger.info(f"Result file uploaded successfully to MinIO: {result_file_name}")

        outgoing_message = OutgoingMessage(
            scan_id=incoming_message.scan_id,
            file_path=result_file_name,
            file_id=incoming_message.file_id,
            chunk=incoming_message.chunk,
            chunks=incoming_message.chunks,
            status=FileStatus.PROCESSED,
            body=json_body
        )
        producer.send_message(outgoing_message)
        logger.info(f"Successfully processed APK file: {incoming_message.file_path}")

        logger.info(f"Cleaning up temporary files...")
        os.unlink(local_path)
        os.unlink(result_file_path)
        logger.info(f"Temporary files deleted: {local_path}, {result_file_path}")

    except Exception as e:
        logger.error(f"Error processing APK file: {e}")
        outgoing_message = OutgoingMessage(
            scan_id=incoming_message.scan_id,
            file_path="",
            file_id=incoming_message.file_id,
            chunk=incoming_message.chunk,
            chunks=incoming_message.chunks,
            status=FileStatus.FAILED
        )
        producer.send_message(outgoing_message)
        logger.error(f"Failed to process APK file: {incoming_message.file_path}")

def process_file_sync(incoming_message, producer, minio_handler, scanner):
    """Synchronous file processing for non-APK files"""
    
    try:
        local_path = f"{os.getcwd()}/tmp/{incoming_message.file_path}"
        logger.info(f"Downloading file from MinIO: {incoming_message.file_path}")
        minio_handler.download_file(incoming_message.file_path, local_path)
        logger.info(f"File downloaded successfully: {local_path}")

        logger.info(f"Scanning file: {local_path}")
        result_file_path, result_file_name, json_body = scanner.scan_file(
            local_path, incoming_message.file_path, incoming_message.folder_name, incoming_message.name
        )
        logger.info(f"Scan completed. Result saved to: {result_file_path}")

        logger.info(f"Uploading result file to MinIO: {result_file_name}")
        minio_handler.upload_file(result_file_path, result_file_name, "application/pdf")
        logger.info(f"Result file uploaded successfully to MinIO: {result_file_name}")

        outgoing_message = OutgoingMessage(
            scan_id=incoming_message.scan_id,
            file_path=result_file_name,
            file_id=incoming_message.file_id,
            chunk=incoming_message.chunk,
            chunks=incoming_message.chunks,
            status=FileStatus.PROCESSED,
            body=json_body
        )
        producer.send_message(outgoing_message)
        logger.info(f"Successfully processed file: {incoming_message.file_path}")

        logger.info(f"Cleaning up temporary files...")
        os.unlink(local_path)
        os.unlink(result_file_path)
        logger.info(f"Temporary files deleted: {local_path}, {result_file_path}")

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        outgoing_message = OutgoingMessage(
            scan_id=incoming_message.scan_id,
            file_path="",
            file_id=incoming_message.file_id,
            chunk=incoming_message.chunk,
            chunks=incoming_message.chunks,
            status=FileStatus.FAILED
        )
        producer.send_message(outgoing_message)
        logger.error(f"Failed to process file: {incoming_message.file_path}")

def is_apk_file(file_path: str) -> bool:
    """Check if the file is an APK file"""
    return file_path.lower().endswith('.apk')

async def main_async():
    """Async main function for handling APK files"""
    
    consumer = KafkaConsumerHandler()
    producer = KafkaProducerHandler()
    minio_handler = MinioService()
    scanner = Scanner()

    logger.info("Starting the async file processing service...")

    for incoming_message in consumer.consume_messages():
        logger.info(f"Received message: {incoming_message.__dict__}")

        if is_apk_file(incoming_message.file_path):
            logger.info(f"Detected APK file, using async processing: {incoming_message.file_path}")
            await process_file_async(incoming_message, producer, minio_handler, scanner)
        else:
            logger.info(f"Detected non-APK file, using sync processing: {incoming_message.file_path}")
            process_file_sync(incoming_message, producer, minio_handler, scanner)

def main():
    """Main function that handles both sync and async processing"""
    
    consumer = KafkaConsumerHandler()
    producer = KafkaProducerHandler()
    minio_handler = MinioService()
    scanner = Scanner()

    logger.info("Starting the file processing service...")

    # Create tmp directory if it doesn't exist
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    for incoming_message in consumer.consume_messages():
        logger.info(f"Received message: {incoming_message.__dict__}")

        if is_apk_file(incoming_message.file_path):
            logger.info(f"Detected APK file, using async processing: {incoming_message.file_path}")
            # Run async processing in event loop
            asyncio.run(process_file_async(incoming_message, producer, minio_handler, scanner))
        else:
            logger.info(f"Detected non-APK file, using sync processing: {incoming_message.file_path}")
            process_file_sync(incoming_message, producer, minio_handler, scanner)

if __name__ == "__main__":
    main()