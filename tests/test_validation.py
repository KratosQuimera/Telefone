"""
Testes de Validação de IP e MAC Cisco.
"""
from haoc_voip.core.importer import validar_ipv4, normalizar_mac, MAC_CISCO_REGEX


def test_valid_ipv4():
    assert validar_ipv4("192.168.1.1") is True
    assert validar_ipv4("10.0.0.1") is True
    assert validar_ipv4("172.16.254.1") is True
    assert validar_ipv4("127.0.0.1") is True


def test_invalid_ipv4():
    assert validar_ipv4("256.1.1.1") is False
    assert validar_ipv4("192.168.1") is False
    assert validar_ipv4("192.168.1.1.1") is False
    assert validar_ipv4("abc.def.ghi.jkl") is False
    assert validar_ipv4("192.168.01.1") is False  # zeros à esquerda não canônicos
    assert validar_ipv4("") is False
    assert validar_ipv4("   ") is False


def test_mac_normalization():
    # Sem separadores
    assert normalizar_mac("001b54123456") == "00:1B:54:12:34:56"
    # Com hífens
    assert normalizar_mac("00-1b-54-12-34-56") == "00:1B:54:12:34:56"
    # Formato Cisco com pontos (001b.5412.3456)
    assert normalizar_mac("001b.5412.3456") == "00:1B:54:12:34:56"
    # Já no formato padrão
    assert normalizar_mac("00:1B:54:12:34:56") == "00:1B:54:12:34:56"


def test_mac_regex_validation():
    assert bool(MAC_CISCO_REGEX.match("00:1B:54:12:34:56")) is True
    assert bool(MAC_CISCO_REGEX.match("FF:FF:FF:FF:FF:FF")) is True
    assert bool(MAC_CISCO_REGEX.match("00:1B:54:12:34:5G")) is False  # 'G' não é hex
    assert bool(MAC_CISCO_REGEX.match("00:1B:54:12:34")) is False     # incompleto
