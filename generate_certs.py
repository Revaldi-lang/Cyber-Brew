import os
import ipaddress
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_self_signed_cert():
    print("Generating RSA Private Key...")
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"ID"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"DKI Jakarta"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Jakarta"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Cyber Brew Coffee Ltd"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])
    
    print("Building Certificate...")
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.IPAddress(ipaddress.ip_address("127.0.0.1"))
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    
    # Write private key to file
    key_path = "key.pem"
    print(f"Writing private key to {key_path}...")
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    # Write certificate to file
    cert_path = "cert.pem"
    print(f"Writing certificate to {cert_path}...")
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        
    print("Sertifikat SSL/TLS self-signed (cert.pem & key.pem) berhasil dibuat!")

if __name__ == "__main__":
    generate_self_signed_cert()
