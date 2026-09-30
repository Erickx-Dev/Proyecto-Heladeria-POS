from __future__ import annotations

import unittest

from src.core.exceptions import ValidacionError
from src.core.security import hash_password, verify_password


class TestHashPassword(unittest.TestCase):

    def test_hash_genera_cadena_60_caracteres(self) -> None:
        resultado = hash_password("mi_clave_segura")
        self.assertIsInstance(resultado, str)
        self.assertEqual(len(resultado), 60)

    def test_hash_comienza_con_prefijo_bcrypt(self) -> None:
        resultado = hash_password("clave123")
        self.assertTrue(resultado.startswith("$2b$"))

    def test_salts_dinamicos_generan_hashes_diferentes(self) -> None:
        hash_1 = hash_password("misma_clave")
        hash_2 = hash_password("misma_clave")
        self.assertNotEqual(hash_1, hash_2)

    def test_hash_password_vacia_lanza_error(self) -> None:
        with self.assertRaises(ValidacionError):
            hash_password("")

    def test_hash_password_espacios_lanza_error(self) -> None:
        with self.assertRaises(ValidacionError):
            hash_password("   ")


class TestVerifyPassword(unittest.TestCase):

    def test_verificacion_correcta_retorna_true(self) -> None:
        clave = "admin2026"
        hashed = hash_password(clave)
        self.assertTrue(verify_password(clave, hashed))

    def test_verificacion_incorrecta_retorna_false(self) -> None:
        hashed = hash_password("clave_correcta")
        self.assertFalse(verify_password("clave_incorrecta", hashed))

    def test_verificacion_con_hash_conocido(self) -> None:
        hash_admin = "$2b$12$PmIxg7ONN2NO7XExZ9hBAODxQxq25YxDrbayYPDmfTgFxYFhMmSPa"
        self.assertTrue(verify_password("admin123", hash_admin))
        self.assertFalse(verify_password("otraClave", hash_admin))

    def test_verificacion_cadena_vacia_retorna_false(self) -> None:
        self.assertFalse(verify_password("", "$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ012"))
        self.assertFalse(verify_password("clave", ""))

    def test_verificacion_hash_invalido_retorna_false(self) -> None:
        self.assertFalse(verify_password("clave", "no_es_un_hash_bcrypt"))


if __name__ == "__main__":
    unittest.main()
