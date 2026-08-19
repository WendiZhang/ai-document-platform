import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


ALLOWED_EXTENSIONS = {".pdf", ".docx"}

ALLOWED_MIME_TYPES = {
    ".pdf": {
        "application/pdf",
        "application/octet-stream",
    },
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
}

CHUNK_SIZE = 1024 * 1024  # 1 MB


@dataclass
class SavedFile:
    original_filename: str
    stored_filename: str
    file_path: Path
    file_type: str
    mime_type: str
    file_size: int


def get_safe_extension(filename: str | None) -> str:
    """
    Return and validate the lowercase file extension.

    We use only the extension from the original filename. The original
    filename is never used as the physical server filename.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must have a filename.",
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed.",
        )

    return extension


def validate_content_type(
    extension: str,
    content_type: str | None,
) -> str:
    """
    Check the MIME type reported by the upload.

    MIME type checks are useful but are not sufficient by themselves,
    so the file's actual structure is checked after saving.
    """
    normalized_content_type = (
        content_type or "application/octet-stream"
    ).lower()

    if normalized_content_type not in ALLOWED_MIME_TYPES[extension]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid content type for {extension} file: "
                f"{normalized_content_type}"
            ),
        )

    return normalized_content_type


def validate_pdf(file_path: Path) -> None:
    """
    A PDF file should begin with the PDF signature: %PDF-
    """
    with file_path.open("rb") as file:
        signature = file.read(5)

    if signature != b"%PDF-":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid PDF document.",
        )


def validate_docx(file_path: Path) -> None:
    """
    DOCX files are ZIP archives containing specific XML files.
    """
    try:
        with zipfile.ZipFile(file_path, "r") as archive:
            filenames = set(archive.namelist())

            required_files = {
                "[Content_Types].xml",
                "word/document.xml",
            }

            if not required_files.issubset(filenames):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The uploaded file is not a valid DOCX document.",
                )

    except zipfile.BadZipFile as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid DOCX document.",
        ) from exc


def validate_saved_file(
    file_path: Path,
    extension: str,
) -> None:
    if extension == ".pdf":
        validate_pdf(file_path)
    elif extension == ".docx":
        validate_docx(file_path)


async def save_upload_file(upload_file: UploadFile) -> SavedFile:
    """
    Validate and safely store one uploaded PDF or DOCX file.

    The file is read in chunks so that a large upload is not loaded
    completely into memory.
    """
    extension = get_safe_extension(upload_file.filename)

    mime_type = validate_content_type(
        extension=extension,
        content_type=upload_file.content_type,
    )

    upload_directory = Path(settings.upload_directory).resolve()
    upload_directory.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = upload_directory / stored_filename

    max_file_size = settings.max_upload_size_mb * 1024 * 1024
    total_size = 0

    try:
        with file_path.open("wb") as destination:
            while chunk := await upload_file.read(CHUNK_SIZE):
                total_size += len(chunk)

                if total_size > max_file_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            "The uploaded file is too large. "
                            f"Maximum size is "
                            f"{settings.max_upload_size_mb} MB."
                        ),
                    )

                destination.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty.",
            )

        validate_saved_file(
            file_path=file_path,
            extension=extension,
        )

        return SavedFile(
            original_filename=Path(
                upload_file.filename or "document"
            ).name,
            stored_filename=stored_filename,
            file_path=file_path,
            file_type=extension.removeprefix("."),
            mime_type=mime_type,
            file_size=total_size,
        )

    except Exception:
        # Remove partially saved or invalid files.
        file_path.unlink(missing_ok=True)
        raise

    finally:
        await upload_file.close()


def delete_saved_file(file_path: str | Path) -> bool:
    """
    Delete a file only when it is located inside the configured
    upload directory.

    Returns True when the file was deleted or did not exist.
    Returns False when the path was outside the upload directory.
    """
    upload_directory = Path(
        settings.upload_directory
    ).resolve()

    saved_path = Path(file_path).resolve()

    try:
        saved_path.relative_to(upload_directory)
    except ValueError:
        # The requested path is outside the upload directory.
        return False

    saved_path.unlink(missing_ok=True)

    return True
