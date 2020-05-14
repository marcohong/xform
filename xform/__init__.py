class FieldABC:
    pass


class FormABC:

    def bind(self, request):
        raise NotImplementedError
