#------------------------------------------------------------------------------
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.ciphers import algorithms, modes, Cipher
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.asymmetric import ec, padding
    from cryptography.hazmat.primitives.kdf import pbkdf2
except Exception as e:
    CRYPTOGRAPHY_IMPORT_ERROR = e


DN_REGEX = '(?:^|,\s?)(?:(?P<name>[A-Z]+)=(?P<val>"(?:[^"]|"")+"|[^,]+))+'
PEM_WALLET_FILE_NAME = "ewallet.pem"

def _name_matches(name_to_check, cert_name):
    """
    Returns a boolean indicating if the name to check matches with the
    certificate name. The certificate name may contain a wildcard (*)
    character.
    """

    # check for a full match (case insensitive)
    cert_name = cert_name.lower()
    name_to_check = name_to_check.lower()
    if name_to_check == cert_name:
        return True

    # ensure that more than one label exists in both the name to check and the
    # certificate name
    check_pos = name_to_check.find(".")
    cert_pos = cert_name.find(".")
    if check_pos <= 0 or cert_pos <= 0:
        return False

    # ensure that the right hand labels all match
    if name_to_check[check_pos:] != cert_name[cert_pos:]:
        return False

    # match wildcards, if applicable
    cert_label = cert_name[:cert_pos]
    check_label = name_to_check[:check_pos]
    if cert_label == "*":
        return True
    elif cert_label.startswith("*"):
        return check_label.endswith(cert_label[1:])
    elif cert_label.endswith("*"):
        return check_label.startswith(cert_label[:-1])
    wildcard_pos = cert_name.find("*")
    if wildcard_pos < 0:
        return False
    return check_label.startswith(cert_label[:wildcard_pos]) \
            and check_label.endswith(cert_label[wildcard_pos + 1:])


def check_server_dn(sock, expected_dn, expected_name):
    """
    Validates the server distinguished name (if one is specified) or the
    simple name (if a distinguished name is not present).
    """
    cert_data = sock.getpeercert(binary_form=True)
    cert = x509.load_der_x509_certificate(cert_data)
    if expected_dn is not None:
        server_dn = cert.subject.rfc4514_string()
        expected_dn_dict = dict(re.findall(DN_REGEX, expected_dn))
        server_dn_dict = dict(re.findall(DN_REGEX, server_dn))
        if server_dn_dict != expected_dn_dict:
            errors._raise_err(errors.ERR_INVALID_SERVER_CERT_DN,
                              expected_dn=expected_dn)
    else:
        try:
            ext = cert.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            )
            for name in ext.value.get_values_for_type(x509.DNSName):
                if _name_matches(expected_name, name):
                    return
        except x509.ExtensionNotFound:
            pass
        for name in cert.subject.get_attributes_for_oid(
            x509.oid.NameOID.COMMON_NAME
        ):
            if _name_matches(expected_name, name.value):
                return
        errors._raise_err(errors.ERR_INVALID_SERVER_NAME,
                          expected_name=expected_name)


def decrypt_cbc(key, encrypted_text):
    """
    Decrypt the given text using the given key.
    """
    iv = bytes(16)
    algo = algorithms.AES(key)
    cipher = Cipher(algo, modes.CBC(iv))
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_text)


def decrypt_gcm(key, encrypted_text, iv):
    """
    Decryptes the given text using the given key and iv.
    """
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, encrypted_text, None)


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


def encrypt_gcm(key, plain_text, iv):
    """
    Encrypts the given text using the given key and iv.
    """
    aesgcm = AESGCM(key)
    return aesgcm.encrypt(iv, plain_text, None)


def get_derived_key(key, salt, length, iterations):
    """
    Return a derived key using PBKDF2.
    """
    kdf = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA512(), salt=salt,
                            length=length, iterations=iterations)
    return kdf.derive(key)


def get_signature(private_key_str, text):
    """
    Returns a signed version of the given text (used for IAM token
    authentication) in base64 encoding.
    """
    private_key = serialization.load_pem_private_key(private_key_str.encode(),
                                                     password=None)
    sig = private_key.sign(text.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()


cdef class TlsWrapper:
    cdef:
        object incoming, outgoing, ssl_obj, context
        bytes _verify_key

    def __init__(self):
        self.context = ssl.create_default_context()
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
        self.incoming = ssl.MemoryBIO()
        self.outgoing = ssl.MemoryBIO()
        self.ssl_obj = self.context.wrap_bio(self.incoming, self.outgoing)
        try:
            self.ssl_obj.do_handshake()
        except ssl.SSLWantReadError:
            pass

    cdef bytes _process_data(self, bytes data, bint incoming):
        """
        Processes data and adjusts the packet header, as applicable.
        """
        cdef:
            char_type packet_size_buf[4]
            bytes processed_data
            uint32_t packet_size
        if incoming:
            self.incoming.write(data[DATA_PACKET_HEADER_SIZE:])
            processed_data = self.ssl_obj.read(len=len(data))
        else:
            self.ssl_obj.write(data[DATA_PACKET_HEADER_SIZE:])
            processed_data = self.outgoing.read()
        packet_size = <uint32_t> len(processed_data) + DATA_PACKET_HEADER_SIZE
        encode_uint32be(packet_size_buf, packet_size)
        return packet_size_buf[:4] + data[4:DATA_PACKET_HEADER_SIZE] + \
                processed_data

    cdef int continue_handshake(self, bytes data) except -1:
        """
        Continues the handshake necessary for establishing a TLS stream.
        """
        self.incoming.write(data)
        self.ssl_obj.do_handshake()

    cdef bytes process_incoming_data(self, bytes data):
        """
        Processes incoming data.
        """
        return self._process_data(data, incoming=True)

    cdef bytes process_outgoing_data(self, bytes data):
        """
        Processes outgoing data.
        """
        return self._process_data(data, incoming=False)

    cdef bytes read_outgoing_data(self):
        """
        Returns the outgoing data.
        """
        return self.outgoing.read()
