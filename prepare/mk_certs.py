# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

from __future__ import print_function

from OpenSSL import crypto
from certgen import (
    createKeyPair,
    createCertRequest,
    createCertificate,
)


def make_certs(cfg):
    cname = 'Microsoft CNTK Demo'
    cakey = createKeyPair(crypto.TYPE_RSA, 2048)
    careq = createCertRequest(cakey, CN=cname)
    # CA certificate is valid for five years.
    cacert = createCertificate(careq, (careq, cakey), 0, (0, 60*60*24*365*5))

    # print('Creating Certificate Authority private key in "%s"' % cfg.SSL_KEY)
    # with open(cfg.SSL_KEY, 'w') as capkey:
    #     capkey.write(
    #         crypto.dump_privatekey(crypto.FILETYPE_PEM, cakey).decode('utf-8')
    #     )

    # print('Creating Certificate Authority certificate in "%s"' % cfg.SSL_CERT)
    # with open(cfg.SSL_CERT, 'w') as ca:
    #     ca.write(
    #         crypto.dump_certificate(crypto.FILETYPE_PEM, cacert).decode('utf-8')
    #     )

    pkey = createKeyPair(crypto.TYPE_RSA, 2048)
    req = createCertRequest(pkey, CN=cname)
    # Certificates are valid for five years.
    cert = createCertificate(req, (cacert, cakey), 1, (0, 60*60*24*365*5))

    with open(cfg.SSL_KEY, 'w') as leafpkey:
        leafpkey.write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey).decode('utf-8')
        )
    print('[SUCCESS] Created Certificate private key in "%s"' % cfg.SSL_KEY)
        

    with open(cfg.SSL_CERT, 'w') as leafcert:
        leafcert.write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8')
        )
    print('[SUCCESS] Created Certificate certificate in "%s"' % cfg.SSL_CERT)
"""
    for (fname, cname) in [('client', 'Simple Client'),
                        ('server', 'Simple Server')]:
        pkey = createKeyPair(crypto.TYPE_RSA, 2048)
        req = createCertRequest(pkey, CN=cname)
        # Certificates are valid for five years.
        cert = createCertificate(req, (cacert, cakey), 1, (0, 60*60*24*365*5))

        print('Creating Certificate %s private key in "%s/%s.pkey"'
            % (fname, fname))
        with open('%s/%s.pkey' % (fname,), 'w') as leafpkey:
            leafpkey.write(
                crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey).decode('utf-8')
            )

        print('Creating Certificate %s certificate in "%s/%s.cert"'
            % (fname, fname))
        with open('%s/%s.cert' % (fname,), 'w') as leafcert:
            leafcert.write(
                crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8')
            )
"""