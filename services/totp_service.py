import base64
import io
import secrets

import pyotp
import qrcode
import qrcode.image.svg

_ISSUER_NAME = "StayFlow"


def generate_secret():
    return pyotp.random_base32()


def get_provisioning_uri(secret, email):
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=_ISSUER_NAME)


def generate_qr_code_data_uri(otpauth_uri):
    """
    QR code gerado no servidor como SVG (sem Pillow, sem CDN externo) -
    devolvido como data URI pra <img> renderizar direto, sem precisar
    de rota/arquivo estatico proprio.
    """
    img = qrcode.make(otpauth_uri, image_factory=qrcode.image.svg.SvgImage)
    buffer = io.BytesIO()
    img.save(buffer)
    svg_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/svg+xml;base64,{svg_base64}"


def verify_totp_code(secret, code):
    """valid_window=1 tolera diferenca de ate 30s de relogio (pra frente ou pra tras) entre servidor e celular - padrao razoavel, nao abre janela grande demais."""
    if not secret or not code:
        return False
    try:
        return pyotp.TOTP(secret).verify(code.strip(), valid_window=1)
    except Exception:
        return False


def normalize_backup_code(raw):
    """Maiusculo, so alfanumerico - deixa o traco de exibicao ('A1B2-C3D4') opcional na hora de digitar de volta."""
    return "".join(ch for ch in (raw or "").upper() if ch.isalnum())


def generate_backup_codes(count=8):
    """Codigos de backup de uso unico, formato legivel pra exibir uma unica vez na confirmacao do 2FA."""
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(4).upper()
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes
