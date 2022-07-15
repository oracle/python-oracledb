#------------------------------------------------------------------------------
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# crypto.pyx
#
# Cython file defining the cryptographic methods used by the thin client
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

from cryptography import x509
from cryptography.hazmat.primitives.ciphers import algorithms, modes, Cipher
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf import pbkdf2

DN_REGEX = '(?:^|,\s?)(?:(?P<name>[A-Z]+)=(?P<val>"(?:[^"]|"")+"|[^,]+))+'
PEM_WALLET_FILE_NAME = "ewallet.pem"

def decrypt_cbc(key, encrypted_text):
    """
    Decrypt the given text using the given key.
    """
    iv = bytes(16)
    algo = algorithms.AES(key)
    cipher = Cipher(algo, modes.CBC(iv))
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_text)


def encrypt_cbc(key, plain_text, zeros=False):
    """
    Encrypt the given text using the given key. If the zeros flag is set, use
    zero padding if required. Otherwise, use number padding.
    """
    block_size = 16
    iv = bytes(block_size)
    algo = algorithms.AES(key)
    cipher = Cipher(algo, modes.CBC(iv))
    encryptor = cipher.encryptor()
    n = block_size - len(plain_text) % block_size
    if n:
        if zeros:
            plain_text += bytes(n)
        else:
            plain_text += (bytes([n]) * n)
    return encryptor.update(plain_text) + encryptor.finalize()


def get_derived_key(key, salt, length, iterations):
    """
    Return a derived key using PBKDF2.
    """
    kdf = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA512(), salt=salt,
                            length=length, iterations=iterations)
    return kdf.derive(key)


def get_server_dn_matches(sock, expected_dn):
    """
    Return a boolean indicating if the server distinguished name (DN) matches
    the expected distinguished name (DN).
    """
    cert_data = sock.getpeercert(binary_form=True)
    cert = x509.load_der_x509_certificate(cert_data)
    server_dn = cert.subject.rfc4514_string()
    expected_dn_dict = dict(re.findall(DN_REGEX, expected_dn))
    server_dn_dict = dict(re.findall(DN_REGEX, server_dn))
    return server_dn_dict == expected_dn_dict


def get_ssl_socket(sock, ConnectParamsImpl params, Description description,
                   Address address):
    """
    Returns a wrapped SSL socket given a socket and the parameters supplied by
    the user.
    """
    ssl_context = ssl.create_default_context()

    # if the platform is macOS, and one-way TLS or mTLS is being used, check
    # if the certifi package is installed. If certifi is not installed, load
    # the certificates from the macOS keychain in PEM format.
    if sys.platform == "darwin" and certifi is None:
        global macos_certs
        if macos_certs is None:
            certs = subprocess.run(["security", "find-certificate",
                                    "-a", "-p"],
                                    stdout=subprocess.PIPE).stdout
            macos_certs = certs.decode("utf-8")
        ssl_context.load_verify_locations(cadata=macos_certs)
    if description.wallet_location is not None:
        pem_file_name = os.path.join(description.wallet_location,
                                     PEM_WALLET_FILE_NAME)
        if not os.path.exists(pem_file_name):
            errors._raise_err(errors.ERR_WALLET_FILE_MISSING,
                              name=pem_file_name)
        ssl_context.load_verify_locations(pem_file_name)
        ssl_context.load_cert_chain(pem_file_name,
                                    password=params._get_wallet_password())
    return perform_tls_negotiation(sock, ssl_context, description, address)


def perform_tls_negotiation(sock, ssl_context, Description description,
                            Address address):
    """
    Peforms TLS negotiation.
    """
    if description.ssl_server_dn_match \
            and description.ssl_server_cert_dn is None:
        sock = ssl_context.wrap_socket(sock, server_hostname=address.host)
    else:
        ssl_context.check_hostname = False
        sock = ssl_context.wrap_socket(sock)
    if description.ssl_server_dn_match \
            and description.ssl_server_cert_dn is not None:
        if not get_server_dn_matches(sock, description.ssl_server_cert_dn):
            errors._raise_err(errors.ERR_INVALID_SERVER_CERT_DN)
    return sock
