import base64
import email
import logging
from pathlib import Path

logger = logging.getLogger("expense_tracker")
DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)

def list_messages(service, query: str =' ', page_token: str | None = None):
    
    while True:
        response = service.users().messages().list(
            userId='me', 
            q=query, 
            maxResults=500,
            pageToken=page_token
        ).execute()
        
        messages = response.get('messages', [])
        for msg in messages:
            yield msg
        
        page_token = response.get('nextPageToken')
        if not page_token:
            break

def get_message(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='raw').execute()
    msg_raw = base64.urlsafe_b64decode(msg['raw'])
    email_msg = email.message_from_bytes(msg_raw)
    return email_msg

def parse_email(email_msg, msg_id):
    """
    Parsea un mensaje de email de forma robusta, manejando diferentes encodings y multipart.
    Prioriza texto plano, luego HTML si no hay plano.
    """
    payload = {
        'id': msg_id,
        'subject': email_msg.get('Subject', ''),
        'from': email_msg.get('From', ''),
        'to': email_msg.get('To', ''),
        'date': email_msg.get('Date', ''),
        'body_plain': '',
        'body_html': '',
    }

    # Si es multipart
    if email_msg.is_multipart():
        for part in email_msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Ignorar attachments y headers
            if "attachment" in content_disposition:
                continue

            if content_type == 'text/plain' and not payload['body_plain']:
                payload['body_plain'] = _decode_payload(part)
            elif content_type == 'text/html' and not payload['body_html']:
                payload['body_html'] = _decode_payload(part)

        # Si no hay texto plano, usar HTML como fallback
        if not payload['body_plain'] and payload['body_html']:
            payload['body_plain'] = payload['body_html']

    else:
        # Email simple (no multipart)
        payload['body_plain'] = _decode_payload(email_msg)

    return payload


def _decode_payload(part):
    """
    Decodifica el payload de una parte del email de forma segura.
    Maneja base64, quoted-printable y diferentes charsets.
    """
    try:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ''

        # Intentar obtener el charset declarado
        charset = part.get_content_charset() or 'utf-8'

        # Lista de charsets a probar si falla el declarado
        charsets_to_try = [charset, 'utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']

        for cs in charsets_to_try:
            try:
                return payload.decode(cs, errors='replace')
            except (UnicodeDecodeError, LookupError):
                continue

        # forzar latin-1
        return payload.decode('latin-1', errors='replace')

    except Exception:
        return '[Error al decodificar el cuerpo del email]'
    
def save_email_body(email_message: dict, msg_id: str, *, prefer_html: bool = True) -> Path | None:
    """
    Saves the email body (HTML preferred, fallback to plain) to disk.
    
    Args:
        email_message: Dict from parse_email() containing 'body_html' and/or 'body_plain'
        msg_id: Gmail message ID (used as filename)
        prefer_html: If True, save HTML if available; else save plain text
    
    Returns:
        Path to saved file, or None if nothing was saved
    """
    body = None
    extension = ".html"

    if prefer_html and email_message.get('body_html'):
        body = email_message['body_html']
    elif email_message.get('body_plain'):
        body = email_message['body_plain']
        extension = ".txt"

    if not body:
        logger.debug(f"No body content to save for email {msg_id}")
        return None

    filename = DATA_FOLDER / f"{msg_id}{extension}"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(body)

        return filename
    except Exception as e:
        logger.error(f"Failed to save email {msg_id} to {filename}: {e}")
        return None