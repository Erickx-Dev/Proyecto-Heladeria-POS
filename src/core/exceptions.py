class HeladeriaPOSException(Exception):
    pass


class ReglaNegocioError(HeladeriaPOSException):
    pass


class UsuarioDuplicadoError(ReglaNegocioError):
    pass


class UsuarioNoEncontradoError(ReglaNegocioError):
    pass


class CredencialInvalidaError(ReglaNegocioError):
    pass


class RolInvalidoError(ReglaNegocioError):
    pass
