# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

public_cert = """
-----BEGIN CERTIFICATE-----
MIID8TCCAtmgAwIBAgIJAMoDz7Npas2/MA0GCSqGSIb3DQEBCwUAMIGOMQswCQYD
VQQGEwJVUzETMBEGA1UECAwKQ2FsaWZvcm5pYTEWMBQGA1UEBwwNU2FuIEZyYW5j
aXNjbzEVMBMGA1UECgwMTGlicmF0byBJbmMuMRUwEwYDVQQDDAxBcHBPcHRpY3Mg
Q0ExJDAiBgkqhkiG9w0BCQEWFXN1cHBvcnRAYXBwb3B0aWNzLmNvbTAeFw0xNzA5
MTUyMjAxMzlaFw0yNzA5MTMyMjAxMzlaMIGOMQswCQYDVQQGEwJVUzETMBEGA1UE
CAwKQ2FsaWZvcm5pYTEWMBQGA1UEBwwNU2FuIEZyYW5jaXNjbzEVMBMGA1UECgwM
TGlicmF0byBJbmMuMRUwEwYDVQQDDAxBcHBPcHRpY3MgQ0ExJDAiBgkqhkiG9w0B
CQEWFXN1cHBvcnRAYXBwb3B0aWNzLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEP
ADCCAQoCggEBAOxO0wsGba3iI4r3L5BMST0rAO/gGaUhpQre6nRwVTmPCnLw1bmn
GdiFgYv/oRRwU+VieumHSQqoOmyFrg+ajGmvUDp2WqQ0It+XhcbaHFiAp2H7+mLf
cUH6S43/em0WUxZHeRzRupRDyO1bX6Hh2jgxykivlFrn5HCIQD5Hx1/SaZoW9v2n
oATCbgFOiPW6kU/AVs4R0VBujon13HCehVelNKkazrAEBT1i6RvdOB6aQQ32seW+
gLV5yVWSPEJvA9ZJqad/nQ8EQUMSSlVN191WOjp4bGpkJE1svs7NmM+Oja50W56l
qOH5eWermr/8qWjdPlDJ+I0VkgN0UyHVuRECAwEAAaNQME4wHQYDVR0OBBYEFOuL
KDTFhRQXwlBRxhPqhukrNYeRMB8GA1UdIwQYMBaAFOuLKDTFhRQXwlBRxhPqhukr
NYeRMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAJQtH446NZhjusy6
iCyvmnD95ybfNPDpjHmNx5n9Y6w9n+9y1o3732HUJE+WjvbLS3h1o7wujGKMcRJn
7I7eTDd26ZhLvnh5/AitYjdxrtUkQDgyxwLFJKhZu0ik2vXqj0fL961/quJL8Gyp
hNj3Nf7WMohQMSohEmCCX2sHyZGVGYmQHs5omAtkH/NNySqmsWNcpgd3M0aPDRBZ
5VFreOSGKBTJnoLNqods/S9RV0by84hm3j6aQ/tMDIVE9VCJtrE6evzC0MWyVFwR
ftgwcxyEq5SkiR+6BCwdzAMqADV37TzXDHLjwSrMIrgLV5xZM20Kk6chxI5QAr/f
7tsqAxw=
-----END CERTIFICATE-----
"""


def get_public_cert() -> str:
    return public_cert
